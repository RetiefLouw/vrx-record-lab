"""Strict aggregation helpers for the reconstructed VRX 2019 protocol.

The public 2019 station-keeping result reports six trial scores and defines
the task score as their arithmetic mean.  The generic result harness in
``stats.py`` intentionally supports partial engineering runs, so it is not a
safe comparator for a historical six-trial claim.  This module is the strict
boundary: it refuses a missing, failed, duplicated, or non-finite trial rather
than silently averaging the trials that happened to finish.

The public record does not expose the phase-3 seeds or the unrounded scores.
Consequently this code validates the required *number* of complete runs, but
does not invent seed values or claim that a public phase-2 run is phase-3
comparable.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections.abc import Iterable, Mapping, Sequence
from numbers import Real
from pathlib import Path
from typing import Any

from .jsonio import load_json, write_json


class AggregationProtocolError(ValueError):
    """The supplied scores or result do not satisfy the 2019 protocol."""


VRX2019_PROTOCOL_ID = "vrx-2019-station-keeping"
VRX2019_TRIAL_COUNT = 6
VRX2019_SCORE_DIRECTION = "minimize"

# These are the six values displayed by the official 2019 results page.  They
# are retained at display precision; the underlying unrounded values are not
# public, so this is an arithmetic/provenance check, not a byte-level replay.
VRX2019_UF_PUBLISHED_RUN_SCORES = (0.02, 0.04, 0.35, 0.04, 0.10, 0.11)
VRX2019_UF_PUBLISHED_TASK_SCORE = 0.11


def _validate_expected_count(expected_count: int | None) -> None:
    if expected_count is not None and (
        isinstance(expected_count, bool)
        or not isinstance(expected_count, int)
        or expected_count <= 0
    ):
        raise AggregationProtocolError("expected_count must be a positive integer or None")


def validate_run_scores(
    scores: Iterable[Real], *, expected_count: int | None = VRX2019_TRIAL_COUNT
) -> tuple[float, ...]:
    """Return finite scores after enforcing the declared run count.

    ``expected_count=None`` is available for generic mean calculations, but
    callers comparing with the reconstructed VRX 2019 result should retain the
    default of six.  Booleans are rejected even though Python considers them
    integers; accepting one would turn a malformed status field into a score.
    """

    _validate_expected_count(expected_count)
    if isinstance(scores, (str, bytes)):
        raise AggregationProtocolError("scores must be an iterable of numbers")
    try:
        values = tuple(scores)
    except TypeError as exc:
        raise AggregationProtocolError("scores must be an iterable of numbers") from exc
    if expected_count is not None and len(values) != expected_count:
        raise AggregationProtocolError(
            f"VRX 2019 station keeping requires exactly {expected_count} run scores; got {len(values)}"
        )
    if not values:
        raise AggregationProtocolError("at least one run score is required")
    converted: list[float] = []
    for index, score in enumerate(values):
        if isinstance(score, bool) or not isinstance(score, Real):
            raise AggregationProtocolError(f"run score {index} must be a finite number")
        numeric = float(score)
        if not math.isfinite(numeric):
            raise AggregationProtocolError(f"run score {index} must be a finite number")
        converted.append(numeric)
    return tuple(converted)


def aggregate_vrx2019_runs(scores: Iterable[Real]) -> dict[str, Any]:
    """Aggregate six complete 2019 station-keeping runs.

    The returned ``task_score`` is deliberately not rounded.  The official
    values were printed to two decimal places; preserving the input precision
    avoids implying access to the hidden unrounded values.
    """

    values = validate_run_scores(scores)
    task_score = math.fsum(values) / len(values)
    return {
        "protocol_id": VRX2019_PROTOCOL_ID,
        "score_direction": VRX2019_SCORE_DIRECTION,
        "method": "arithmetic_mean",
        "trial_count": len(values),
        "n": len(values),
        "run_scores": list(values),
        "sum": math.fsum(values),
        "task_score": task_score,
        # ``mean`` mirrors the canonical result aggregate terminology while
        # ``task_score`` keeps the 2019 leaderboard meaning explicit.
        "mean": task_score,
        "complete": True,
    }


def _canonical_identity(result: Mapping[str, Any]) -> dict[str, Any]:
    """Extract identity fields used by a conservative result comparison."""

    benchmark = result.get("benchmark")
    scorer = benchmark.get("scorer") if isinstance(benchmark, Mapping) else None
    task = result.get("task")
    return {
        "benchmark_name": benchmark.get("name") if isinstance(benchmark, Mapping) else None,
        "benchmark_revision": benchmark.get("revision") if isinstance(benchmark, Mapping) else None,
        "protocol_revision": benchmark.get("protocol_revision") if isinstance(benchmark, Mapping) else None,
        "scorer_name": scorer.get("name") if isinstance(scorer, Mapping) else None,
        "scorer_revision": scorer.get("revision") if isinstance(scorer, Mapping) else None,
        "task_name": task.get("name") if isinstance(task, Mapping) else None,
    }


def aggregate_vrx2019_result(
    result: Mapping[str, Any], *, expected_seeds: Sequence[int] | None = None
) -> dict[str, Any]:
    """Strictly aggregate a canonical result document's six trial records.

    A trial counts only when it explicitly has ``completed=true``,
    ``status=completed``, and a finite numeric score.  The check also rejects
    duplicate trial IDs/seeds.  If ``expected_seeds`` is supplied, its order
    must match the result's seed order; this is useful for the public phase-2
    suite, while phase-3 seed values remain unavailable and must be omitted.
    """

    if not isinstance(result, Mapping):
        raise AggregationProtocolError("result must be an object")
    if result.get("status") not in (None, "completed"):
        raise AggregationProtocolError("a strict 2019 aggregate requires result.status=completed")
    benchmark = result.get("benchmark")
    if isinstance(benchmark, Mapping) and benchmark.get("score_direction") not in (None, "minimize"):
        raise AggregationProtocolError("VRX 2019 station keeping is lower-is-better; score_direction must be minimize")
    trials = result.get("trials")
    if not isinstance(trials, list):
        raise AggregationProtocolError("result.trials must be a list")
    if len(trials) != VRX2019_TRIAL_COUNT:
        raise AggregationProtocolError(
            f"VRX 2019 station keeping requires exactly {VRX2019_TRIAL_COUNT} trial records; got {len(trials)}"
        )

    trial_ids: list[str] = []
    seeds: list[int] = []
    scores: list[float] = []
    for index, trial in enumerate(trials):
        if not isinstance(trial, Mapping):
            raise AggregationProtocolError(f"result.trials[{index}] must be an object")
        trial_id = trial.get("trial_id")
        if not isinstance(trial_id, str) or not trial_id:
            raise AggregationProtocolError(f"result.trials[{index}].trial_id must be a non-empty string")
        if trial_id in trial_ids:
            raise AggregationProtocolError(f"duplicate trial_id {trial_id!r}")
        trial_ids.append(trial_id)
        seed = trial.get("seed")
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise AggregationProtocolError(f"result.trials[{index}].seed must be an integer")
        if seed in seeds:
            raise AggregationProtocolError(f"duplicate trial seed {seed}")
        seeds.append(seed)
        if trial.get("completed") is not True or trial.get("status") != "completed":
            raise AggregationProtocolError(
                f"result.trials[{index}] is not complete; failed, timeout, and invalid trials cannot be omitted"
            )
        score_values = validate_run_scores([trial.get("score")], expected_count=1)
        scores.append(score_values[0])

    if expected_seeds is not None:
        if isinstance(expected_seeds, (str, bytes)):
            raise AggregationProtocolError("expected_seeds must be a sequence of integers")
        expected = tuple(expected_seeds)
        if len(expected) != VRX2019_TRIAL_COUNT or any(
            isinstance(seed, bool) or not isinstance(seed, int) for seed in expected
        ):
            raise AggregationProtocolError("expected_seeds must contain exactly six integer seeds")
        if tuple(seeds) != expected:
            raise AggregationProtocolError(f"trial seeds {seeds!r} do not match expected seeds {list(expected)!r}")

    summary = aggregate_vrx2019_runs(scores)
    summary.update(
        {
            "result_id": result.get("result_id"),
            "trial_ids": trial_ids,
            "seeds": seeds,
            "identity": _canonical_identity(result),
        }
    )
    return summary


def compare_vrx2019_results(
    candidate: Mapping[str, Any], reference: Mapping[str, Any], *, require_identity: bool = True
) -> dict[str, Any]:
    """Compare two complete six-trial canonical results conservatively.

    ``comparable`` is false when the evaluator identity differs.  This is
    important here: public phase-2 worlds and the unrecovered private phase-3
    worlds are not interchangeable simply because both have six runs.  Set
    ``require_identity=False`` only for an explicitly declared conditional
    comparison; the result still reports the identity mismatches.
    """

    candidate_summary = aggregate_vrx2019_result(candidate)
    reference_summary = aggregate_vrx2019_result(reference)
    candidate_identity = candidate_summary["identity"]
    reference_identity = reference_summary["identity"]
    mismatches = []
    for field in candidate_identity:
        candidate_value = candidate_identity[field]
        reference_value = reference_identity[field]
        if candidate_value != reference_value or (
            require_identity and (not isinstance(candidate_value, str) or not candidate_value)
        ):
            mismatches.append(field)
    comparable = not mismatches if require_identity else True
    return {
        "protocol_id": VRX2019_PROTOCOL_ID,
        "comparable": comparable,
        "comparison_status": "direct" if comparable else "not_comparable",
        "identity_mismatches": mismatches,
        "candidate": {
            "task_score": candidate_summary["task_score"],
            "run_scores": candidate_summary["run_scores"],
            "result_id": candidate_summary.get("result_id"),
        },
        "reference": {
            "task_score": reference_summary["task_score"],
            "run_scores": reference_summary["run_scores"],
            "result_id": reference_summary.get("result_id"),
        },
        "delta_candidate_minus_reference": candidate_summary["task_score"] - reference_summary["task_score"],
    }


def compare_vrx2019_run_vectors(
    candidate_scores: Iterable[Real], reference_scores: Iterable[Real]
) -> dict[str, Any]:
    """Compare two six-run vectors while labelling the result arithmetic-only.

    This helper is appropriate for checking the displayed UF vector, but raw
    vectors carry no evaluator identity.  It therefore never reports a direct
    benchmark comparison; use :func:`compare_vrx2019_results` when canonical
    result metadata is available.
    """

    candidate = aggregate_vrx2019_runs(candidate_scores)
    reference = aggregate_vrx2019_runs(reference_scores)
    return {
        "protocol_id": VRX2019_PROTOCOL_ID,
        "comparison_status": "arithmetic_only",
        "comparable": False,
        "candidate": {"run_scores": candidate["run_scores"], "task_score": candidate["task_score"]},
        "reference": {"run_scores": reference["run_scores"], "task_score": reference["task_score"]},
        "delta_candidate_minus_reference": candidate["task_score"] - reference["task_score"],
    }


def _is_dnf_or_dsq(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.upper() in {"DNF", "DSQ"})


def rank_vrx2019_task_scores(team_scores: Mapping[str, Real | None | str]) -> dict[str, int]:
    """Rank teams on one lower-is-better task, including DNF/DSQ handling.

    The recovered rule assigns a DNF/DSQ the rank equal to the number of
    teams.  Ties use competition ranking (equal scores share the same rank;
    the next rank skips accordingly), which is made explicit because the
    public record does not publish a tie example or tie-break rule.
    """

    if not isinstance(team_scores, Mapping) or not team_scores:
        raise AggregationProtocolError("team_scores must be a non-empty object")
    team_count = len(team_scores)
    valid: list[tuple[float, str]] = []
    for team, score in team_scores.items():
        if not isinstance(team, str) or not team:
            raise AggregationProtocolError("team names must be non-empty strings")
        if _is_dnf_or_dsq(score):
            continue
        if isinstance(score, bool) or not isinstance(score, Real) or not math.isfinite(float(score)):
            raise AggregationProtocolError(f"{team!r} score must be finite or null for DNF/DSQ")
        valid.append((float(score), team))
    valid.sort(key=lambda item: (item[0], item[1]))
    ranks: dict[str, int] = {}
    previous_score: float | None = None
    previous_rank = 0
    for position, (score, team) in enumerate(valid, start=1):
        if previous_score is not None and score == previous_score:
            rank = previous_rank
        else:
            rank = position
        ranks[team] = rank
        previous_score, previous_rank = score, rank
    for team, score in team_scores.items():
        if _is_dnf_or_dsq(score):
            ranks[team] = team_count
    return ranks


def aggregate_vrx2019_leaderboard(
    task_scores: Mapping[str, Mapping[str, Real | None | str]],
    *,
    task_order: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Aggregate task ranks and overall totals for the recovered rule.

    ``task_scores`` maps each team to one already-aggregated score per task.
    Missing task values are treated as DNF/DSQ (rank equal to the number of
    teams), making the missingness explicit in the returned ``task_scores``.
    Overall totals are the sum of task ranks; the lower total ranks first.
    """

    if not isinstance(task_scores, Mapping) or not task_scores:
        raise AggregationProtocolError("task_scores must be a non-empty team object")
    teams = tuple(task_scores)
    if any(not isinstance(team, str) or not team for team in teams):
        raise AggregationProtocolError("team names must be non-empty strings")
    if any(not isinstance(values, Mapping) for values in task_scores.values()):
        raise AggregationProtocolError("each team must map task names to scores")
    discovered = {task for values in task_scores.values() for task in values}
    if task_order is None:
        tasks = tuple(sorted(discovered))
    else:
        if isinstance(task_order, (str, bytes)):
            raise AggregationProtocolError("task_order must be a sequence of task names")
        tasks = tuple(task_order)
        if not tasks or any(not isinstance(task, str) or not task for task in tasks):
            raise AggregationProtocolError("task_order must contain non-empty task names")
        if len(set(tasks)) != len(tasks):
            raise AggregationProtocolError("task_order must not contain duplicate task names")
        unknown = discovered - set(tasks)
        if unknown:
            raise AggregationProtocolError(f"task_order omits task names: {sorted(unknown)!r}")
    if not tasks:
        raise AggregationProtocolError("at least one task is required")

    normalized_scores: dict[str, dict[str, Any]] = {
        team: {task: task_scores[team].get(task) for task in tasks} for team in teams
    }
    task_ranks = {
        task: rank_vrx2019_task_scores({team: normalized_scores[team][task] for team in teams})
        for task in tasks
    }
    overall_totals = {
        team: sum(task_ranks[task][team] for task in tasks) for team in teams
    }
    overall_ranks = rank_vrx2019_task_scores(overall_totals)
    return {
        "protocol_id": VRX2019_PROTOCOL_ID,
        "score_direction": VRX2019_SCORE_DIRECTION,
        "tasks": list(tasks),
        "task_scores": normalized_scores,
        "task_ranks": task_ranks,
        "overall_totals": overall_totals,
        "overall_ranks": overall_ranks,
    }


