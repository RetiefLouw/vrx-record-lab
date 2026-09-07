# Q-22 candidate: Q-21 stable-readiness LiCS plus a directional near-obstacle
# emergency stop/turn. The learned model and benchmark evaluator remain fixed.
FROM vrx-record-lab:barn-lics-safe

RUN python3 - <<'PY'
from pathlib import Path

path = Path('/opt/barn_ws/src/the-barn-challenge/lics/scripts/env/robot.py')
text = path.read_text()
needle = "            elif front < 1.10 and linear > 0.0:\n                linear *= max(0.0, (front - 0.75) / 0.35)\n"
addition = needle + """            # The narrow frontal test can miss an obstacle at the edge of
            # the footprint while the policy is turning. Inspect the
            # commanded travel direction with a low-distance emergency
            # threshold; unlike the rejected wide shield this only arms when
            # a genuinely near obstacle is present.
            if abs(linear) > 0.15:
                corridor = self.laser[220:500] if linear > 0.0 else np.concatenate((self.laser[:140], self.laser[580:]))
                valid = corridor[np.isfinite(corridor) & (corridor > 0.05)]
                if valid.size and float(np.min(valid)) < 0.55:
                    left = float(np.mean(self.laser[440:620]))
                    right = float(np.mean(self.laser[100:280]))
                    linear = 0.0
                    angular = 0.8 * self.max_w if left >= right else -0.8 * self.max_w
"""
if text.count(needle) != 1:
    raise SystemExit('expected one LiCS velocity block')
path.write_text(text.replace(needle, addition))
PY
RUN grep -q 'commanded travel direction' /opt/barn_ws/src/the-barn-challenge/lics/scripts/env/robot.py

LABEL org.opencontainers.image.source="https://github.com/RetiefLouw/vrx-record-lab" \
      org.opencontainers.image.description="Pinned BARN LiCS-KI with stable readiness and directional emergency shield" \
      org.opencontainers.image.lics.commit="f7bd87cc232b04f6ce9edd10a6a05b84a6c7dfaa" \
      org.opencontainers.image.safety="directional-near-obstacle-v1"
