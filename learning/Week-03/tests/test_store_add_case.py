"""Tests for CaseStore.add_case using temporary index/metadata files."""

import json
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import faiss  # noqa: E402
from services.store import CaseStore  # noqa: E402


class TestStoreAddCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.index_path = os.path.join(self.tmp.name, "index.index")
        self.names_path = os.path.join(self.tmp.name, "case_names.txt")
        self.metadata_path = os.path.join(self.tmp.name, "metadata.json")

        seed = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32).reshape(1, -1)
        index = faiss.IndexFlatIP(4)
        index.add(seed)
        faiss.write_index(index, self.index_path)
        with open(self.names_path, "w") as f:
            f.write("PETS-01\n")
        with open(self.metadata_path, "w") as f:
            json.dump({"PETS-01": {"case_id": "PETS-01", "title": "seed"}}, f)

        self.store = CaseStore(
            index_path=self.index_path,
            names_path=self.names_path,
            metadata_path=self.metadata_path,
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_case_grows_index(self):
        self.assertEqual(len(self.store), 1)
        added = self.store.add_case("PETS-02", [0.0, 1.0, 0.0, 0.0], {"case_id": "PETS-02", "title": "new"})
        self.assertEqual(added, "PETS-02")
        self.assertEqual(len(self.store), 2)

    def test_new_case_is_searchable(self):
        self.store.add_case("PETS-02", [0.0, 1.0, 0.0, 0.0], {"case_id": "PETS-02"})
        results = self.store.nearest([0.0, 1.0, 0.0, 0.0], 2)
        self.assertEqual(results[0][0], "PETS-02")

    def test_persists_to_files(self):
        self.store.add_case("ITEMS-21", [0.0, 0.0, 1.0, 0.0], {"case_id": "ITEMS-21", "category": "drone"})
        reloaded = CaseStore(
            index_path=self.index_path,
            names_path=self.names_path,
            metadata_path=self.metadata_path,
        )
        self.assertEqual(len(reloaded), 2)
        self.assertIn("ITEMS-21", reloaded.case_names)
        self.assertEqual(reloaded.metadata["ITEMS-21"]["category"], "drone")
        found = reloaded.nearest([0.0, 0.0, 1.0, 0.0], 1)
        self.assertEqual(found[0][0], "ITEMS-21")

    def test_embedding_is_normalized_before_add(self):
        self.store.add_case("PERS-11", [0.0, 0.0, 5.0, 0.0], {"case_id": "PERS-11"})
        found = self.store.nearest([0.0, 0.0, 1.0, 0.0], 1)
        self.assertEqual(found[0][0], "PERS-11")
        self.assertAlmostEqual(found[0][1], 1.0, places=5)
        far = self.store.nearest([1.0, 0.0, 0.0, 0.0], 1)
        self.assertEqual(far[0][0], "PETS-01")


if __name__ == "__main__":
    unittest.main()