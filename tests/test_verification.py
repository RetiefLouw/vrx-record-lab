import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from verification.verify import (
    VerificationError,
    check_benchmark_tree,
    check_manifest,
    check_seed_sets,
    clean_clone,
    create_manifest,
    validate_result,
    write_json,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_RESULT = REPO_ROOT / "verification/examples/result.json"
SCHEMA = REPO_ROOT / "verification/result.schema.json"
SEEDS = REPO_ROOT / "verification/seed_sets.json"
INTEGRITY = REPO_ROOT / "verification/benchmark_paths.json"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


class VerificationTests(unittest.TestCase):
    def test_example_result_validates_with_artifact_manifest(self) -> None:
        summary = validate_result(
            EXAMPLE_RESULT,
            SCHEMA,
            root=REPO_ROOT / "verification/examples/artifacts",
            seed_config=SEEDS,
            manifest=REPO_ROOT / "verification/examples/artifacts/SHA256SUMS.json",
        )
        self.assertEqual(summary["runs"], 6)
        self.assertEqual(summary["comparability"], "not_comparable")

    def test_bad_aggregate_is_rejected(self) -> None:
        result = json.loads(EXAMPLE_RESULT.read_text(encoding="utf-8"))
        result["aggregate"]["value"] = 0.31
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "result.json"
            write_json(path, result)
            with self.assertRaisesRegex(VerificationError, "aggregate.value"):
                validate_result(path, SCHEMA)

    def test_promoted_claim_requires_independent_evidence(self) -> None:
        result = json.loads(EXAMPLE_RESULT.read_text(encoding="utf-8"))
        result["claim_status"] = "promoted"
        result["protocol"]["comparability"] = "direct"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "result.json"
            write_json(path, result)
            with self.assertRaisesRegex(VerificationError, "independently verified"):
                validate_result(
                    path,
                    SCHEMA,
                    root=REPO_ROOT / "verification/examples/artifacts",
                    seed_config=SEEDS,
                    manifest=REPO_ROOT / "verification/examples/artifacts/SHA256SUMS.json",
                )

    def test_seed_overlap_is_rejected(self) -> None:
        config = json.loads(SEEDS.read_text(encoding="utf-8"))
        config["sets"]["hidden_evaluation"]["seeds"][0] = config["sets"]["development"]["seeds"][0]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "seeds.json"
            write_json(path, config)
            with self.assertRaisesRegex(VerificationError, "overlap|multiple sets"):
                check_seed_sets(path)

    def test_manifest_detects_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "artifacts"
            root.mkdir()
            payload = root / "payload.txt"
            payload.write_text("before\n", encoding="utf-8")
            manifest_path = root / "SHA256SUMS.json"
            write_json(manifest_path, create_manifest(root, manifest_path))
            self.assertEqual(check_manifest(root, manifest_path)["files"], 1)
            payload.write_text("after\n", encoding="utf-8")
            with self.assertRaisesRegex(VerificationError, "manifest mismatch"):
                check_manifest(root, manifest_path)

    def test_benchmark_tree_change_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
            (repo / "benchmark").mkdir()
            (repo / "benchmark" / "score.py").write_text("return 1\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "baseline"], check=True)
            base = git(repo, "rev-parse", "HEAD")
            (repo / "benchmark" / "score.py").write_text("return 2\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "change"], check=True)
            config = {
                "schema_version": "vrx-benchmark-integrity/v1",
                "protected_prefixes": ["benchmark"],
                "protected_exact_paths": [],
                "allow_missing": False,
            }
            config_path = repo / "integrity.json"
            write_json(config_path, config)
            with self.assertRaisesRegex(VerificationError, "protected benchmark/scorer paths changed"):
                check_benchmark_tree(repo, config_path, base, "HEAD")

    def test_clean_clone_checks_exact_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
            (repo / "README").write_text("clean clone\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "README"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "initial"], check=True)
            commit = git(repo, "rev-parse", "HEAD")
            summary = clean_clone(str(repo), commit, None, f'{sys.executable} -c "import os; assert os.environ[\'VRX_CLEAN_CLONE\'] == \'1\'"')
            self.assertTrue(summary["clean"])
            self.assertEqual(summary["commit"], commit)


if __name__ == "__main__":
    unittest.main()
