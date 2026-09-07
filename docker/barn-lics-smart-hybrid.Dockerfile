# Q-25 candidate: select between Q-23's EBand fallback and Q-21's emergency
# turn using the observed clearance direction. This keeps the Q-21 repair when
# the planner points into the obstacle, while preserving EBand on world 294.
FROM vrx-record-lab:barn-lics-hybrid-safe

RUN python3 - <<'PY'
from pathlib import Path

path = Path('/opt/barn_ws/src/the-barn-challenge/lics/scripts/env/robot.py')
text = path.read_text()
old = """            if front < 0.75:
                left = float(np.mean(self.laser[420:600]))
                right = float(np.mean(self.laser[120:300]))
                linear = 0.0
                angular = 0.8 * self.max_w if left >= right else -0.8 * self.max_w
"""
new = """            if front < 0.75:
                left = float(np.mean(self.laser[420:600]))
                right = float(np.mean(self.laser[120:300]))
                clear_turn = 0.8 * self.max_w if left >= right else -0.8 * self.max_w
                planner_turn = float(self.lp_vel[1]) * self.max_w
                planner_agrees = (planner_fresh and np.linalg.norm(self.lp_vel) > 1e-3
                                  and abs(planner_turn) > 0.15
                                  and np.sign(planner_turn) == np.sign(clear_turn))
                if planner_agrees:
                    linear = float(self.lp_vel[0]) * self.max_v
                    angular = planner_turn
                else:
                    linear = 0.0
                    angular = clear_turn
"""
if text.count(old) != 1:
    raise SystemExit('expected exactly one close-range shield block')
path.write_text(text.replace(old, new))
PY
RUN grep -q 'planner_agrees' /opt/barn_ws/src/the-barn-challenge/lics/scripts/env/robot.py

LABEL org.opencontainers.image.source="https://github.com/RetiefLouw/vrx-record-lab" \
      org.opencontainers.image.description="Pinned BARN LiCS-KI smart hybrid safety candidate" \
      org.opencontainers.image.lics.commit="f7bd87cc232b04f6ce9edd10a6a05b84a6c7dfaa" \
      org.opencontainers.image.safety="planner-agreement-shield-v1"
