"""Tests for the filtering and ranking services."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.filtering_service import filter_candidates  # noqa: E402
from services.ranking_service import haversine_km, location_score, rank_candidates  # noqa: E402

CANDIDATES = [
    {"case_id": "PETS-01", "case_type": "lost_pet", "category": "cat", "status": "open",
     "latitude": 33.6844, "longitude": 73.0479},
    {"case_id": "PETS-13", "case_type": "lost_pet", "category": "dog", "status": "open",
     "latitude": 33.6844, "longitude": 73.0479},
    {"case_id": "ITEMS-06", "case_type": "lost_item", "category": "bicycle", "status": "closed",
     "latitude": 31.4504, "longitude": 73.1350},
]


class TestFiltering(unittest.TestCase):
    def test_no_filter_keeps_everything(self):
        self.assertEqual(filter_candidates(CANDIDATES), CANDIDATES)

    def test_filter_by_query_type(self):
        result = filter_candidates(CANDIDATES, query_type="lost_pet")
        self.assertEqual([c["case_id"] for c in result], ["PETS-01", "PETS-13"])

    def test_filter_by_category(self):
        result = filter_candidates(CANDIDATES, category="cat")
        self.assertEqual([c["case_id"] for c in result], ["PETS-01"])

    def test_filter_by_category_case_insensitive(self):
        result = filter_candidates(CANDIDATES, category="DOG")
        self.assertEqual([c["case_id"] for c in result], ["PETS-13"])

    def test_filter_by_status(self):
        result = filter_candidates(CANDIDATES, status="closed")
        self.assertEqual([c["case_id"] for c in result], ["ITEMS-06"])

    def test_combined_filters(self):
        result = filter_candidates(CANDIDATES, query_type="lost_pet", category="dog", status="open")
        self.assertEqual([c["case_id"] for c in result], ["PETS-13"])

    def test_empty_result(self):
        result = filter_candidates(CANDIDATES, query_type="lost_person")
        self.assertEqual(result, [])


class TestRanking(unittest.TestCase):
    def test_haversine_zero_distance(self):
        self.assertAlmostEqual(haversine_km(30.0, 71.0, 30.0, 71.0), 0.0, places=3)

    def test_haversine_islamabad_to_lahore(self):
        distance = haversine_km(33.6844, 73.0479, 31.5497, 74.3436)
        self.assertGreater(distance, 200)
        self.assertLess(distance, 320)

    def test_location_exact_city_match(self):
        case = {"location": "Islamabad"}
        self.assertEqual(location_score(case, "Islamabad"), 1.0)
        self.assertEqual(location_score(case, "islamabad"), 1.0)

    def test_location_distant_city_zero(self):
        case = {"latitude": 33.6844, "longitude": 73.0479}
        self.assertEqual(location_score(case, None, 24.8607, 67.0011), 0.0)

    def test_location_forgone_no_query_location(self):
        case = {"location": "Islamabad", "latitude": 33.6844, "longitude": 73.0479}
        self.assertIsNone(location_score(case, None, None, None))

    def test_final_score_weighted_formula(self):
        candidates = [{"case_id": "C", "location": "Islamabad",
                       "latitude": 33.6844, "longitude": 73.0479}]
        result = rank_candidates(
            candidates,
            visual_scores={"C": 0.89},
            text_scores={"C": 0.82},
            query_location="Islamabad",
        )[0]
        expected = 0.70 * 0.89 + 0.20 * 0.82 + 0.10 * 1.0
        self.assertAlmostEqual(result["final_score"], round(expected, 4))
        self.assertAlmostEqual(result["visual_score"], 0.89)
        self.assertAlmostEqual(result["text_score"], 0.82)
        self.assertAlmostEqual(result["location_score"], 1.0)

    def test_ranking_sorts_by_final_score(self):
        candidates = [
            {"case_id": "A"},
            {"case_id": "B"},
        ]
        result = rank_candidates(
            candidates, visual_scores={"A": 0.9, "B": 0.6}, text_scores={}
        )
        self.assertEqual([r["case_id"] for r in result], ["A", "B"])

    def test_missing_scores_default_to_zero(self):
        candidates = [{"case_id": "C", "latitude": 33.6844, "longitude": 73.0479}]
        result = rank_candidates(candidates, visual_scores={"D": 1.0})[0]
        self.assertEqual(result["final_score"], 0.0)
        self.assertEqual(result["visual_score"], 0.0)

    def test_visual_only_renormalizes_weights(self):
        candidates = [{"case_id": "C"}]
        result = rank_candidates(candidates, visual_scores={"C": 1.0})[0]
        self.assertEqual(result["final_score"], 1.0)


class TestMultimodal(unittest.TestCase):
    def test_combined_normalized_unit_norm(self):
        from services.multimodal_service import combine_embeddings

        image = [1.0, 0.0, 0.0, 0.0]
        text = [0.0, 1.0, 0.0, 0.0]
        combined = combine_embeddings(image, text, 0.7, 0.3)
        self.assertAlmostEqual(sum(v ** 2 for v in combined), 1.0, places=5)

    def test_only_image(self):
        from services.multimodal_service import combine_embeddings

        image = [3.0, 4.0]
        combined = combine_embeddings(image, None)
        self.assertAlmostEqual(combined[0], 0.6)
        self.assertAlmostEqual(combined[1], 0.8)

    def test_only_text(self):
        from services.multimodal_service import combine_embeddings

        text = [3.0, 4.0]
        combined = combine_embeddings(None, text)
        self.assertAlmostEqual(combined[0], 0.6)

    def test_both_none_raises(self):
        from services.multimodal_service import combine_embeddings

        with self.assertRaises(ValueError):
            combine_embeddings(None, None)

    def test_zero_vector_raises(self):
        from services.multimodal_service import combine_embeddings

        with self.assertRaises(ValueError):
            combine_embeddings([0.0, 0.0], None)


if __name__ == "__main__":
    unittest.main()