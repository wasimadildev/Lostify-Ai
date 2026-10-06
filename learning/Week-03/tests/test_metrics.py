"""Tests for the dependency-free retrieval metrics."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.metrics import (  # noqa: E402
    accuracy_at_k,
    is_hit_at,
    mean_reciprocal_rank,
    recall_at_k,
    reciprocal_rank,
)


class TestMetrics(unittest.TestCase):
    def test_hit_at_k_true(self):
        self.assertTrue(is_hit_at(["A", "B", "C"], ["B"], 2))
        self.assertTrue(is_hit_at(["A", "B", "C"], ["C"], 3))

    def test_hit_at_k_false(self):
        self.assertFalse(is_hit_at(["A", "B", "C"], ["C"], 2))
        self.assertFalse(is_hit_at(["A", "B", "C"], ["Z"], 3))

    def test_recall_at_k_single_expected(self):
        self.assertEqual(recall_at_k(["C", "B", "A"], ["C"], 1), 1.0)
        self.assertEqual(recall_at_k(["C", "B", "A"], ["C"], 0), 0.0)

    def test_recall_multiple_expected(self):
        self.assertEqual(recall_at_k(["A", "B", "C", "D"], ["A", "D"], 2), 0.5)
        self.assertEqual(recall_at_k(["A", "B", "C", "D"], ["A", "D"], 4), 1.0)

    def test_recall_empty_expected(self):
        self.assertEqual(recall_at_k(["A", "B"], [], 5), 0.0)

    def test_reciprocal_rank_first_match(self):
        self.assertEqual(reciprocal_rank(["X", "A", "Y"], ["A"]), 0.5)

    def test_reciprocal_rank_no_match(self):
        self.assertEqual(reciprocal_rank(["X", "Y"], ["A"]), 0.0)

    def test_mean_reciprocal_rank(self):
        results = [
            (["A", "B"], ["A"]),   # 1/1
            (["C", "A"], ["A"]),   # 1/2
            (["X", "Y"], ["A"]),   # 0/1
        ]
        self.assertAlmostEqual(mean_reciprocal_rank(results), (1.0 + 0.5 + 0.0) / 3)

    def test_accuracy_at_k(self):
        results = [
            (["A", "B", "C"], ["A"]),  # hit@1
            (["A", "B", "C"], ["C"]),  # miss@1, hit@3
            (["A", "B", "C"], ["Z"]),  # never
        ]
        self.assertEqual(accuracy_at_k(results, 1), 1.0 / 3)
        self.assertEqual(accuracy_at_k(results, 3), 2.0 / 3)

    def test_accuracy_at_k_empty(self):
        self.assertEqual(accuracy_at_k([], 5), 0.0)


if __name__ == "__main__":
    unittest.main()