import unittest

from vrx_record_lab.barn_metric import BarnRun, aggregate, parse_log, score_run


class BarnMetricTests(unittest.TestCase):
    def test_parse_accepts_logged_metric_column(self):
        runs = parse_log(["0 1 0 0 10.0 0.5", "0 0 1 0 12.0 0.0"])
        self.assertEqual(len(runs), 2)
        self.assertTrue(runs[0].succeeded)
        self.assertFalse(runs[1].succeeded)

    def test_score_clips_to_bounded_performance(self):
        self.assertEqual(score_run(BarnRun(0, True, False, False, 1.0), 1.0), 0.5)
        self.assertEqual(score_run(BarnRun(0, False, True, False, 1.0), 1.0), 0.0)

    def test_aggregate_requires_balanced_suite(self):
        runs = [BarnRun(0, True, False, False, 2.0)]
        with self.assertRaisesRegex(ValueError, "incomplete"):
            aggregate(runs, {0: 1.0}, expected_worlds=(0,), trials_per_world=2)

    def test_aggregate_reports_success_and_rates(self):
        runs = [
            BarnRun(0, True, False, False, 2.0),
            BarnRun(0, False, True, False, 2.0),
        ]
        result = aggregate(runs, {0: 1.0}, expected_worlds=(0,), trials_per_world=2)
        self.assertEqual(result["overall_score"], 0.25)
        self.assertEqual(result["success_rate"], 0.5)
        self.assertEqual(result["collision_rate"], 0.5)

    def test_logged_metric_mismatch_is_retained_as_audit_metadata(self):
        runs = [
            BarnRun(0, True, False, False, 2.0, logged_metric=0.1),
        ]
        result = aggregate(runs, {0: 1.0}, expected_worlds=(0,), trials_per_world=1)
        self.assertEqual(result["logged_metric_mismatches"], 1)
