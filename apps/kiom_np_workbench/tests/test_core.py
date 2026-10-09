import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import create_project, validate_target_rows, overlap_rows, save_json, load_json, write_cytoscape_exports, analysis_review_findings, expand_source_upload, hub_metrics, source_panel_gate, normalized_upload_stem, source_result_status, upload_provenance_status, target_column_present

class CoreTests(unittest.TestCase):
 def test_species_qc_does_not_promote_missing_or_nonhuman(self):
  rows=validate_target_rows([{"target":"STAT3","species":"9606"},{"target":"Trp53","species":"10090"},{"target":"JUN"}],"x")
  self.assertEqual([x['species_qc'] for x in rows],["PASS_HUMAN","EXCLUDE_NONHUMAN","REVIEW_MISSING"])
 def test_auto_targets_wait_for_human_mapping(self):
  row=validate_target_rows([{"target":"1544","species":"AUTO_HUMAN_MAPPING_REQUIRED"}],"PubChem")[0]
  self.assertEqual(row["species_qc"],"PENDING_HUMAN_MAPPING")
 def test_overlap_requires_human_and_approved_symbol(self):
  c=[{"species_qc":"PASS_HUMAN","approved_symbol":"STAT3","source":"a"},{"species_qc":"EXCLUDE_NONHUMAN","approved_symbol":"JUN","source":"b"}]
  d=[{"species_qc":"PASS_HUMAN","approved_symbol":"stat3","source":"z"},{"species_qc":"PASS_HUMAN","approved_symbol":"JUN","source":"q"}]
  self.assertEqual([r['approved_symbol'] for r in overlap_rows(c,d)],["STAT3"])
 def test_manifest_and_project_structure(self):
  with tempfile.TemporaryDirectory() as td:
   p=create_project(Path(td),{"name":"X"},{"name":"Y"},"Publication")
   self.assertTrue((p/'00_project/NP_manifest.json').exists())
   self.assertEqual(load_json(p/'00_project/NP_manifest.json')['status'],'PROJECT_CREATED')
 def test_project_preserves_multiple_compounds(self):
  with tempfile.TemporaryDirectory() as td:
   p=create_project(Path(td),[{"name":"A","pubchem_cid":1},{"name":"B","pubchem_cid":2}],{"name":"Y"},"Publication")
   self.assertEqual(len(load_json(p/'00_project/NP_manifest.json')['compounds']),2)
 def test_atomic_json_roundtrip(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'x.json';save_json(p,{"status":"ok"});self.assertEqual(load_json(p),{"status":"ok"})
 def test_graphml_connects_string_ids(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);write_cytoscape_exports(p,[{"approved_symbol":"A","string_id":"9606.A"},{"approved_symbol":"B","string_id":"9606.B"}],[{"stringId_A":"9606.A","stringId_B":"9606.B","score":"0.8"}])
   xml=(p/'03_cytoscape/network.graphml').read_text()
   self.assertIn('source="9606.A" target="9606.B"',xml)
 def test_graphml_escapes_node_ids(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);write_cytoscape_exports(p,[{"approved_symbol":"A&B"},{"approved_symbol":"C"}],[{"preferredName_A":"A&B","preferredName_B":"C","score":"0.8"}])
   xml=(p/'03_cytoscape/network.graphml').read_text()
   self.assertIn('id="A&amp;B"',xml)
   self.assertIn('source="A&amp;B" target="C"',xml)
 def test_analysis_review_findings_flags_empty_string_and_missing_sources(self):
  findings=analysis_review_findings({"counts":{"overlap_genes":3,"string_nodes":3,"string_edges":0},"provider_runs":[{"provider":"STRING","status":"NO_EDGES_RETURNED"}],"source_registry":[{"source":"PubChem"},{"source":"PharmMapper"}]}, [])
  self.assertTrue(any(x["code"]=="STRING_NO_EDGES" for x in findings))
  self.assertTrue(any(x["code"]=="MISSING_SOURCE_PANEL" for x in findings))
 def test_expand_source_upload_extracts_tsv_from_zip(self):
  import io, zipfile
  buf=io.BytesIO()
  with zipfile.ZipFile(buf,"w") as z: z.writestr("sea_result_all.tsv", "target\tspecies\nSTAT3\t9606\n")
  files=expand_source_upload("sea_result.zip",buf.getvalue())
  self.assertEqual(files[0]["name"],"sea_result_all.tsv")
  self.assertEqual(files[0]["rows"][0]["target"],"STAT3")
 def test_hub_metrics_ranks_nodes_from_edges(self):
  rows=hub_metrics([{"approved_symbol":"A"},{"approved_symbol":"B"},{"approved_symbol":"C"}], [{"preferredName_A":"A","preferredName_B":"B"},{"preferredName_A":"A","preferredName_B":"C"}])
  self.assertEqual(rows[0]["approved_symbol"],"A")
  self.assertEqual(rows[0]["degree"],2)
 def test_source_panel_gate_blocks_unverified_source(self):
  result=source_panel_gate([{"source":"SwissTargetPrediction","provenance_status":"UNVERIFIED"}],True,True)
  self.assertFalse(result["ready"])
  self.assertIn("UNVERIFIED_SOURCE_PROVENANCE",result["reasons"])
 def test_normalized_upload_stem_prevents_zip_inner_name_collision(self):
  self.assertEqual(normalized_upload_stem("sea_result_41debffd05f4.zip","sea_result_all.tsv"),"sea_result_41debffd05f4_sea_result_all")
 def test_empty_source_is_nonfatal_status(self):
  self.assertEqual(source_result_status([]),"EMPTY_RESULT")
  self.assertEqual(source_result_status([{"target":"STAT3"}]),"IMPORTED")
 def test_upload_provenance_requires_url_date_and_confirmation(self):
  self.assertEqual(upload_provenance_status("https://sea.docking.org/result?taskId=x","2026-10-09",True)["status"],"VERIFIED")
  self.assertEqual(upload_provenance_status("","2026-10-09",True)["status"],"UNVERIFIED")
 def test_auxiliary_similarity_table_is_not_target_evidence(self):
  self.assertFalse(target_column_present([{"Target_Chembl_Id":"CHEMBL1974","Target_Name":"FLT3"}]))
  self.assertTrue(target_column_present([{"target":"FLT3","species":"9606"}]))
if __name__=='__main__': unittest.main()
