# VRX 2019 environment reproduction

This directory builds a pinned `linux/amd64` container for the historical VRX
2019 station-keeping example. It is intended for OrbStack on Apple Silicon;
the `platform` field deliberately requests x86_64 emulation. The container is
headless by default so it does not require X11 forwarding or a host GPU.

## Reproduction pins

| Component | Pin | Status |
|---|---|---|
| Container architecture | `linux/amd64` | Explicit target for all builds and runs |
| Base image | `osrf/ros:melodic-desktop-full-bionic@sha256:39b2900892a32886033f168e55fd8ce4e01d804ed1ffdde156639b3cf789ee71` | Official OSRF image digest resolved on 2026-09-03; its config is amd64/Bionic |
| ROS | Melodic | Historical VRX 2019 system requirement |
| Ubuntu | 18.04 Bionic | Historical VRX 2019 system requirement |
| Gazebo | `9.19.0-1~bionic` | Explicit OSRF Bionic package; see the inference below |
| Gazebo support libraries | Ignition Common `1.1.1-1~bionic`, Ignition Fuel Tools `1.2.0-1~bionic`, SDFormat `6.3.1-1~bionic` | Explicit OSRF Bionic packages selected to match the pinned Gazebo ABI |
| VRX source | `a62df11109ee95c206111c37a37c60d39bc7b705` | Last public upstream commit observed before the 2019-11-22 submission deadline |
| VRX source URL | `https://github.com/osrf/vrx.git` | Official upstream repository |

The historical system requirements say “Gazebo 9.11.0+”. The official Bionic
OSRF repository no longer exposes a Bionic 9.11 package, while it does expose
`9.19.0-1~bionic`; the Dockerfile pins that exact package rather than taking
the base image's Gazebo 9.0.0. This is a documented availability inference,
not a claim that 9.19 was the exact competition binary. The 9.11 Disco
packages are not silently installed on Bionic.

The resolved ROS desktop image also contains older Ubuntu builds of several
Gazebo support libraries. A runtime loader check showed that Gazebo 9.19
could not start with Ignition Fuel Tools 1.0.0 or SDFormat 6.0.0, so the
Dockerfile pins the matching OSRF Bionic builds above. This is an operational
ABI-compatibility inference from the public package metadata and the local
startup failure, not a claim about the competition's exact support-library
versions.

The selected VRX commit is also an inference. It is timestamped 2019-11-22
17:23 UTC (09:23 PST), after the task document v1.4 date and before the phase-3
submission deadline. The private evaluation image, hidden worlds, and exact
apt snapshot used for the competition are not available in the public record.
No source under this repository changes the upstream benchmark or scorer.

## Bootstrap

From the repository root:

```bash
./scripts/bootstrap.sh
```

The first build is large because the official desktop-full image contains the
ROS/Gazebo desktop stack. Subsequent builds use the local image cache. The
script validates Compose configuration, builds the image, starts the
headless station-keeping launch, and waits for the `/vrx/task/info` health
check.

Useful commands:

```bash
./scripts/bootstrap.sh --build-only
docker compose --env-file config/vrx-2019.env -f compose.yaml logs -f simulator
docker compose --env-file config/vrx-2019.env -f compose.yaml exec simulator bash
./scripts/bootstrap.sh --down
```

Run the smoke test after the image is available:

```bash
./scripts/smoke-test.sh
```

It checks the architecture-constrained image, ROS distribution, Gazebo
version, exact VRX source commit, station-keeping launch/world presence, task
status, and the configured wind seed. It stops the container on exit and
writes diagnostic output under `artifacts/smoke-test/`; those files are
intentionally ignored by Git.

## Seeds and historical behavior

The pinned 2019 wind plugin accepts a `random_seed` field through the
`usv_wind_gazebo` xacro macro. The published station-keeping world leaves that
field empty, which makes the plugin seed from `std::random_device`. The
committed config sets `VRX_WIND_SEED=2019` solely to make local smoke runs
repeatable. That number is an arbitrary reproducibility input, not a recovered
competition seed.

When `VRX_WIND_SEED` is non-empty and non-zero, the entrypoint creates a
temporary copy of the upstream station-keeping xacro, injects only that
supported seed argument, expands it, and passes the generated world to the
unchanged upstream launch file. When the value is empty or `0`, it passes the
upstream generated world without a seed override. The repository does not
claim deterministic wave, physics, scheduler, or hidden-world behavior where
the historical code does not expose a seed.

To run the unmodified public example behavior:

```bash
VRX_WIND_SEED= docker compose --env-file config/vrx-2019.env -f compose.yaml up --detach --wait simulator
```

Do not compare the seeded local example score to the published `0.11` as a
record reproduction. The public results page reports six trials, while the
competition's hidden configurations and evaluation image are not in this
repository.

## Scope and validation limits

This project adds a legacy-ROS practice adapter for the closest UF MRAC
public-source port. The fetched upstream tree is still built at the pinned
commit; no benchmark, task, or scorer source is copied into or modified in
this project. The adapter's ground-truth state, stationary goal, and
co-located mapper are explicitly practice-only deviations; see
[`docs/uf-mrac-port.md`](uf-mrac-port.md).

The smoke test is intentionally a startup test: it does not wait through the
full 300-second station-keeping running state or assert a score. A clean
baseline reproduction still requires an independent controller, the original
trial selection/aggregation protocol, raw outputs, and a verified historical
runtime snapshot.

Primary historical references:

- [VRX 2019 system requirements](https://github.com/osrf/vrx/wiki/vrx_2019-system_requirements)
- [VRX 2019 task tutorials](https://github.com/osrf/vrx/wiki/vrx_2019-task_tutorials)
- [VRX 2019 phase-3 instructions](https://github.com/osrf/vrx/wiki/vrx_2019-phase3_competition)
- [VRX 2019 results](https://github.com/osrf/vrx/wiki/vrx_2019-results)
- [Pinned VRX source commit](https://github.com/osrf/vrx/commit/a62df11109ee95c206111c37a37c60d39bc7b705)
