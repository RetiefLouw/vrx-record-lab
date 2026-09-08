# LoRR replay visualisations

These two MP4 files are offline, data-derived explainer animations for the
LoRR 2024 Test Round results:

- `lorr-q35-pinned-clean-beat.mp4` — current clean local best, Q-35: 1,325
  tasks, +139 over the archive reference of 1,186, and zero planner,
  schedule, or entry-timeout errors under `OMP_NUM_THREADS=1` and Docker CPU
  pinning.
- `lorr-q31-previous-clean-beat.mp4` — previous clean local beat, Q-31: 1,318
  tasks, +132 over the same archive reference, and zero planner, schedule, or
  entry-timeout errors.

The repository does not retain raw LoRR simulator video or per-agent
trajectory traces. The clips animate verified ledger values and use a clearly
labelled schematic fleet view; they are **illustrative replay visualisations,
not raw simulator footage** and do not establish an official leaderboard
change.

Source ledgers:

- [`Q-35`](../../../results/lorr-q35-test-round-random100-team-rapid-cpuset1.json)
- [`Q-31`](../../../results/lorr-q31-test-round-random100-team-rapid.json)

Generated with `scripts/create_lorr_replay_videos.py` using PIL and ffmpeg.
Both files are H.264 MP4, 1280×720, 24 fps, 12 seconds, and use `yuv420p`
for offline browser compatibility. Poster PNGs are provided beside each
video for stable page loading.
