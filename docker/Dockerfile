# syntax=docker/dockerfile:1.7

ARG BASE_IMAGE=osrf/ros:melodic-desktop-full-bionic@sha256:39b2900892a32886033f168e55fd8ce4e01d804ed1ffdde156639b3cf789ee71
FROM --platform=linux/amd64 ${BASE_IMAGE}

ARG VRX_REPOSITORY=https://github.com/osrf/vrx.git
ARG VRX_COMMIT=a62df11109ee95c206111c37a37c60d39bc7b705
ARG GAZEBO_VERSION=9.19.0-1~bionic
ARG IGNITION_COMMON_VERSION=1.1.1-1~bionic
ARG IGNITION_FUEL_TOOLS_VERSION=1.2.0-1~bionic
ARG SDFORMAT_VERSION=6.3.1-1~bionic
ARG VRX_USER=vrx
ARG VRX_UID=1000
ARG VRX_GID=1000

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    VRX_SOURCE_DIR=/opt/vrx_ws/src/vrx \
    VRX_WORKSPACE=/opt/vrx_ws

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# This is the OSRF repository key carried by the official VRX 2019 Docker
# tree. Keeping the public key in the repository avoids trusting a key fetched
# during the build.
COPY docker/keys/gazebo.key /tmp/gazebo.key

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      gnupg \
      git \
      mercurial \
      build-essential \
      cmake \
      pkg-config \
      ruby \
      libeigen3-dev \
      libprotobuf-dev \
      protobuf-compiler \
      python3-numpy \
      python3-netifaces \
      python3-pip \
      python3-setuptools \
      python3-yaml \
      qtbase5-dev \
      libgles2-mesa-dev \
 && apt-key add /tmp/gazebo.key \
 && echo "deb http://packages.osrfoundation.org/gazebo/ubuntu-stable bionic main" > /etc/apt/sources.list.d/gazebo-stable.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      gazebo9="${GAZEBO_VERSION}" \
      gazebo9-common="${GAZEBO_VERSION}" \
      gazebo9-plugin-base="${GAZEBO_VERSION}" \
      libgazebo9="${GAZEBO_VERSION}" \
      libgazebo9-dev="${GAZEBO_VERSION}" \
      libignition-common="${IGNITION_COMMON_VERSION}" \
      libignition-fuel-tools1-1="${IGNITION_FUEL_TOOLS_VERSION}" \
      libsdformat6="${SDFORMAT_VERSION}" \
      libsdformat6-dev="${SDFORMAT_VERSION}" \
      sdformat-sdf="${SDFORMAT_VERSION}" \
      ros-melodic-gazebo-ros \
      ros-melodic-gazebo-plugins \
      ros-melodic-geographic-msgs \
      ros-melodic-hector-gazebo-plugins \
      ros-melodic-joy \
      ros-melodic-joy-teleop \
      ros-melodic-key-teleop \
      ros-melodic-robot-localization \
      ros-melodic-robot-state-publisher \
      ros-melodic-rviz \
      ros-melodic-teleop-tools \
      ros-melodic-teleop-twist-keyboard \
      ros-melodic-velodyne-simulator \
      ros-melodic-xacro \
 && apt-mark hold gazebo9 gazebo9-common gazebo9-plugin-base libgazebo9 libgazebo9-dev libignition-common libignition-fuel-tools1-1 libsdformat6 libsdformat6-dev sdformat-sdf \
 && rm -f /tmp/gazebo.key \
 && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir \
      "catkin_pkg==0.5.2" \
      "dataclasses==0.8" \
      "defusedxml==0.7.1" \
      "empy==3.3.4" \
      "rospkg==1.5.0"

RUN groupadd --gid "${VRX_GID}" "${VRX_USER}" \
 && useradd --uid "${VRX_UID}" --gid "${VRX_GID}" --create-home --shell /bin/bash "${VRX_USER}"

RUN mkdir -p "${VRX_WORKSPACE}/src" \
 && git init "${VRX_SOURCE_DIR}" \
 && git -C "${VRX_SOURCE_DIR}" remote add origin "${VRX_REPOSITORY}" \
 && git -C "${VRX_SOURCE_DIR}" fetch --depth 1 origin "${VRX_COMMIT}" \
 && git -C "${VRX_SOURCE_DIR}" checkout --detach "${VRX_COMMIT}" \
 && test "$(git -C "${VRX_SOURCE_DIR}" rev-parse HEAD)" = "${VRX_COMMIT}"

RUN source /opt/ros/melodic/setup.bash \
 && cd "${VRX_WORKSPACE}" \
 && catkin_make -DCMAKE_BUILD_TYPE=Release

COPY ros/vrx_controller_ros "${VRX_WORKSPACE}/src/vrx_controller_ros"
COPY src/vrx_controller /opt/vrx_controller/src/vrx_controller
RUN chmod 0755 "${VRX_WORKSPACE}/src/vrx_controller_ros/scripts/"*.py \
 && source /opt/ros/melodic/setup.bash \
 && cd "${VRX_WORKSPACE}" \
 && catkin_make -DCMAKE_BUILD_TYPE=Release

COPY docker/entrypoint.sh /usr/local/bin/vrx-entrypoint
COPY docker/run-stationkeeping.sh /usr/local/bin/vrx-run-stationkeeping
COPY docker/run-trial.sh /usr/local/bin/vrx-run-trial
ENV PYTHONPATH=/opt/vrx_controller/src
RUN chmod 0755 /usr/local/bin/vrx-entrypoint /usr/local/bin/vrx-run-stationkeeping /usr/local/bin/vrx-run-trial \
 && chown -R "${VRX_USER}:${VRX_USER}" /home/"${VRX_USER}" "${VRX_WORKSPACE}"

LABEL org.opencontainers.image.source="https://github.com/RetiefLouw/vrx-record-lab" \
      org.opencontainers.image.description="Pinned VRX 2019 station-keeping environment" \
      org.opencontainers.image.vrx.commit="${VRX_COMMIT}" \
      org.opencontainers.image.gazebo.version="${GAZEBO_VERSION}" \
      org.opencontainers.image.architecture="linux/amd64"

USER ${VRX_USER}:${VRX_USER}
WORKDIR /home/${VRX_USER}

ENTRYPOINT ["/usr/local/bin/vrx-entrypoint"]
CMD ["run"]
