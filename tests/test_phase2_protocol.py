import json
import unittest
from pathlib import Path

from vrx_record_lab.phase2_protocol import Phase2ProtocolError, select_phase2_world, validate_phase2_protocol


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "config/experiments/vrx2019-station-keeping-phase2.json"


class Phase2ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_describes_six_explicit_complete_worlds(self):
        validate_phase2_protocol(self.manifest)
        protocol = self.manifest["task"]["parameters"]["protocol"]
        self.assertEqual(protocol["run_mode"], "complete_scored")
        self.assertEqual(protocol["scored_running_duration_s"], 300)
        self.assertEqual(
            [world["id"] for world in protocol["worlds"]],
            [f"stationkeeping{i}" for i in range(6)],
        )
        self.assertEqual(len({world["source_sha256"] for world in protocol["worlds"]}), 6)

    def test_trial_index_selects_matching_world(self):
        self.assertEqual(select_phase2_world(self.manifest, 0)["id"], "stationkeeping0")
        self.assertEqual(select_phase2_world(self.manifest, 5)["id"], "stationkeeping5")
        with self.assertRaises(Phase2ProtocolError):
            select_phase2_world(self.manifest, 6)

    def test_shortened_protocol_cannot_be_used_by_canonical_manifest(self):
        self.manifest["task"]["parameters"]["protocol"]["scored_running_duration_s"] = 30
        with self.assertRaisesRegex(Phase2ProtocolError, "must be 300"):
            validate_phase2_protocol(self.manifest)

    def test_world_path_is_pinned_to_public_phase2_tree(self):
        self.manifest["task"]["parameters"]["protocol"]["worlds"][0]["path"] = "../stationkeeping0.world"
        with self.assertRaisesRegex(Phase2ProtocolError, "path must be"):
            validate_phase2_protocol(self.manifest)


if __name__ == "__main__":
    unittest.main()
