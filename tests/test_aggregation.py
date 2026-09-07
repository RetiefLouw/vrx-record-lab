import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from vrx_record_lab.aggregation import (  # noqa: E402
    AggregationProtocolError,
    VRX2019_UF_PUBLISHED_RUN_SCORES,
    aggregate_vrx2019_result,
    aggregate_vrx2019_leaderboard,
    aggregate_vrx2019_runs,
    compare_vrx2019_results,
    compare_vrx2019_run_vectors,
    rank_vrx2019_task_scores,
)


REPO = Path(__file__).parents[1]


class AggregationTests(unittest.TestCase):
    def test_published_six_run_vector_reproduces_displayed_task_score(self):
        summary = aggregate_vrx2019_runs(VRX2019_UF_PUBLISHED_RUN_SCORES)
        self.assertEqual(summary["trial_count"], 6)
        self.assertEqual(summary["sum"], 0.66)
        self.assertAlmostEqual(summary["task_score"], 0.11)
        self.assertEqual(summary["method"], "arithmetic_mean")

    def test_wrong_count_and_nonfinite_values_are_rejected(self):
        with self.assertRaisesRegex(AggregationProtocolError, "exactly 6"):
            aggregate_vrx2019_runs([0.1] * 5)
        with self.assertRaises(AggregationProtocolError):
            aggregate_vrx2019_runs([0.1, 0.2, 0.3, 0.4, 0.5, float("nan")])
        with self.assertRaises(AggregationProtocolError):
            aggregate_vrx2019_runs([0.1, 0.2, 0.3, 0.4, 0.5, True])

    def _canonical_result(self, scores=None):
        values = scores or list(VRX2019_UF_PUBLISHED_RUN_SCORES)
        return {
            "result_id": "fixture",
            "benchmark": {
                "name": "vrx-2019-station-keeping",
                "revision": "vrx-revision",
                "protocol_revision": "protocol-revision",
                "scorer": {"name": "scorer", "revision": "scorer-revision"},
            },
            "task": {"name": "station_keeping"},
            "trials": [
                {
                    "trial_id": f"trial-{i}",
                    "seed": i,
                    "status": "completed",
                    "completed": True,
                    "score": score,
                }
                for i, score in enumerate(values)
            ],
        }

    def test_result_aggregation_requires_all_six_trials_to_be_complete(self):
        result = self._canonical_result()
        summary = aggregate_vrx2019_result(result, expected_seeds=list(range(6)))
        self.assertAlmostEqual(summary["task_score"], 0.11)
        incomplete = copy.deepcopy(result)
        incomplete["trials"][2]["status"] = "timeout"
        incomplete["trials"][2]["completed"] = False
        with self.assertRaisesRegex(AggregationProtocolError, "not complete"):
            aggregate_vrx2019_result(incomplete)
        with self.assertRaisesRegex(AggregationProtocolError, "exactly 6"):
            aggregate_vrx2019_result({**result, "trials": result["trials"][:5]})

    def test_comparison_reports_identity_mismatch_instead_of_claiming_direct(self):
        candidate = self._canonical_result([0.01] * 6)
        reference = self._canonical_result()
        candidate["benchmark"]["protocol_revision"] = "public-phase2"
        comparison = compare_vrx2019_results(candidate, reference)
        self.assertFalse(comparison["comparable"])
        self.assertEqual(comparison["comparison_status"], "not_comparable")
        self.assertIn("protocol_revision", comparison["identity_mismatches"])
        self.assertAlmostEqual(comparison["delta_candidate_minus_reference"], -0.1)

    def test_raw_vector_comparison_is_explicitly_arithmetic_only(self):
        comparison = compare_vrx2019_run_vectors([0.01] * 6, VRX2019_UF_PUBLISHED_RUN_SCORES)
        self.assertFalse(comparison["comparable"])
        self.assertEqual(comparison["comparison_status"], "arithmetic_only")
        self.assertAlmostEqual(comparison["candidate"]["task_score"], 0.01)

    def test_unavailable_score_direction_is_not_accepted_as_2019(self):
        result = self._canonical_result()
        result["status"] = "failed"
        with self.assertRaisesRegex(AggregationProtocolError, "status=completed"):
            aggregate_vrx2019_result(result)

    def test_task_ranking_assigns_dnf_last_rank_and_competition_ties(self):
        ranks = rank_vrx2019_task_scores({"a": 0.1, "b": 0.1, "c": 0.2, "dnf": None})
        self.assertEqual(ranks, {"a": 1, "b": 1, "c": 3, "dnf": 4})
        self.assertEqual(rank_vrx2019_task_scores({"a": 0.1, "dnf": "DSQ"}), {"a": 1, "dnf": 2})

    def test_leaderboard_sums_task_ranks_for_overall_order(self):
        leaderboard = aggregate_vrx2019_leaderboard(
            {
                "alpha": {"stationkeeping": 0.1, "wayfinding": 0.3},
                "bravo": {"stationkeeping": 0.2, "wayfinding": 0.1},
                "charlie": {"stationkeeping": None, "wayfinding": 0.2},
            },
            task_order=["stationkeeping", "wayfinding"],
        )
        self.assertEqual(leaderboard["task_ranks"]["stationkeeping"], {"alpha": 1, "bravo": 2, "charlie": 3})
        self.assertEqual(leaderboard["task_ranks"]["wayfinding"], {"bravo": 1, "charlie": 2, "alpha": 3})
        self.assertEqual(leaderboard["overall_totals"], {"alpha": 4, "bravo": 3, "charlie": 5})
        self.assertEqual(leaderboard["overall_ranks"], {"bravo": 1, "alpha": 2, "charlie": 3})


if __name__ == "__main__":
    unittest.main()
