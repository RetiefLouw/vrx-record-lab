import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from vrx_record_lab.manifest import ManifestError, load_manifest
from vrx_record_lab.runner import TrialError, run_suite
from vrx_record_lab.stats import aggregate_scores
from vrx_record_lab.verify import verify_result
from vrx_record_lab.verify_result import main as verify_result_main


REPO = Path(__file__).parents[1]
BASELINE = REPO / "config/experiments/vrx2019-station-keeping-upstream.json"
FIXTURE = REPO / "tests/fixtures/emit_trial.py"


class HarnessTests(unittest.TestCase):
    def fixture_manifest(self, directory: Path) -> Path:
        manifest = {
            "$schema": "../../schemas/experiment.schema.json",
            "schema_version": "1.0.0",
            "experiment_id": "fixture-suite",
            "benchmark": {
                "name": "fixture-benchmark",
                "revision": "benchmark-revision",
                "protocol_revision": "protocol-revision",
                "score_direction": "minimize",
                "scorer": {"name": "fixture-scorer", "revision": "scorer-revision"},
            },
            "controller": {
                "name": "fixture-controller",
                "source": "tests/fixtures/emit_trial.py",
                "revision": "controller-revision",
                "command": [],
                "parameters": {"mode": "fixture"},
            },
            "container": {"image": "fixture/image", "digest": "sha256:fixture"},
            "task": {"name": "fixture-task", "parameters": {"duration_s": 1}},
            "trials": {"seeds": [1, 2, 3], "seed_provenance": "test-owned deterministic seeds", "environment": {}},
            "execution": {"command": [sys.executable, str(FIXTURE)], "timeout_s": 10, "cwd": None},
        }
        path = directory / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return path

    def test_statistics_are_deterministic_and_lower_score_worst_case_is_maximum(self):
        aggregate = aggregate_scores([0.1, 0.2, 0.3], "minimize")
        self.assertEqual(aggregate["count"], 3)
        self.assertAlmostEqual(aggregate["mean"], 0.2)
        self.assertAlmostEqual(aggregate["median"], 0.2)
        self.assertAlmostEqual(aggregate["stddev"], 0.1)
        self.assertEqual(aggregate["worst_case"], 0.3)
        self.assertLess(aggregate["confidence_interval_95"]["low"], 0.2)
        self.assertGreater(aggregate["confidence_interval_95"]["high"], 0.2)

    def test_fixture_suite_writes_canonical_result_and_verifies(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            manifest_path = self.fixture_manifest(directory)
            result, result_path = run_suite(manifest_path, directory / "run", result_id="fixture-result")
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["aggregate"]["count"], 3)
            self.assertAlmostEqual(result["aggregate"]["mean"], 0.2)
            self.assertTrue((directory / "run/SHA256SUMS").is_file())
            report = verify_result(result_path, manifest_path)
            self.assertTrue(report["verified"], report)
            self.assertTrue(report["claim_eligible"])

    def test_artifact_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            manifest_path = self.fixture_manifest(directory)
            _, result_path = run_suite(manifest_path, directory / "run", result_id="tamper-result")
            artifact = directory / "run/trials/trial-0001.stdout.log"
            artifact.write_text("tampered\n", encoding="utf-8")
            report = verify_result(result_path, manifest_path)
            self.assertFalse(report["verified"])
            self.assertTrue(any(not check["passed"] for check in report["checks"]))

    def test_verifier_can_write_result_and_standalone_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            manifest_path = self.fixture_manifest(directory)
            _, result_path = run_suite(manifest_path, directory / "run", result_id="verified-result")
            report_path = directory / "run" / "verification.json"

            exit_code = verify_result_main(
                [str(result_path), "--manifest", str(manifest_path), "--write", "--output", str(report_path)]
            )

            self.assertEqual(exit_code, 0)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            result = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertTrue(report["verified"])
            self.assertEqual(report["claim_scope"], "local_result_integrity_only")
            self.assertFalse(report["record_claim_eligible"])
            self.assertEqual(result["verification"], report)

    def test_empty_adapter_command_is_refused_without_fabricating_result(self):
        manifest = load_manifest(BASELINE)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(TrialError):
                run_suite(BASELINE, Path(temporary) / "run")
        self.assertEqual(manifest["execution"]["command"], [])

    def test_unlisted_seed_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest_path = self.fixture_manifest(Path(temporary))
            manifest = load_manifest(manifest_path)
            output = Path(temporary) / "trial.json"
            from vrx_record_lab.runner import execute_trial

            with self.assertRaises(TrialError):
                execute_trial(manifest_path, manifest, 99, output, "trial-unlisted")

    def test_result_schema_files_are_valid_json(self):
        for path in (
            REPO / "schemas/experiment.schema.json",
            REPO / "schemas/result.schema.json",
            REPO / "schemas/diagnostics.schema.json",
        ):
            with self.subTest(path=path):
                value = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(value["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_manifest_rejects_duplicate_seeds(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.fixture_manifest(Path(temporary))
            value = json.loads(path.read_text(encoding="utf-8"))
            value["trials"]["seeds"] = [1, 1]
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(ManifestError):
                load_manifest(path)


if __name__ == "__main__":
    unittest.main()
