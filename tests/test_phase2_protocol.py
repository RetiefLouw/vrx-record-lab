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
        frozen = json.loads(
            (REPO_ROOT / "config/experiments/vrx2019-station-keeping-practice0-fast-pd.json").read_text(encoding="utf-8")
        )
        self.assertEqual(self.manifest["controller"]["name"], frozen["controller"]["name"])
        self.assertEqual(self.manifest["controller"]["revision"], frozen["controller"]["revision"])
        self.assertEqual(self.manifest["controller"]["parameters"], frozen["controller"]["parameters"])
        self.assertEqual(self.manifest["controller"]["name"], "saturation-aware-fast-pd-stock-t-thrusters")
        self.assertTrue(self.manifest["controller"]["runtime"]["enabled"])
        self.assertEqual(
            self.manifest["controller"]["parameters"]["position_source"],
            "/wamv/sensors/gps/gps/fix",
        )
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

    def test_controller_command_and_runtime_are_pinned(self):
        self.manifest["controller"]["command"] = []
        with self.assertRaisesRegex(Phase2ProtocolError, "launch the ROS scored"):
            validate_phase2_protocol(self.manifest)

    def test_controller_sensor_topics_are_manifest_parameters(self):
        self.manifest["controller"]["parameters"]["position_source"] = "/test/gps/fix"
        validate_phase2_protocol(self.manifest)

    def test_phase2_runner_wires_controller_and_diagnostics(self):
        runner = (REPO_ROOT / "src/vrx_record_lab/phase2_trial.py").read_text(encoding="utf-8")
        container_runner = (REPO_ROOT / "docker/run-phase2-stationkeeping.sh").read_text(encoding="utf-8")
        for marker in (
            "VRX_PHASE2_CONTROLLER_ENABLED",
            "VRX_CONTROLLER_PARAMETERS_JSON",
            "VRX_CONTROLLER_POSITION_SOURCE",
            "VRX_CONTROLLER_DIAGNOSTICS_TOPIC",
            "VRX_RUNNING_STATE_DURATION_OVERRIDE",
        ):
            self.assertIn(marker, runner)
        self.assertIn("vrx_controller_ros scored_station_keeping.launch", container_runner)
        self.assertIn("--require-controller-diagnostics", container_runner)

    def test_hybrid_candidate_inherits_frozen_world_protocol(self):
        from vrx_record_lab.manifest import load_manifest

        candidate = load_manifest(REPO_ROOT / "config/experiments/vrx2019-station-keeping-phase2-hybrid-transit.json")
        baseline = load_manifest(MANIFEST)
        self.assertEqual(
            candidate["task"]["parameters"]["protocol"]["worlds"],
            baseline["task"]["parameters"]["protocol"]["worlds"],
        )
        self.assertEqual(candidate["trials"], baseline["trials"])
        self.assertEqual(candidate["controller"]["parameters"]["guidance_mode"], "hybrid")
        self.assertEqual(candidate["controller"]["parameters"]["transit_radius_m"], 8.0)

    def test_observer_candidate_inherits_frozen_world_protocol(self):
        from vrx_record_lab.manifest import load_manifest

        candidate = load_manifest(REPO_ROOT / "config/experiments/vrx2019-station-keeping-phase2-hybrid-observer.json")
        self.assertEqual(candidate["controller"]["parameters"]["disturbance_observer_bandwidth_hz"], 0.15)
        self.assertEqual(len(candidate["task"]["parameters"]["protocol"]["worlds"]), 6)


if __name__ == "__main__":
    unittest.main()
