# Q-23 candidate: keep LiCS-KI for nominal motion and delegate only near-
# obstacle commands to the already-running EBand local planner.
FROM vrx-record-lab:barn-lics-ready

RUN python3 - <<'PY'
from pathlib import Path

path = Path('/opt/barn_ws/src/the-barn-challenge/lics/scripts/env/robot.py')
text = path.read_text()
replacements = {
    "        # rospy.Subscriber('/move_base/cmd_vel', Twist, self.get_lp_velocity, queue_size=1)\n":
    "        rospy.Subscriber('/move_base/cmd_vel', Twist, self.get_lp_velocity, queue_size=1)\n",
    "        self.lp_vel = np.zeros((2,), dtype=np.float32)\n":
    "        self.lp_vel = np.zeros((2,), dtype=np.float32)\n        self.lp_stamp = 0.0\n",
    "    def set_velocity(self, v, w):\n        # Scale the velocity to the maximum and minimum values and clip\n        if self.state == STATE_NORMAL:\n            twist = Twist()\n            twist.linear.x = np.clip(v * self.max_v * self.v_multiplier, self.min_v, self.max_v)\n            twist.angular.z = np.clip(w * self.max_w, self.min_w, self.max_w)\n            self.vel_pub.publish(twist)\n":
    "    def set_velocity(self, v, w):\n        # Scale the velocity to the maximum and minimum values and clip\n        if self.state == STATE_NORMAL:\n            twist = Twist()\n            linear = v * self.max_v * self.v_multiplier\n            angular = w * self.max_w\n            front = float(np.min(self.laser[300:420]))\n            # Near an obstacle, prefer the collision-aware EBand command if\n            # it is fresh. LiCS remains the nominal controller in open space.\n            planner_fresh = (rospy.get_time() - self.lp_stamp) < 0.5\n            if front < 0.90 and planner_fresh and np.linalg.norm(self.lp_vel) > 1e-3:\n                linear = float(self.lp_vel[0]) * self.max_v\n                angular = float(self.lp_vel[1]) * self.max_w\n            twist.linear.x = np.clip(linear, self.min_v, self.max_v)\n            twist.angular.z = np.clip(angular, self.min_w, self.max_w)\n            self.vel_pub.publish(twist)\n",
    "    def get_lp_velocity(self, msg):\n        v = msg.linear.x / self.max_v\n        w = msg.angular.z / self.max_w\n        self.lp_vel[:] = (v, w)\n":
    "    def get_lp_velocity(self, msg):\n        v = msg.linear.x / self.max_v\n        w = msg.angular.z / self.max_w\n        self.lp_vel[:] = (v, w)\n        self.lp_stamp = rospy.get_time()\n",
}
for old, new in replacements.items():
    if text.count(old) != 1:
        raise SystemExit('expected exactly one source block')
    text = text.replace(old, new)
path.write_text(text)
PY
RUN grep -q 'planner_fresh' /opt/barn_ws/src/the-barn-challenge/lics/scripts/env/robot.py

LABEL org.opencontainers.image.source="https://github.com/RetiefLouw/vrx-record-lab" \
      org.opencontainers.image.description="Pinned BARN LiCS-KI hybrid with EBand near-obstacle fallback" \
      org.opencontainers.image.lics.commit="f7bd87cc232b04f6ce9edd10a6a05b84a6c7dfaa" \
      org.opencontainers.image.safety="eband-near-obstacle-fallback-v1"
