# syntax=docker/dockerfile:1.7

FROM vrx-record-lab:barn-dwa

ARG LICS_REPOSITORY=https://github.com/damanikjosh/the-barn-challenge.git
ARG LICS_COMMIT=f7bd87cc232b04f6ce9edd10a6a05b84a6c7dfaa

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV LICS_COMMIT=${LICS_COMMIT} \
    PYTHONPATH=/opt/barn_ws/src/the-barn-challenge/lics/scripts

RUN cd / \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      python3-pip \
      python3-yaml \
      ros-melodic-global-planner \
 && rm -rf /var/lib/apt/lists/* \
 && rm -rf /opt/barn_ws/src/the-barn-challenge \
 && git init /opt/barn_ws/src/the-barn-challenge \
 && git -C /opt/barn_ws/src/the-barn-challenge remote add origin "${LICS_REPOSITORY}" \
 && git -C /opt/barn_ws/src/the-barn-challenge fetch --depth 1 origin "${LICS_COMMIT}" \
 && git -C /opt/barn_ws/src/the-barn-challenge checkout --detach "${LICS_COMMIT}" \
 && test "$(git -C /opt/barn_ws/src/the-barn-challenge rev-parse HEAD)" = "${LICS_COMMIT}" \
 && python3 -m pip install --no-cache-dir --upgrade 'pip<22' \
 && python3 -m pip install --no-cache-dir \
      'torch==1.10.2+cpu' \
      'numpy==1.19.5' \
      'scipy==1.5.4' \
      easydict \
      'setuptools==59.6.0' \
      'rospkg==1.5.0' \
      'catkin_pkg==0.4.23' \
      'netifaces==0.10.9' \
      --find-links https://download.pytorch.org/whl/torch_stable.html

# Ubuntu 18.04 ships PyYAML 3.x, which has no FullLoader symbol. The released
# LiCS loader only needs safe YAML parsing, so make that compatibility fix in
# the image while leaving the upstream source commit and model unchanged.
RUN sed -i 's/yaml.load(f, Loader=yaml.FullLoader)/yaml.safe_load(f)/' \
    /opt/barn_ws/src/the-barn-challenge/lics/scripts/utils.py

RUN test -f /opt/ros/melodic/setup.bash \
 && source /opt/ros/melodic/setup.bash \
 && cd /opt/barn_ws \
 && catkin_make -j2

COPY docker/barn-lics-entrypoint.sh /usr/local/bin/barn-lics-entrypoint
RUN chmod 0755 /usr/local/bin/barn-lics-entrypoint

LABEL org.opencontainers.image.source="https://github.com/RetiefLouw/vrx-record-lab" \
      org.opencontainers.image.description="Pinned public BARN LiCS-KI evaluation environment" \
      org.opencontainers.image.lics.commit="${LICS_COMMIT}" \
      org.opencontainers.image.architecture="linux/amd64"

WORKDIR /opt/barn_ws/src/the-barn-challenge
ENTRYPOINT ["/usr/local/bin/barn-lics-entrypoint"]
CMD ["--world_idx", "0"]
