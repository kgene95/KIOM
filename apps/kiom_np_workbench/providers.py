from __future__ import annotations
import csv, io
import requests

TIMEOUT=30

def pubchem_compound(query):
    raw=query.strip()
    cid_text=raw.replace("CID","",1).replace("cid","",1).replace(":","").strip()
    fields="IUPACName,MolecularFormula,CanonicalSMILES,IsomericSMILES,InChIKey"
    if cid_text.isdigit():
        url=f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{int(cid_text)}/property/{fields}/JSON"
        r=requests.get(url,timeout=TIMEOUT); r.raise_for_status()
        return r.json().get("PropertyTable",{}).get("Properties",[])[:20]
    else:
        q=requests.utils.quote(raw,safe="")
        url=f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{q}/property/{fields}/JSON"
        r=requests.get(url,timeout=TIMEOUT)
        try:
            r.raise_for_status()
            return r.json().get("PropertyTable",{}).get("Properties",[])[:20]
        except requests.HTTPError:
            if getattr(r,"status_code",None) != 404: raise
            # PubChem's name endpoint is sensitive to Unicode primes/quotes. Retry
            # using its official autocomplete synonyms, then return all candidates.
            candidates=pubchem_suggestions(raw)
            merged=[]; seen=set()
            for synonym in candidates:
                sq=requests.utils.quote(synonym,safe="")
                sr=requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{sq}/property/{fields}/JSON",timeout=TIMEOUT)
                if getattr(sr,"status_code",None)==404: continue
                sr.raise_for_status()
                for item in sr.json().get("PropertyTable",{}).get("Properties",[]):
                    cid=item.get("CID")
                    if cid not in seen: seen.add(cid); merged.append(item)
            if merged: return merged[:20]
            raise

def pubchem_suggestions(query):
    q=requests.utils.quote(query.strip(),safe="")
    r=requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/autocomplete/compound/{q}/json",timeout=TIMEOUT); r.raise_for_status()
    return r.json().get("dictionary_terms",{}).get("compound",[])[:10]

def pubchem_synonyms(cid):
    r=requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{int(cid)}/synonyms/JSON",timeout=TIMEOUT); r.raise_for_status()
    info=(r.json().get("InformationList",{}).get("Information",[]) or [])
    return (info[0].get("Synonym",[]) if info else [])

def ols_disease(query):
    raw=query.strip()
    # A bare numeric ontology value is ambiguous in OLS search. In this project
    # disease IDs are MONDO IDs, so resolve the exact MONDO term rather than
    # allowing a full-text search to return an unrelated ontology (e.g. UBERON).
    if raw.isdigit():
        raise ValueError("Ontology ID에는 MONDO:, DOID:, HP: 같은 접두사를 함께 입력하세요.")
    if raw.upper().startswith("MONDO:") or raw.upper().startswith("MONDO_"):
        digits=raw.split(":",1)[-1].split("_",1)[-1]
        iri=f"http://purl.obolibrary.org/obo/MONDO_{digits}"
        encoded=requests.utils.quote(requests.utils.quote(iri,safe=""),safe="")
        r=requests.get(f"https://www.ebi.ac.uk/ols4/api/ontologies/mondo/terms/{encoded}",timeout=TIMEOUT); r.raise_for_status()
        term=r.json()
        return [term] if term.get("obo_id") else []
    r=requests.get("https://www.ebi.ac.uk/ols4/api/search",params={"q":raw,"rows":20,"queryFields":"label,synonym"},timeout=TIMEOUT); r.raise_for_status()
    docs=r.json().get("response",{}).get("docs",[])
    return docs

def mygene_map(targets, batch_size=250):
    """Map identifiers in bounded batches, isolating malformed values."""
    cleaned=[]; seen=set()
    for target in targets or []:
        value=str(target).strip()
        if value and value not in seen:
            seen.add(value); cleaned.append(value)
    if not cleaned: return []
    endpoint="https://mygene.info/v3/query"
    params_base={"species":"human","scopes":"symbol,uniprot.Swiss-Prot,entrezgene","fields":"symbol,entrezgene,uniprot.Swiss-Prot,taxid","format":"json"}
    def request(values):
        safe_targets=[requests.utils.quote(value,safe="._-") for value in values]
        response=requests.post(endpoint,data={**params_base,"q":",".join(safe_targets)},timeout=TIMEOUT)
        response.raise_for_status()
        payload=response.json()
        return payload if isinstance(payload,list) else []
    output=[]; size=max(1,int(batch_size))
    for start in range(0,len(cleaned),size):
        batch=cleaned[start:start+size]
        try:
            output.extend(request(batch))
        except requests.HTTPError as error:
            if getattr(error.response,"status_code",None)!=400: raise
            for value in batch:
                try: output.extend(request([value]))
                except requests.HTTPError as item_error:
                    if getattr(item_error.response,"status_code",None)!=400: raise
    return output

