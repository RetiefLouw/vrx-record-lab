# Verification commands

`verify.py` is a standard-library-only command line verifier. It checks
provenance and evidence around a benchmark; it does not contain benchmark or
scorer implementation.

## Commands

```bash
# Validate all known seed sets and their configured pairwise separation.
python3 -m verification.verify seeds --config verification/seed_sets.json

# Compare protected benchmark/scorer trees in two Git revisions.
python3 -m verification.verify benchmark-tree \
  --repo . --baseline-ref origin/main --target-ref HEAD

# Create a deterministic manifest. The output is excluded from its own input.
python3 -m verification.verify manifest \
  --root results/promoted/run-001/artifacts \
  --output results/promoted/run-001/artifacts/SHA256SUMS.json

# Validate a result, check its artifact bytes, and check the manifest.
python3 -m verification.verify results \
  --input results/promoted/run-001/result.json \
  --schema verification/result.schema.json \
  --root results/promoted/run-001/artifacts \
  --seed-config verification/seed_sets.json \
  --manifest results/promoted/run-001/artifacts/SHA256SUMS.json

# Clone the exact published commit and run a command in the clean checkout.
python3 -m verification.verify clean-clone \
  --repo https://github.com/RetiefLouw/vrx-record-lab.git \
  --ref codex/independent-verification \
  --commit <40-character-commit-sha> \
  --run-command 'python3 -m unittest discover -s tests'
```

`result.schema.json` requires full commit SHAs, an image digest, configuration
hash, run-level scores and artifact references. The verifier additionally
checks mean arithmetic, unique run IDs and seeds, exact seed-set membership,
artifact bytes, and the conditions needed for `claim_status: promoted`.

The protected-tree config intentionally permits missing paths in this
documentation-only repository. A report with `vacuous: true` is a warning: it
must be replaced with the actual evaluator benchmark/scorer roots before a
record claim.
