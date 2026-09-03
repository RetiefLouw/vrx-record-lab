import json
from pathlib import Path

from vrx_controller import force_to_command, command_to_force, quaternion_to_yaw, wgs84_to_local_enu


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_wgs84_datum_and_yaw_conventions():
    assert wgs84_to_local_enu(21.30996, -157.8901, 21.30996, -157.8901) == (0.0, 0.0)
    assert abs(quaternion_to_yaw(0.0, 0.0, 0.70710678118, 0.70710678118) - 1.57079632679) < 1e-9


def test_stock_thruster_mapping_round_trips_force_requests():
    for force in (-90.0, -20.0, 20.0, 140.0, 240.0):
        command = force_to_command(force)
        assert -1.0 <= command <= 1.0
        assert abs(command_to_force(command) - force) < 1e-6


def test_ros_boundary_declares_real_vrx_topics_and_unlocked_robot():
    launch = (REPO_ROOT / "ros/vrx_controller_ros/launch/scored_station_keeping.launch").read_text()
    node = (REPO_ROOT / "ros/vrx_controller_ros/scripts/station_keeping_node.py").read_text()
    assert 'wamv_locked:=false' not in launch  # launch forwards the explicit arg rather than hard-coding it
    assert 'wamv_locked" default="false"' in launch
    assert "/wamv/robot_localization/odometry/filtered" in launch
    assert "/vrx/station_keeping/goal" in node
    assert "std_msgs.msg import Float32" in node
    assert "force_to_command" in node


def test_practice_manifest_is_complete_and_runnable():
    path = REPO_ROOT / "config/experiments/vrx2019-station-keeping-practice0-baseline.json"
    manifest = json.loads(path.read_text())
    assert manifest["execution"]["command"] == ["../../scripts/run_vrx_trial"]
    assert manifest["trials"]["seeds"] == [10]
    assert manifest["task"]["parameters"]["running_state_duration_s"] == 300.0
