"""Tests for local post-training evaluation helpers."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = ROOT / "job-radar-eval"
if str(EVAL_ROOT) not in sys.path:
    sys.path.insert(0, str(EVAL_ROOT))

from job_radar_eval.local_responses_client import LocalTransformersClient  # noqa: E402


class LocalPostTrainingEvalTests(unittest.TestCase):
    def test_local_transformers_client_is_lazy(self) -> None:
        client = LocalTransformersClient(
            "Qwen/Qwen3-4B-Instruct-2507",
            max_input_tokens=2048,
            trust_remote_code=True,
        )

        self.assertEqual(client.responses.config.model_name_or_path, "Qwen/Qwen3-4B-Instruct-2507")
        self.assertEqual(client.responses.config.max_input_tokens, 2048)
        self.assertTrue(client.responses.config.trust_remote_code)
        self.assertIsNone(client.responses._model)
        self.assertIsNone(client.responses._tokenizer)

    def test_run_post_training_local_eval_help(self) -> None:
        script_path = ROOT / "job-radar-eval" / "scripts" / "run_post_training_local_eval.py"
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--sft-model-source", result.stdout)
        self.assertIn("--dpo-model-source", result.stdout)
        self.assertIn("--artifact-repo", result.stdout)


if __name__ == "__main__":
    unittest.main()
