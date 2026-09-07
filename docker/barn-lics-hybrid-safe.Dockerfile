# Q-24 candidate: Q-21's close-range shield plus Q-23's fresh EBand fallback
# in the earlier near-obstacle band.
FROM vrx-record-lab:barn-lics-safe

RUN python3 - <<'PY'
from pathlib import Path

path = Path('/opt/barn_ws/src/the-barn-challenge/lics/scripts/env/robot.py')
text = path.read_text()
sub_old = "        # rospy.Subscriber('/move_base/cmd_vel', Twist, self.get_lp_velocity, queue_size=1)\n"
sub_new = "        rospy.Subscriber('/move_base/cmd_vel', Twist, self.get_lp_velocity, queue_size=1)\n"
if text.count(sub_old) != 1:
    raise SystemExit('expected commented planner subscriber')
text = text.replace(sub_old, sub_new)
stamp_old = "        self.lp_vel = np.zeros((2,), dtype=np.float32)\n"
stamp_new = "        self.lp_vel = np.zeros((2,), dtype=np.float32)\n        self.lp_stamp = 0.0\n"
if text.count(stamp_old) != 1:
    raise SystemExit('expected planner velocity state')
text = text.replace(stamp_old, stamp_new)
callback_old = "        self.lp_vel[:] = (v, w)\n"
callback_new = "        self.lp_vel[:] = (v, w)\n        self.lp_stamp = rospy.get_time()\n"
if text.count(callback_old) != 1:
    raise SystemExit('expected planner callback')
text = text.replace(callback_old, callback_new)
anchor = "            angular = w * self.max_w\n            # Policy-only commands can continue into a previously unseen\n"
replacement = """            angular = w * self.max_w
            front = float(np.min(self.laser[300:420]))
            # In the near-obstacle band, use a fresh collision-aware EBand
            # command. The close-range Q-21 shield below still overrides it.
            planner_fresh = (rospy.get_time() - self.lp_stamp) < 0.5
            if front < 0.90 and planner_fresh and np.linalg.norm(self.lp_vel) > 1e-3:
                linear = float(self.lp_vel[0]) * self.max_v
                angular = float(self.lp_vel[1]) * self.max_w
            # Policy-only commands can continue into a previously unseen
"""
if text.count(anchor) != 1:
    raise SystemExit('expected Q-21 command anchor')
text = text.replace(anchor, replacement)
path.write_text(text)
PY
RUN grep -q 'planner_fresh' /opt/barn_ws/src/the-barn-challenge/lics/scripts/env/robot.py

LABEL org.opencontainers.image.source="https://github.com/RetiefLouw/vrx-record-lab" \
      org.opencontainers.image.description="Pinned BARN LiCS-KI with EBand near-obstacle fallback and close-range shield" \
      org.opencontainers.image.lics.commit="f7bd87cc232b04f6ce9edd10a6a05b84a6c7dfaa" \
      org.opencontainers.image.safety="eband-fallback-plus-close-shield-v1"
