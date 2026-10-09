"""Deterministic rerun of an existing KIOM NP project after source-file integration.

This follows the same core path as the Streamlit application while batching
MyGene requests so large, source-preserving SEA exports remain tractable.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import providers
from core import (
    analysis_review_findings,
    file_sha,
    hub_metrics,
    load_json,
    log,
    now,
    overlap_rows,
    read_csv,
    save_json,
    target_column_present,
    validate_target_rows,
    write_csv,
    write_cytoscape_exports,
)


def batches(values: list[str], size: int = 250):
    for start in range(0, len(values), size):
        yield values[start : start + size]


def main(project_text: str) -> None:
    project = Path(project_text)
    if not (project / "00_project" / "NP_manifest.json").exists():
        raise FileNotFoundError(f"Not a KIOM project: {project}")

    checkpoint = project / "00_project" / "NP_checkpoint.json"
    log(project, "SEA_RERUN_STARTED | preserving raw exports and rerunning QC/overlap/STRING/enrichment")
    save_json(checkpoint, {"stage": "LOAD_RAW_SOURCE_EXPORTS", "status": "RUNNING", "updated_utc": now()})

    compound_rows: list[dict] = []
    disease_rows: list[dict] = []
    registry: list[dict] = []
    for kind, bucket in (("compound_targets", compound_rows), ("disease_targets", disease_rows)):
        for source_file in sorted((project / "01_np" / "raw" / kind).glob("*.csv")):
            raw = read_csv(source_file)
            if not raw:
                registry.append({"entity": kind, "source": source_file.stem, "raw_file": str(source_file.relative_to(project)), "raw_sha256": file_sha(source_file), "retrieved_by": "user_export", "access_date": now(), "records": 0, "primary_eligible": False, "status": "EMPTY_RESULT", "notes": "Empty source result preserved and skipped"})
                log(project, f"EMPTY_RESULT | {kind}/{source_file.name} | skipped without aborting run")
                continue
            if not target_column_present(raw):
                registry.append({"entity": kind, "source": source_file.stem, "raw_file": str(source_file.relative_to(project)), "raw_sha256": file_sha(source_file), "retrieved_by": "user_export", "access_date": now(), "records": len(raw), "primary_eligible": False, "status": "UNSUPPORTED_SCHEMA", "notes": "Auxiliary/non-target table preserved but skipped from target analysis"})
                log(project, f"UNSUPPORTED_SCHEMA | {kind}/{source_file.name} | preserved and skipped without aborting run")
                continue
            for row in raw:
                if not any((row.get(k) or "").strip() for k in ("species", "organism", "taxid")):
                    row["species"] = "9606"
            validated = validate_target_rows(raw, source_file.stem)
            for row in validated:
                row["raw_file"] = str(source_file.relative_to(project))
            bucket.extend(validated)
            registry.append(
                {
                    "entity": kind,
                    "source": source_file.stem,
                    "raw_file": str(source_file.relative_to(project)),
                    "raw_sha256": file_sha(source_file),
                    "retrieved_by": "user_export",
                    "access_date": now(),
                    "records": len(raw),
                    "primary_eligible": False,
                    "status": "IMPORTED_PENDING_ID_QC",
                }
            )

    save_json(checkpoint, {"stage": "STABLE_ID_MAPPING", "status": "RUNNING", "updated_utc": now()})
    all_rows = compound_rows + disease_rows
    query_values = sorted(
        {
            row["target_submitted"]
            for row in all_rows
            if row["species_qc"] in {"PASS_HUMAN", "PENDING_HUMAN_MAPPING"} and row["target_submitted"]
        }
    )
    responses: list[dict] = []
    for index, group in enumerate(batches(query_values), start=1):
        log(project, f"RUNNING | MyGene batch {index} ({len(group)} identifiers)")
        responses.extend(providers.mygene_map(group))

    map_index: dict[str, list[dict]] = {}
    for result in responses:
        query = (result.get("query") or "").strip().upper()
        symbol = (result.get("symbol") or "").strip()
        if query and symbol:
            map_index.setdefault(query, []).append(result)

    mapped = 0
    for row in all_rows:
        if row["species_qc"] not in {"PASS_HUMAN", "PENDING_HUMAN_MAPPING"}:
            row["mapping_qc"] = "EXCLUDED_SPECIES"
            continue
        hits = map_index.get(row["target_submitted"].upper(), [])
        symbols = sorted({hit.get("symbol") for hit in hits if hit.get("symbol") and hit.get("taxid") == 9606})
        if len(symbols) == 1:
            chosen = next(hit for hit in hits if hit.get("symbol") == symbols[0] and hit.get("taxid") == 9606)
            uniprot = chosen.get("uniprot", {}).get("Swiss-Prot", []) if isinstance(chosen.get("uniprot", {}), dict) else []
            row["approved_symbol"] = symbols[0]
            row["entrez_id"] = str(chosen.get("entrezgene", ""))
            row["uniprot_accessions"] = ";".join(uniprot if isinstance(uniprot, list) else [str(uniprot)])
            row["mapping_route"] = "MyGene.info exact query; human taxid 9606; batched rerun"
            row["mapping_qc"] = "MAPPED_SINGLE_HUMAN_SYMBOL"
            row["species_qc"] = "PASS_HUMAN"
            mapped += 1
        elif len(symbols) > 1:
            row["mapping_qc"] = "AMBIGUOUS_ONE_TO_MANY"
            if row["species_qc"] == "PENDING_HUMAN_MAPPING":
                row["species_qc"] = "REVIEW_AMBIGUOUS_HUMAN_MAPPING"
        else:
            row["mapping_qc"] = "UNMAPPED_OR_NOT_FOUND"
            if row["species_qc"] == "PENDING_HUMAN_MAPPING":
                row["species_qc"] = "EXCLUDE_NO_HUMAN_MAPPING"

    write_csv(project / "01_np" / "processed" / "compound_target_records_qc.csv", compound_rows)
    write_csv(project / "01_np" / "processed" / "disease_target_records_qc.csv", disease_rows)
    overlaps = overlap_rows(compound_rows, disease_rows)
    write_csv(project / "01_np" / "final" / "overlap_broad_exploratory_pending_review.csv", overlaps)

    save_json(checkpoint, {"stage": "STRING_PPI", "status": "RUNNING", "updated_utc": now()})
    genes = [row["approved_symbol"] for row in overlaps if row.get("approved_symbol")]
    edges: list[dict] = []
    string_nodes: list[dict] = []
    string_ids: list[str] = []
    provider_runs: list[dict] = []
    if genes:
        try:
            string_nodes = providers.string_map(genes)
            string_ids = sorted({row.get("stringId") for row in string_nodes if row.get("stringId")})
            edges = providers.string_network(string_ids, required_score=400) if string_ids else []
            write_csv(project / "01_np" / "processed" / "string_mapping.tsv.csv", string_nodes)
            write_csv(project / "01_np" / "final" / "string_edges_score400.tsv.csv", edges)
            write_csv(project / "01_np" / "final" / "hub_topology_degree.csv", hub_metrics([{"approved_symbol": gene} for gene in genes], edges))
            provider_runs.append({"provider": "STRING", "status": "COMPLETED" if edges else "NO_EDGES_RETURNED", "mapped_ids": len(string_ids), "edges": len(edges), "score_threshold": 400, "species": 9606})
        except Exception as error:  # preserve partial QC and explicit failure
            provider_runs.append({"provider": "STRING", "status": "FAILED", "error": f"{type(error).__name__}: {error}"})
            log(project, f"STRING_FAILED | {type(error).__name__} | {error}")

    save_json(checkpoint, {"stage": "ENRICHMENT", "status": "RUNNING", "updated_utc": now()})
    if string_ids:
        try:
            enrichment = providers.string_enrichment(string_ids)
            write_csv(project / "01_np" / "final" / "string_enrichment.tsv.csv", enrichment)
            provider_runs.append({"provider": "STRING enrichment", "status": "COMPLETED", "terms": len(enrichment)})
        except Exception as error:
            provider_runs.append({"provider": "STRING enrichment", "status": "FAILED", "error": str(error)})
        try:
            gprofiler = providers.gprofiler_enrichment(genes)
            save_json(project / "01_np" / "final" / "gprofiler_enrichment.json", gprofiler)
            provider_runs.append({"provider": "g:Profiler", "status": "COMPLETED", "sources": ["GO:BP", "GO:CC", "GO:MF", "KEGG", "REAC"]})
        except Exception as error:
            provider_runs.append({"provider": "g:Profiler", "status": "FAILED", "error": str(error)})

    write_cytoscape_exports(
        project,
        [{"approved_symbol": gene, "string_id": next((item.get("stringId") for item in string_nodes if item.get("preferredName") == gene), "")} for gene in genes],
        edges,
    )

    manifest = load_json(project / "00_project" / "NP_manifest.json", {})
    for item in registry:
        source_name = str(item.get("source", "")).lower()
        item["provenance_status"] = "UNVERIFIED" if any(token in source_name for token in ("swisstarget", "pharmmapper")) else "PARTIALLY_VERIFIED"
    manifest["source_registry"] = registry
    manifest["analysis_started_utc"] = manifest.get("analysis_started_utc", now())
    manifest["analysis_updated_utc"] = now()
    manifest["analysis_parameters"] = {
        "species": 9606,
        "string_required_score": 400,
        "mapping_provider": "MyGene.info query API (250-ID batches)",
        "overlap": "exact approved HGNC symbol after human mapping",
        "branch": "broad_exploratory_pending_review",
        "missing_species_assumed_human_after_user_confirmation": True,
        "sea_source_included": True,
    }
    manifest["provider_runs"] = provider_runs
    manifest["counts"] = {"compound_rows": len(compound_rows), "disease_rows": len(disease_rows), "human_mapped_rows": mapped, "overlap_genes": len(overlaps), "string_nodes": len(string_ids), "string_edges": len(edges)}
    manifest["status"] = "COMPLETED_WITH_REVIEW" if overlaps else "COMPLETED_NO_OVERLAP"
    manifest["transcriptomics"] = {"status": "OPTIONAL_NOT_STARTED", "branch": "02_transcriptomics"}
    manifest["files"] = []
    for file_path in sorted(project.rglob("*")):
        if file_path.is_file() and file_path.name != "NP_manifest.json":
            manifest["files"].append({"path": str(file_path.relative_to(project)), "sha256": file_sha(file_path)})
    # Evaluate review findings only after the generated output inventory is
    # populated; otherwise a newly written hub table is falsely reported as
    # missing.
    findings = analysis_review_findings(manifest)
    manifest["review_findings"] = findings
    manifest["limitations"] = [item["message"] for item in findings if item.get("severity") in {"warning", "error"}]
    save_json(project / "00_project" / "NP_manifest.json", manifest)
    save_json(checkpoint, {"stage": "NP_CORE_RUN", "status": manifest["status"], "updated_utc": now(), "counts": manifest["counts"], "next_action": "Review mapping QC and source availability; broad overlap remains exploratory pending QC signoff."})
    (project / "00_project" / "NP_checkpoint.md").write_text(
        f"# NP checkpoint\n\n- Status: {manifest['status']}\n- Human-mapped target records: {mapped}\n- Broad exploratory overlap: {len(overlaps)}\n- STRING mapped IDs / edges: {len(string_ids)} / {len(edges)}\n- SEA: included from official raw TSV exports\n- Transcriptomics: OPTIONAL_NOT_STARTED\n- Mapping/QC signoff: PENDING\n",
        encoding="utf-8",
    )
    log(project, f"SEA_RUN_COMPLETED | overlap={len(overlaps)} | mapped={mapped} | STRING_edges={len(edges)}")
    print({"counts": manifest["counts"], "providers": provider_runs, "findings": findings})


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/rerun_project_with_sea.py PROJECT_DIR")
    main(sys.argv[1])
