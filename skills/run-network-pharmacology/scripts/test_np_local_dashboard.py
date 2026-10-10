import sys
import tempfile
import json
from unittest import mock
from pathlib import Path
import unittest
sys.path.insert(0, r"D:\GPT-CODECX\KIOM\skills\run-network-pharmacology\scripts")
import np_local_dashboard as dashboard

class MultiCompoundInputTests(unittest.TestCase):
    def test_compound_queries_keeps_each_nonempty_line_once(self):
        self.assertEqual(dashboard.compound_queries("Naringenin\n\nVitexin 4-O-glucoside\nNaringenin"), ["Naringenin", "Vitexin 4-O-glucoside"])

    def test_confirmation_requires_one_cid_choice_for_each_compound(self):
        row = {"cid": "1", "title": "A", "formula": "C", "inchikey": "K"}
        page = dashboard.confirmation({"disease": "UC", "species": "Homo sapiens"}, [("compound A", [row]), ("compound B", [row])])
        self.assertIn('name="selected_cid_0"', page)
        self.assertIn('name="selected_cid_1"', page)

    def test_zero_existing_candidates_offers_only_new_submission_path(self):
        form = dashboard.approval_fields("run-a", {"candidates": []})
        self.assertIn('name="new_submit"', form)
        self.assertNotIn('name="reuse"', form)
        self.assertNotIn('name="supplement"', form)

    def test_existing_candidates_offer_reuse_and_conditional_supplement(self):
        form = dashboard.approval_fields("run-b", {"candidates": [{"source": "existing"}]})
        self.assertIn('name="reuse"', form)
        self.assertIn('name="supplement"', form)
        self.assertNotIn('name="new_submit"', form)

    def test_only_the_first_card_collects_session_email(self):
        review = {"candidates": []}
        self.assertIn('name="pharmmapper_email"', dashboard.approval_fields("run-a", review, include_email=True))
        self.assertNotIn('name="pharmmapper_email"', dashboard.approval_fields("run-b", review, include_email=False))

    def test_landing_page_contains_only_new_registration(self):
        self.assertNotIn("3. 분석 경로 결정", dashboard.index())

    def test_new_project_is_saved_before_compound_registration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = dashboard.create_project("UC two compounds", Path(temp_dir))
            saved = dashboard.read_project(project["project_id"], Path(temp_dir))
        self.assertEqual(saved["name"], "UC two compounds")
        self.assertEqual(saved["status"], "DRAFT")
        self.assertEqual(saved["run_ids"], [])

    def test_saved_page_only_shows_next_compound_action(self):
        page = dashboard.saved_page("project-a", "run-a", "run-b")
        self.assertIn("다음 화합물 결정", page)
        self.assertNotIn("3. 분석 경로 결정", page)

    def test_new_compound_form_is_collapsed_until_requested(self):
        page = dashboard.new_compound_form("project-a")
        self.assertIn("<details>", page)
        self.assertIn("새 화합물 추가", page)
        self.assertIn('name="project" value="project-a"', page)

    def test_completed_decision_is_labelled_completed(self):
        self.assertEqual(dashboard.decision_status({"user_approved": True}), "분석 경로 확정 완료")
        self.assertEqual(dashboard.decision_status({}), "결정 필요")

    def test_begin_run_analysis_prepares_local_evidence_without_external_submission(self):
        class Response:
            content=(b"PUBCHEM TEST\n" + b"x"*120 + b"\n$$$$\n")
            def raise_for_status(self): pass
        with tempfile.TemporaryDirectory() as temp_dir:
            run=Path(temp_dir)/"CID12345_20261010"
            run.mkdir()
            request={"run_id":run.name,"compound_input":"Test (CID 12345)","compound_cid":"12345","compound_smiles":"CCO","compound_title":"Test","species":"Homo sapiens"}
            dashboard.m.save(run/"request.json",request)
            dashboard.m.save(run/"initial_approval.json",{"user_approved":True,"new_submission_authorized":True})
            with mock.patch.object(dashboard.requests,"get",return_value=Response()):
                result=dashboard.begin_run_analysis(run)
            self.assertEqual(result["status"],"LOCAL_PREPARATION_COMPLETE")
            self.assertFalse(result["external_submission_performed"])
            self.assertTrue((run/"structure_manifest.json").exists())
            self.assertEqual(set(result["prepared_providers"]),{"SEA","PharmMapper"})

    def test_begin_run_analysis_retries_pubchem_2d_after_3d_not_found(self):
        class FailedResponse:
            def raise_for_status(self): raise RuntimeError("404")
        class GoodResponse:
            content=(b"PUBCHEM TEST\n" + b"x"*120 + b"\n$$$$\n")
            def raise_for_status(self): pass
        with tempfile.TemporaryDirectory() as temp_dir:
            run=Path(temp_dir)/"CID12346_20261010"
            run.mkdir()
            dashboard.m.save(run/"request.json",{"run_id":run.name,"compound_input":"Test (CID 12346)","compound_cid":"12346","compound_smiles":"CCO","compound_title":"Test","species":"Homo sapiens"})
            dashboard.m.save(run/"initial_approval.json",{"user_approved":True,"new_submission_authorized":True})
            with mock.patch.object(dashboard.requests,"get",side_effect=[FailedResponse(),GoodResponse()]):
                result=dashboard.begin_run_analysis(run)
            manifest=dashboard.m.read(run/"structure_manifest.json")
            attempts=dashboard.m.read(run/"source_attempts.json")["attempts"]
            self.assertEqual(result["status"],"LOCAL_PREPARATION_COMPLETE")
            self.assertEqual(manifest["record_type"],"2d")
            self.assertEqual([item["status"] for item in attempts],["FAILED","RETRIEVED"])

    def test_prepared_run_exposes_external_submission_stage_not_repeat_button(self):
        source = Path(dashboard.__file__).read_text(encoding="utf-8")
        self.assertIn('def submit_pharmmapper(run, email):', source)
        self.assertIn('def external_submission_panel(project):', source)
        self.assertNotIn('로컬 분석 준비 다시 점검', source)

    def test_external_submission_stage_provides_copyable_sea_inputs(self):
        source = Path(dashboard.__file__).read_text(encoding="utf-8")
        self.assertIn('def sea_copy_control(label, value):', source)
        self.assertIn('SEA SMILES', source)
        self.assertIn('navigator.clipboard.writeText', source)
        self.assertIn('def retrieve_sea_result(run):', source)
        self.assertIn('SEA 자동 제출 확인됨', source)

    def test_duplicate_check_is_project_scoped_not_workspace_scoped(self):
        source = Path(dashboard.__file__).read_text(encoding="utf-8")
        self.assertIn('project_runs=[WORKSPACE/"runs"/run_id', source)
        self.assertNotIn('existing_runs=[a for a in (WORKSPACE/"runs").glob("*")]', source)

    def test_legacy_decision_page_is_not_reached_by_navigation_routes(self):
        source = Path(dashboard.__file__).read_text(encoding="utf-8")
        self.assertEqual(source.count("decision_page("), 1)

    def test_zero_candidate_runs_use_one_compact_submission_form(self):
        page = dashboard.zero_candidate_form("project-a", ["run-a", "run-b"])
        self.assertIn('name="run_ids" value="run-a,run-b"', page)
        self.assertIn("신규 제출 경로 확정", page)
        self.assertIn('name="pharmmapper_email"', page)

    def test_pharmmapper_submission_records_job_without_persisting_email(self):
        class Response:
            text = "Accepted job 261010123456"
            def raise_for_status(self): pass
        with tempfile.TemporaryDirectory() as temp_dir:
            run = Path(temp_dir) / "CID75596314_20261010"
            raw = run / "source_archive" / "PubChem" / "75596314_test.sdf"
            raw.parent.mkdir(parents=True)
            raw.write_bytes(b"test sdf\n  -OEChem- 2D\nV2000\n$$$$\n")
            dashboard.m.save(run / "structure_manifest.json", {"cid":"75596314", "structure_file":str(raw), "structure_sha256":dashboard.sha256_file(raw)})
            submissions = run / "submissions"; submissions.mkdir()
            dashboard.m.save(submissions / "PharmMapper_test.json", {"submission_status":"PREPARED_NOT_SUBMITTED", "compound_tag":"NP-75596314-test"})
            with mock.patch.object(dashboard.requests, "post", return_value=Response()) as posted:
                result = dashboard.submit_pharmmapper(run, "person@example.org")
            ledger = dashboard.m.read(run / "job_ledger.json")
            self.assertTrue(posted.called)
            self.assertEqual(result["job_id"], "261010123456")
            self.assertEqual(ledger["pharmmapper_submission"]["job_id"], "261010123456")
            self.assertFalse(ledger["pharmmapper_submission"]["email_stored"])
            self.assertNotIn("person@example.org", json.dumps(ledger))

    def test_pharmmapper_response_review_is_idempotent_and_blocks_resubmission(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run = Path(temp_dir) / "CID75596314_20261010"
            dashboard.m.save(run / "job_ledger.json", {"pharmmapper_submission": {
                "status": "SUBMITTED_RESPONSE_REVIEW_REQUIRED", "job_id": None, "response_sha256": "abc"
            }})
            with mock.patch.object(dashboard.requests, "post") as posted:
                result = dashboard.submit_pharmmapper(run, "person@example.org")
            self.assertTrue(result["already_recorded"])
            posted.assert_not_called()

    def test_pharmmapper_response_without_job_id_is_not_confirmed(self):
        class Response:
            text = "accepted"
            def raise_for_status(self): pass
        with tempfile.TemporaryDirectory() as temp_dir:
            run = Path(temp_dir) / "CID75596314_20261010"
            raw = run / "source_archive" / "PubChem" / "test.sdf"
            raw.parent.mkdir(parents=True)
            raw.write_bytes(b"test sdf\nV2000\n$$$$\n")
            dashboard.m.save(run / "structure_manifest.json", {"cid":"75596314", "structure_file":str(raw), "structure_sha256":dashboard.sha256_file(raw)})
            submissions = run / "submissions"; submissions.mkdir()
            dashboard.m.save(submissions / "PharmMapper_test.json", {"submission_status":"PREPARED_NOT_SUBMITTED", "compound_tag":"NP-75596314-test"})
            with mock.patch.object(dashboard.requests, "post", return_value=Response()):
                result = dashboard.submit_pharmmapper(run, "person@example.org")
            ledger = dashboard.m.read(run / "job_ledger.json")
            self.assertIsNone(result["job_id"])
            self.assertEqual(ledger["pharmmapper_submission"]["status"], "SUBMISSION_NOT_CONFIRMED")
            self.assertEqual(ledger["pharmmapper_submission"]["next_action_code"], "PROVIDER_BROWSER_SUBMIT_REQUIRED")

    def test_external_job_id_resume_updates_provider_without_resubmission(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run = Path(temp_dir) / "CID75596314_20261010"
            run.mkdir()
            dashboard.m.save(run / "request.json", {"run_id": run.name})
            dashboard.m.save(run / "job_ledger.json", {"pharmmapper_submission": {
                "status": "SUBMITTED_RESPONSE_REVIEW_REQUIRED", "job_id": None,
                "response_sha256": "abc"
            }})
            dashboard.m.save(run / "analysis_progress.json", {
                "status": "PHARMMAPPER_SUBMISSION_RESPONSE_REVIEW_REQUIRED"
            })
            row = dashboard.record_external_job(run, "pharmmapper", "261010123456")
            self.assertEqual(row["status"], "SUBMITTED")
            self.assertEqual(row["job_id"], "261010123456")
            progress = dashboard.m.read(run / "analysis_progress.json")
            self.assertEqual(progress["status"], "PHARMMAPPER_SUBMITTED")

    def test_external_job_id_resume_rejects_invalid_url(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run = Path(temp_dir) / "CID75596314_20261010"
            run.mkdir()
            with self.assertRaises(ValueError):
                dashboard.record_external_job(run, "sea", "sea-123", "javascript:alert(1)")

if __name__ == "__main__":
    unittest.main()
