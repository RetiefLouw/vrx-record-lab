# VRX 2019 station-keeping protocol

Status: reconstruction in progress.

The official results report a station-keeping value of `0.11` for the
University of Florida entry. Before treating that number as a directly
comparable record, this campaign must recover and pin:

- VRX, WAM-V, Gazebo, ROS, and scoring revisions;
- task world, initial pose, target pose, duration, timeout, and reset behavior;
- wind, wave, and current configuration plus randomization seeds;
- scorer formula, sampling interval, transient handling, and penalties;
- preliminary/final run selection and leaderboard aggregation.

Unknown values are never silently replaced. Any reconstructed setting will be
marked as inferred and accompanied by its evidence.
