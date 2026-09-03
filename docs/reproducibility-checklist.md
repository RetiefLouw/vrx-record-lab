# Reproducibility checklist

- [ ] Historical source revisions are pinned and justified.
- [ ] Official world, scorer, duration, trials, and aggregation are identified.
- [ ] Clean `linux/amd64` container build succeeds.
- [ ] Upstream baseline completes headlessly.
- [ ] Repeated identical-seed runs satisfy the numerical tolerance.
- [ ] Published reference reproduction is documented.
- [ ] Development and hidden evaluation seeds are disjoint.
- [ ] Benchmark and scorer trees are unchanged for promoted runs.
- [ ] Raw results and SHA-256 manifests are retained.
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
