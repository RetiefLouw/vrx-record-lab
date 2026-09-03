import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from vrx_record_lab.diagnostics import DiagnosticsError, extract_diagnostics, extract_trial_diagnostics
from vrx_record_lab.extract_diagnostics import main as extract_diagnostics_cli


class DiagnosticsTests(unittest.TestCase):
    def write_trial(self, directory: Path, *, controller_rows=None):
        task_rows = [
            {"ros_time_s": 0.0, "state": "initial"},
            {"ros_time_s": 10.0, "state": "running"},
            {"ros_time_s": 40.0, "state": "finished"},
        ]
        controller_rows = controller_rows or [
            {
                "stamp_s": 10.0,
                "position_source": "/wamv/sensors/gps/gps/fix",
                "measured_x_m": 2.0,
                "measured_y_m": 0.0,
                "measured_yaw_rad": 0.1,
                "target_x_m": 0.0,
                "target_y_m": 0.0,
                "target_yaw_rad": 0.0,
                "force_left_n": 240.0,
                "force_right_n": 50.0,
                "force_lateral_n": 0.0,
            },
            {
                "stamp_s": 20.0,
                "position_source": "/wamv/sensors/gps/gps/fix",
                "measured_x_m": 0.4,
                "measured_y_m": 0.0,
                "measured_yaw_rad": 0.2,
                "target_x_m": 0.0,
                "target_y_m": 0.0,
                "target_yaw_rad": 0.0,
                "force_left_n": 10.0,
                "force_right_n": 10.0,
                "force_lateral_n": 0.0,
            },
            {
                "stamp_s": 30.0,
                "position_source": "/wamv/sensors/gps/gps/fix",
                "measured_x_m": 0.2,
                "measured_y_m": 0.0,
                "measured_yaw_rad": 0.05,
                "target_x_m": 0.0,
                "target_y_m": 0.0,
                "target_yaw_rad": 0.0,
                "force_left_n": 10.0,
                "force_right_n": 10.0,
                "force_lateral_n": 0.0,
            },
        ]
        (directory / "task-info.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in task_rows), encoding="utf-8"
        )
        (directory / "controller-diagnostics.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in controller_rows), encoding="utf-8"
        )

    def test_extracts_q03_metrics_without_ros(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.write_trial(directory)
            document = extract_trial_diagnostics(directory)
            self.assertEqual(document["schema_version"], "vrx-controller-diagnostics/v1")
            self.assertEqual(document["run_window"]["duration_s"], 30.0)
            self.assertEqual(document["metrics"]["time_to_0_5_m_s"], 10.0)
            self.assertEqual(document["metrics"]["time_to_0_25_m_s"], 20.0)
            self.assertAlmostEqual(document["metrics"]["max_position_error_m"], 2.0)
            self.assertAlmostEqual(document["metrics"]["max_yaw_error_rad"], 0.2)
            self.assertAlmostEqual(document["metrics"]["peak_force_abs_n"], 240.0)
            self.assertAlmostEqual(document["metrics"]["force_saturation_fraction"], 1.0 / 3.0)
            self.assertEqual(document["quality"]["running_controller_message_count"], 3)

    def test_suite_discovery_returns_stable_trial_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, stamp in (("trial-0002.artifacts", 20.0), ("trial-0001.artifacts", 10.0)):
                directory = root / "trials" / name
                directory.mkdir(parents=True)
                self.write_trial(directory)
                task_path = directory / "task-info.jsonl"
                task_path.write_text(task_path.read_text().replace('"ros_time_s": 0.0', f'"ros_time_s": {stamp}'), encoding="utf-8")
            document = extract_diagnostics(root)
            self.assertEqual(document["scope"]["trial_count"], 2)
            self.assertEqual(document["trials"][0]["source"]["trial_directory"], str((root / "trials" / "trial-0001.artifacts").resolve()))

    def test_missing_controller_stream_is_explicit(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "task-info.jsonl").write_text('{"ros_time_s": 1, "state": "running"}\n', encoding="utf-8")
            with self.assertRaisesRegex(DiagnosticsError, "missing controller diagnostics"):
                extract_trial_diagnostics(directory)

    def test_cli_writes_canonical_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.write_trial(directory)
            output = directory / "diagnostics.json"
            self.assertEqual(extract_diagnostics_cli([str(directory), "--output", str(output)]), 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["schema_version"], "vrx-controller-diagnostics/v1")


if __name__ == "__main__":
    unittest.main()