def pubchem_bioactivity_targets(cid):
    """Return active PubChem assay targets; a missing assay summary is a valid empty result.

    PubChem returns HTTP 404 when a compound has no public assay-summary record.  That
    is different from a failed network request, so callers can guide the user to add
    a permitted external source instead of reporting a broken application.
    """
    r=requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{int(cid)}/assaysummary/CSV",timeout=TIMEOUT)
    if getattr(r,"status_code",None) == 404:
        return []
    r.raise_for_status()
    records=[]
    for row in csv.DictReader(io.StringIO(r.text)):
        gene_id=(row.get("Target GeneID") or "").strip()
        if row.get("Activity Outcome") == "Active" and gene_id:
            records.append({"target":gene_id,"species":"AUTO_HUMAN_MAPPING_REQUIRED","source":"PubChem PUG-REST active bioassay","pubchem_cid":str(cid),"pubchem_aid":row.get("AID",""),"activity_outcome":"Active","target_accession":row.get("Target Accession",""),"assay_name":row.get("Assay Name","")})
    return records

def opentargets_disease_targets(query, size=200):
    """Resolve a disease name and retrieve scored human target associations from Open Targets."""
    url="https://api.platform.opentargets.org/api/v4/graphql"
    search_query="""query($text: String!) { search(queryString: $text, entityNames: [\"disease\"], page: {index: 0, size: 10}) { hits { id name entity } } }"""
    r=requests.post(url,json={"query":search_query,"variables":{"text":query}},timeout=TIMEOUT); r.raise_for_status()
    hits=(r.json().get("data",{}).get("search",{}).get("hits",[]) or [])
    if not hits: raise ValueError(f"Open Targets found no disease concept for: {query}")
    disease=hits[0]
    target_query="""query($id: String!, $size: Int!) { disease(efoId: $id) { id name associatedTargets(page: {index: 0, size: $size}) { rows { score target { id approvedSymbol approvedName } } } } }"""
    r=requests.post(url,json={"query":target_query,"variables":{"id":disease["id"],"size":size}},timeout=TIMEOUT); r.raise_for_status()
    resolved=(r.json().get("data",{}).get("disease") or {})
    rows=((resolved.get("associatedTargets") or {}).get("rows") or [])
    records=[]
    for row in rows:
        target=row.get("target") or {}; symbol=(target.get("approvedSymbol") or "").strip()
        if symbol:
            records.append({"target":symbol,"species":"9606","source":"Open Targets Platform GraphQL disease association","opentargets_disease_id":resolved.get("id",disease["id"]),"opentargets_disease_name":resolved.get("name",disease.get("name",query)),"ensembl_id":target.get("id",""),"association_score":row.get("score","")})
    if not records: raise ValueError(f"Open Targets returned no target associations for: {disease['id']}")
    return records, {"query":query,"disease_id":resolved.get("id",disease["id"]),"disease_name":resolved.get("name",disease.get("name",query)),"records":len(records),"endpoint":url}

def string_map(targets):
    r=requests.post("https://string-db.org/api/json/get_string_ids",data={"identifiers":"\r".join(targets),"species":9606,"limit":1,"echo_query":1},timeout=TIMEOUT); r.raise_for_status(); return r.json()

def string_network(string_ids,required_score=400):
    r=requests.post("https://string-db.org/api/tsv/network",data={"identifiers":"\r".join(string_ids),"species":9606,"required_score":required_score,"caller_identity":"KIOM_NP_local_app"},timeout=TIMEOUT); r.raise_for_status()
    lines=r.text.splitlines();
    if len(lines)<2: return []
    import csv,io
    return list(csv.DictReader(io.StringIO(r.text),delimiter="\t"))

def string_enrichment(string_ids):
    r=requests.post("https://string-db.org/api/tsv/enrichment",data={"identifiers":"\r".join(string_ids),"species":9606,"caller_identity":"KIOM_NP_local_app"},timeout=TIMEOUT); r.raise_for_status()
    import csv,io
    return list(csv.DictReader(io.StringIO(r.text),delimiter="\t")) if r.text.strip() else []

def gprofiler_enrichment(symbols,organism="hsapiens"):
    r=requests.post("https://biit.cs.ut.ee/gprofiler/api/gost/profile/",json={"organism":organism,"query":symbols,"sources":["GO:BP","GO:CC","GO:MF","KEGG","REAC"],"significance_threshold_method":"g_SCS","user_threshold":0.05},timeout=TIMEOUT); r.raise_for_status()
    return r.json()
