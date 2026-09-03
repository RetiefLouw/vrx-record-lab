# Reproducibility checklist

- [x] Historical source revision is pinned and justified; exact competition image remains unverified.
- [ ] Official world, scorer, duration, trials, and aggregation are identified.
- [x] Clean `linux/amd64` container build succeeds; verified with `./scripts/bootstrap.sh --build-only` and the headless smoke test on 2026-09-03 under OrbStack.
- [ ] Upstream baseline completes headlessly.
- [ ] Repeated identical-seed runs satisfy the numerical tolerance. (The smoke test only checks seed injection and startup.)
- [ ] Published reference reproduction is documented.
- [ ] Development and hidden evaluation seeds are disjoint.
- [x] Benchmark and scorer trees are unchanged in this environment-plumbing change.
- [ ] Raw results and SHA-256 manifests are retained.
- [ ] A clean-clone verifier reproduces the promoted aggregate.
