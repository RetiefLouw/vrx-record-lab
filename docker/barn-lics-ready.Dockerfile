# syntax=docker/dockerfile:1.7

FROM vrx-record-lab:barn-lics

COPY docker/barn-lics-readiness.patch /tmp/barn-lics-readiness.patch

RUN git -C /opt/barn_ws/src/the-barn-challenge apply /tmp/barn-lics-readiness.patch \
 && rm -f /tmp/barn-lics-readiness.patch

LABEL org.opencontainers.image.source="https://github.com/RetiefLouw/vrx-record-lab" \
      org.opencontainers.image.description="LiCS-KI with preregistered planner-readiness guard" \
      org.opencontainers.image.lics.readiness="zero-command until local goal is valid" \
      org.opencontainers.image.architecture="linux/amd64"

WORKDIR /opt/barn_ws/src/the-barn-challenge
ENTRYPOINT ["/usr/local/bin/barn-lics-entrypoint"]
CMD ["--world_idx", "0"]
