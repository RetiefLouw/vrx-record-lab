"""Deterministic adapter fixture; this is not a VRX benchmark scorer."""

import json
import os
from pathlib import Path


seed = int(os.environ["VRX_TRIAL_SEED"])
output = Path(os.environ["VRX_TRIAL_OUTPUT"])
artifact_dir = Path(os.environ["VRX_TRIAL_ARTIFACT_DIR"])
artifact_dir.mkdir(parents=True, exist_ok=True)
(artifact_dir / "state.json").write_text(json.dumps({"seed": seed}, sort_keys=True) + "\n", encoding="utf-8")
output.write_text(
    json.dumps(
        {
            "completed": True,
            "score": seed / 10.0,
            "score_components": {"fixture_score": seed / 10.0},
            "real_time_factor": 1.0,
            "environment": {"fixture": True},
            "metrics": {"steps": seed},
        },
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
print("fixture adapter completed")
