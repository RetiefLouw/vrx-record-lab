# VRX Record Lab

Reproducible archaeology, baseline replication, and controller development for
the VRX 2019 station-keeping task.

The first reference target is the University of Florida score reported as
`0.11` in the official 2019 results. This repository does **not** claim a new
record until the historical protocol has been reconstructed, the reference
has been reproduced as closely as surviving artifacts allow, and a better
result has passed a clean independent rerun.

## Campaign status

- Target: VRX 2019 station keeping
- Status: protocol reconstruction and environment bootstrap
- Compute policy: OrbStack first; Vast.ai only through a bounded campaign
- Claim policy: independently reproduced task-level record unless recognized
  by the benchmark maintainers

The historical `0.11` value is a reference point, not an accepted directly
comparable record. The public evidence does not currently pin the complete
evaluation inputs needed for direct comparison; see
[`docs/vrx-2019-protocol.md`](docs/vrx-2019-protocol.md).

## Independent verification

Verification code lives under [`verification/`](verification/) and does not
implement or alter VRX benchmark or scorer logic. It checks:

- exact clean-clone commits and optional rerun commands;
- protected benchmark/scorer tree equality against a baseline ref;
- strict result schema, aggregate arithmetic, provenance, and artifact links;
- disjoint development, independent-verification, and evaluation seed sets;
- deterministic SHA-256 artifact manifests.

The checked-in result and artifact files are illustrative and deliberately have
`claim_status: unaccepted`. They are not a performance claim.

Run the dependency-free checks from the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 -m verification.verify seeds
python3 -m verification.verify benchmark-tree --baseline-ref origin/main
python3 -m verification.verify results \
  --input verification/examples/result.json \
  --root verification/examples/artifacts \
  --seed-config verification/seed_sets.json \
  --manifest verification/examples/artifacts/SHA256SUMS.json
```

For a promoted run, first run the candidate commit from a clean clone and
record the output, then validate the resulting manifest and result document.
The `promoted` status is rejected unless the result states direct
comparability, all protocol evidence is verified, and clean-clone, protected
tree, and manifest checks are all recorded as successful.

## Sources

- [Official VRX 2019 results](https://github.com/osrf/vrx/wiki/vrx_2019-results)
- [VRX repository](https://github.com/osrf/vrx)

## License

Project-authored code is released under the Apache License 2.0. Upstream VRX,
ROS, Gazebo, vessel models, and competition assets retain their own licenses.
