# Candidate Q-21 image: published LiCS-KI + stable planner readiness +
# bounded laser collision shield. The learned model and evaluator remain
# unchanged; only the command safety boundary is modified.
FROM vrx-record-lab:barn-lics-ready

COPY docker/barn-lics-safety.patch /tmp/barn-lics-safety.patch
RUN cd /opt/barn_ws/src/the-barn-challenge \
 && git apply --whitespace=error /tmp/barn-lics-safety.patch \
 && rm /tmp/barn-lics-safety.patch \
 && test -f lics/scripts/env/robot.py

LABEL org.opencontainers.image.source="https://github.com/RetiefLouw/vrx-record-lab" \
      org.opencontainers.image.description="Pinned BARN LiCS-KI with stable readiness and reactive collision shield" \
      org.opencontainers.image.lics.commit="f7bd87cc232b04f6ce9edd10a6a05b84a6c7dfaa" \
      org.opencontainers.image.safety="front-clearance-shield-v1"
