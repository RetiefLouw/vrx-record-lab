# ROS/VRX controller boundary

The runnable baseline is `ros/vrx_controller_ros`. It is built into the pinned
ROS Melodic/Gazebo 9 container and is launched by
`scored_station_keeping.launch`.

## Topics and frames

- Input localization: `/wamv/robot_localization/odometry/filtered`,
  `nav_msgs/Odometry`. Position is local ENU metres; twist is body-frame
  `[u, v, r]`.
- Input target: `/vrx/station_keeping/goal`,
  `geographic_msgs/GeoPoseStamped`. The WGS84 latitude/longitude is converted
  to local ENU using datum `(21.30996, -157.8901)`; the quaternion is converted
  to positive-counter-clockwise yaw in radians.
- Output: `/wamv/thrusters/left_thrust_cmd`,
  `/wamv/thrusters/right_thrust_cmd`, and
  `/wamv/thrusters/lateral_thrust_cmd`, each `std_msgs/Float32` in the stock
  normalized command range. Corresponding `_thrust_angle` topics receive zero
  because the baseline uses the fixed stock T layout.
- Scorer observation: `/vrx/task/info`, `vrx_gazebo/Task`. A trial is accepted
  only when this topic reports `state=finished`; the score is copied from its
  `score` field without local recomputation.

The launch passes `wamv_locked:=false`, uses the stock `T` thrust layout, and
starts the upstream localization example. Missing or stale localization and
missing goals result in zero commands.

## Force mapping

The controller allocates physical forces using the stock T geometry. The ROS
node converts each force to the normalized command expected by the upstream
`usv_gazebo_thrust_plugin` using its mapping-type-1 generalized logistic
function. The inverse is a deterministic bisection; no alternate simulator
actuator model is substituted.

## Trial artifacts

`docker/run-trial.sh` starts the launch, records a rosbag, monitors the real
task topic, and writes `adapter-output.json` only after a finished scorer
message. It also retains `task-info.jsonl`, `task-summary.json`,
`trial-protocol.txt`, `simulator.log`, `rosbag.log`, `monitor.log`, and the
bag. The host adapter maps those files into the harness trial artifact
directory, where the suite adds SHA-256 entries.

The practice manifest uses `stationkeeping0.world`, whose pinned public world
sets `random_seed=10`, with no runtime wind-seed override. Its 10 s initial,
10 s ready, and 300 s running intervals are copied into the manifest.
