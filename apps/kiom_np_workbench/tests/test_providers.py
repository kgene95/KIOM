import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import providers


class ProviderTests(unittest.TestCase):
    def response(self, payload=None, text=""):
        result = Mock()
        result.json.return_value = payload
        result.text = text
        return result

    @patch("providers.requests.get")
    def test_pubchem_compound_returns_properties(self, get):
        get.return_value = self.response({"PropertyTable": {"Properties": [{"CID": 439246}]}})
        self.assertEqual(providers.pubchem_compound("naringenin"), [{"CID": 439246}])
        get.return_value.raise_for_status.assert_called_once()

    @patch("providers.requests.get")
    def test_pubchem_compound_accepts_cid_input(self, get):
        get.return_value = self.response({"PropertyTable": {"Properties": [{"CID": 439246}]}})
        self.assertEqual(providers.pubchem_compound("CID 439246"), [{"CID": 439246}])
        self.assertIn("/compound/cid/439246/", get.call_args.args[0])

    @patch("providers.pubchem_suggestions", return_value=["Vitexin-4''-o-glucoside"])
    @patch("providers.requests.get")
    def test_pubchem_compound_retries_unicode_name_with_autocomplete(self, get, suggestions):
        missing = self.response()
        missing.status_code = 404
        missing.raise_for_status.side_effect = providers.requests.HTTPError("404")
        found = self.response({"PropertyTable": {"Properties": [{"CID": 56776173}]}})
        get.side_effect = [missing, found]
        self.assertEqual(providers.pubchem_compound('some-odd″-compound'), [{"CID": 56776173}])

    @patch("providers.requests.get")
    def test_pubchem_vitexin_name_query_is_not_forced_to_one_cid(self, get):
        get.return_value = self.response({"PropertyTable": {"Properties": [{"CID": 75596314}]}})
        self.assertEqual(providers.pubchem_compound('Vitexin-4″-O-glucoside'), [{"CID": 75596314}])

    def test_ols_bare_numeric_id_is_rejected_as_ambiguous(self):
        with self.assertRaises(ValueError): providers.ols_disease("0005101")

    @patch("providers.requests.get")
    def test_ols_returns_response_docs(self, get):
        get.return_value = self.response({"response": {"docs": [{"label": "Ulcerative colitis"}]}})
        self.assertEqual(providers.ols_disease("ulcerative colitis"), [{"label": "Ulcerative colitis"}])
        self.assertEqual(get.call_args.kwargs["params"]["rows"], 20)

    @patch("providers.requests.get")
    def test_ols_numeric_disease_id_resolves_exact_mondo_term(self, get):
        response = self.response({"label": "ulcerative colitis", "obo_id": "MONDO:0005101"})
        get.return_value = response
        rows = providers.ols_disease("MONDO:0005101")
        self.assertEqual(rows[0]["obo_id"], "MONDO:0005101")
        self.assertIn("/ontologies/mondo/terms/", get.call_args.args[0])

    @patch("providers.requests.post")
    def test_mygene_normalizes_non_list_payload(self, post):
        post.return_value = self.response({"hits": []})
        self.assertEqual(providers.mygene_map(["STAT3"]), [])

    @patch("providers.requests.post")
    def test_string_network_parses_tsv(self, post):
        post.return_value = self.response(text="stringId_A\tstringId_B\tscore\n9606.A\t9606.B\t0.8\n")
        self.assertEqual(providers.string_network(["9606.A", "9606.B"]), [{"stringId_A": "9606.A", "stringId_B": "9606.B", "score": "0.8"}])

    @patch("providers.requests.post")
    def test_gprofiler_returns_payload(self, post):
        post.return_value = self.response({"result": []})
        self.assertEqual(providers.gprofiler_enrichment(["STAT3"]), {"result": []})

    @patch("providers.requests.get")
    def test_pubchem_bioactivity_keeps_active_gene_ids(self, get):
        get.return_value = self.response(text='"AID","Activity Outcome","Target GeneID"\n410,"Active",1544\n411,"Inactive",6774\n')
        rows = providers.pubchem_bioactivity_targets(439246)
        self.assertEqual(rows[0]["target"], "1544")
        self.assertEqual(rows[0]["species"], "AUTO_HUMAN_MAPPING_REQUIRED")

    @patch("providers.requests.get")
    def test_pubchem_bioactivity_treats_missing_assay_summary_as_empty(self, get):
        response = self.response()
        response.status_code = 404
        get.return_value = response
        self.assertEqual(providers.pubchem_bioactivity_targets(75596314), [])
        response.raise_for_status.assert_not_called()

    @patch("providers.requests.post")
    def test_opentargets_resolves_and_returns_targets(self, post):
        post.side_effect = [
            self.response({"data": {"search": {"hits": [{"id": "MONDO_0005101", "name": "ulcerative colitis"}]}}}),
            self.response({"data": {"disease": {"id": "MONDO_0005101", "name": "ulcerative colitis", "associatedTargets": {"rows": [{"score": 0.7, "target": {"id": "ENSG1", "approvedSymbol": "IL12B", "approvedName": "interleukin 12B"}}]}}}}),
        ]
        rows, metadata = providers.opentargets_disease_targets("ulcerative colitis")
        self.assertEqual(rows[0]["target"], "IL12B")
        self.assertEqual(metadata["disease_id"], "MONDO_0005101")


if __name__ == "__main__":
    unittest.main()
