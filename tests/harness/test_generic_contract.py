import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]


class GenericContractTests(unittest.TestCase):
    def test_required_generic_documents_exist(self):
        names = [
            "HARNESS_GUIDE.md", "AGENT_CONTRACT.md", "CODEX/ChatGPT.md",
            "WORKFLOW_SCHEMA.md", "WORKTREE_POLICY.md", "APPROVAL_POLICY.md",
            "RECOVERY_POLICY.md", "MODEL_ROUTING_POLICY.md", "VALIDATION_GATES.md",
            "EVALUATION_GUIDE.md", "ADAPTER_GUIDE.md", "PROJECT_STATE.md",
        ]
        for name in names:
            self.assertTrue((ROOT / name).is_file(), name)

    def test_schema_contracts_have_required_fields(self):
        workflow = json.loads((ROOT / "schemas/workflow.schema.json").read_text(encoding="utf-8"))
        task = json.loads((ROOT / "schemas/task.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(workflow["required"], ["workflow_id", "goal", "success_criteria", "tasks", "state", "next_action"])
        self.assertEqual(task["required"], ["task_id", "owner", "requires", "status", "max_attempts"])

    def test_workflow_and_worktree_are_distinguished(self):
        workflow = (ROOT / "HARNESS_GUIDE.md").read_text(encoding="utf-8")
        worktree = (ROOT / "WORKTREE_POLICY.md").read_text(encoding="utf-8")
        self.assertIn("workflow와 worktree는 같은 의미가 아니다", workflow)
        self.assertIn("workflow와 worktree를 같은 개념으로 취급하지 않는다", worktree)


if __name__ == "__main__":
    unittest.main()