def _parse_score(value: str) -> float:
    try:
        score = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid score {value!r}") from exc
    if not math.isfinite(score):
        raise argparse.ArgumentTypeError(f"score must be finite: {value!r}")
    return score


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scores", nargs="*", type=_parse_score, help="six complete run scores")
    parser.add_argument("--result", type=Path, help="canonical six-trial result.json to aggregate")
    parser.add_argument(
        "--reference",
        type=Path,
        help="canonical six-trial result.json for an identity-aware comparison",
    )
    parser.add_argument("--output", type=Path, help="optional JSON output path")
    args = parser.parse_args(argv)
    try:
        if args.reference is not None and args.result is None:
            raise AggregationProtocolError("--reference requires --result")
        if args.result is not None and args.scores:
            raise AggregationProtocolError("provide either positional scores or --result, not both")
        if args.result is not None:
            result = load_json(args.result)
            if args.reference is not None:
                summary = compare_vrx2019_results(result, load_json(args.reference))
                summary["source"] = {
                    "kind": "canonical_result_comparison",
                    "candidate": str(args.result),
                    "reference": str(args.reference),
                }
            else:
                summary = aggregate_vrx2019_result(result)
                summary["source"] = {"kind": "canonical_result", "path": str(args.result)}
        elif args.scores:
            if args.reference is not None:
                raise AggregationProtocolError("--reference cannot be used with positional scores")
            summary = aggregate_vrx2019_runs(args.scores)
            summary["source"] = {"kind": "run_scores"}
        else:
            raise AggregationProtocolError("provide six scores or --result")
        if args.output is not None:
            write_json(args.output, summary)
        print(json.dumps(summary, indent=2, sort_keys=True))
    except (AggregationProtocolError, OSError, ValueError) as exc:
        print(f"aggregate_2019: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
