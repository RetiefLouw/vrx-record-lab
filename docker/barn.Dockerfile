# syntax=docker/dockerfile:1.7

ARG BASE_IMAGE=osrf/ros:melodic-desktop-full-bionic@sha256:39b2900892a32886033f168e55fd8ce4e01d804ed1ffdde156639b3cf789ee71
FROM --platform=linux/amd64 ${BASE_IMAGE}

ARG BARN_REPOSITORY=https://github.com/Daffan/the-barn-challenge.git
ARG BARN_COMMIT=bf5a226f6088ec96bf0d2dbee3253a8ea6119b83
ARG JACKAL_REPOSITORY=https://github.com/jackal/jackal.git
ARG JACKAL_COMMIT=0d8d76f96bd52102b69a3b9cb735fd5f9e15f695
ARG JACKAL_SIMULATOR_REPOSITORY=https://github.com/jackal/jackal_simulator.git
ARG JACKAL_SIMULATOR_COMMIT=f72ffe1c160db5595dc033b323eb924abec539c4
ARG JACKAL_DESKTOP_REPOSITORY=https://github.com/jackal/jackal_desktop.git
ARG JACKAL_DESKTOP_COMMIT=5dbf81c6266c3810d37b3d966a22ec149fd28e99
ARG EBAND_REPOSITORY=https://github.com/utexas-bwi/eband_local_planner.git
ARG EBAND_COMMIT=eefda44382024d52d45bb93e6dcf7294ff0ef8ae

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    ROS_MASTER_URI=http://127.0.0.1:11311 \
    ROS_HOSTNAME=localhost \
    BARN_WORKSPACE=/opt/barn_ws \
    BARN_SOURCE_DIR=/opt/barn_ws/src/the-barn-challenge

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      git \
      build-essential \
      python3-venv \
      ros-melodic-amcl \
      ros-melodic-gmapping \
      ros-melodic-hector-gazebo-plugins \
      ros-melodic-lms1xx \
      ros-melodic-map-server \
      ros-melodic-move-base \
      ros-melodic-pointgrey-camera-description \
      ros-melodic-robot-localization \
      ros-melodic-sick-tim \
      ros-melodic-velodyne-description \
 && rm -rf /var/lib/apt/lists/*

COPY docker/barn-daffan-python2.patch /tmp/barn-daffan-python2.patch

RUN mkdir -p "${BARN_WORKSPACE}/src" \
 && for spec in \
      "${BARN_REPOSITORY} ${BARN_COMMIT} the-barn-challenge" \
      "${JACKAL_REPOSITORY} ${JACKAL_COMMIT} jackal" \
      "${JACKAL_SIMULATOR_REPOSITORY} ${JACKAL_SIMULATOR_COMMIT} jackal_simulator" \
      "${JACKAL_DESKTOP_REPOSITORY} ${JACKAL_DESKTOP_COMMIT} jackal_desktop" \
      "${EBAND_REPOSITORY} ${EBAND_COMMIT} eband_local_planner"; do \
      read -r repo commit name <<<"${spec}"; \
      git init "${BARN_WORKSPACE}/src/${name}"; \
      git -C "${BARN_WORKSPACE}/src/${name}" remote add origin "${repo}"; \
      git -C "${BARN_WORKSPACE}/src/${name}" fetch --depth 1 origin "${commit}"; \
      git -C "${BARN_WORKSPACE}/src/${name}" checkout --detach "${commit}"; \
      test "$(git -C "${BARN_WORKSPACE}/src/${name}" rev-parse HEAD)" = "${commit}"; \
    done \
 && git -C "${BARN_SOURCE_DIR}" apply /tmp/barn-daffan-python2.patch \
 && source /opt/ros/melodic/setup.bash \
 && cd "${BARN_WORKSPACE}" \
 && apt-get update \
 && rosdep update --include-eol-distros \
 && rosdep install -y --from-paths src --ignore-src --rosdistro melodic \
 && catkin_make -j2 \
 && rm -f /tmp/barn-daffan-python2.patch

COPY docker/barn-entrypoint.sh /usr/local/bin/barn-entrypoint
RUN chmod 0755 /usr/local/bin/barn-entrypoint

LABEL org.opencontainers.image.source="https://github.com/RetiefLouw/vrx-record-lab" \
      org.opencontainers.image.description="Pinned public BARN DWA evaluation environment" \
      org.opencontainers.image.barn.commit="${BARN_COMMIT}" \
      org.opencontainers.image.architecture="linux/amd64"

WORKDIR ${BARN_SOURCE_DIR}
ENTRYPOINT ["/usr/local/bin/barn-entrypoint"]
CMD ["--world_idx", "0"]
