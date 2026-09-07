# Candidate Q-21b: Q-21's reactive shield with a wider, earlier clearance
# threshold. Kept separate so Q-21 remains immutable and auditable.
FROM vrx-record-lab:barn-lics-safe

RUN sed -i \
      -e 's/self.laser\[300:420\]/self.laser[260:460]/' \
      -e 's/front < 0.75/front < 1.50/' \
      -e 's/self.laser\[420:600\]/self.laser[460:620]/' \
      -e 's/self.laser\[120:300\]/self.laser[100:260]/' \
      -e 's/front < 1.10/front < 2.00/' \
      -e 's/(front - 0.75) \/ 0.35/(front - 1.50) \/ 0.50/' \
      /opt/barn_ws/src/the-barn-challenge/lics/scripts/env/robot.py \
 && grep -q 'front < 1.50' /opt/barn_ws/src/the-barn-challenge/lics/scripts/env/robot.py

LABEL org.opencontainers.image.source="https://github.com/RetiefLouw/vrx-record-lab" \
      org.opencontainers.image.description="Pinned BARN LiCS-KI with stable readiness and wider reactive collision shield" \
      org.opencontainers.image.lics.commit="f7bd87cc232b04f6ce9edd10a6a05b84a6c7dfaa" \
      org.opencontainers.image.safety="front-clearance-shield-v2"
