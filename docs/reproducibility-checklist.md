# Reproducibility checklist

- [x] Historical source revision is pinned and justified; exact competition image remains unverified.
- [ ] Official world, scorer, duration, trials, and aggregation are identified.
- [x] Clean `linux/amd64` container build succeeds; verified with `./scripts/bootstrap.sh --build-only` and the headless smoke test on 2026-09-03 under OrbStack.
- [ ] Public practice-world baseline completes headlessly with real scorer output.
- [ ] Repeated identical-seed runs satisfy the numerical tolerance. (The smoke test only checks seed injection and startup.)
- [ ] Published reference reproduction is documented.
- [ ] Development and hidden evaluation seeds are disjoint.
- [x] Benchmark and scorer trees are unchanged in this environment-plumbing change.
- [x] Bounded practice-world launch logs and the failed-check rosbag are retained.
- [ ] Raw completed results and SHA-256 manifests are retained.
- [ ] A clean-clone verifier reproduces the promoted aggregate.

## Verification commands

The repository checks are dependency-free:

```bash
python3 -m unittest discover -s tests -v
python3 -m verification.verify seeds --config verification/seed_sets.json
python3 -m verification.verify benchmark-tree --baseline-ref origin/main
python3 -m verification.verify results \
  --input verification/examples/result.json \
  --root verification/examples/artifacts \
  --seed-config verification/seed_sets.json \
  --manifest verification/examples/artifacts/SHA256SUMS.json
```

The committed seed file is a non-secret fixture. A real evaluation must use
the exact seed allocation used by the evaluator and must not claim hidden-seed
separation until that allocation has been independently checked.
