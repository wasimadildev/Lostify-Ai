"""Tests for the SQLite persistence layer (no model loads, uses temp DB files)."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db  # noqa: E402


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")

    def tearDown(self):
        self.tmp.cleanup()

    def test_init_creates_table(self):
        db.init_db(self.db_path)
        with db.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='reports'"
            ).fetchall()
        self.assertEqual(len(rows), 1)

    def test_insert_and_count(self):
        db.init_db(self.db_path)
        self.assertEqual(db.count(self.db_path), 0)
        db.insert_report({
            "case_id": "PETS-15", "case_type": "lost_pet", "title": "Test cat",
            "description": "orange cat", "source": "user",
        }, db_path=self.db_path)
        self.assertEqual(db.count(self.db_path), 1)

    def test_none_values_are_nullable(self):
        db.init_db(self.db_path)
        db.insert_report({"case_id": "ITEMS-21", "case_type": "lost_item"}, db_path=self.db_path)
        rows = db.list_reports(db_path=self.db_path)
        self.assertEqual(rows[0]["case_id"], "ITEMS-21")
        self.assertIsNone(rows[0]["title"])

    def test_next_case_id_sequence(self):
        db.init_db(self.db_path)
        db.insert_report({"case_id": "PETS-14", "case_type": "lost_pet"}, db_path=self.db_path)
        db.insert_report({"case_id": "PETS-15", "case_type": "lost_pet"}, db_path=self.db_path)
        db.insert_report({"case_id": "PERS-10", "case_type": "lost_person"}, db_path=self.db_path)
        self.assertEqual(db.next_case_id("lost_pet", self.db_path), "PETS-16")
        self.assertEqual(db.next_case_id("lost_person", self.db_path), "PERS-11")
        self.assertEqual(db.next_case_id("lost_item", self.db_path), "ITEMS-01")

    def test_seed_from_metadata_idempotent(self):
        metadata = {
            "PETS-01": {"case_id": "PETS-01", "case_type": "lost_pet", "title": "A"},
            "ITEMS-03": {"case_id": "ITEMS-03", "case_type": "lost_item", "title": "B"},
        }
        meta_path = os.path.join(self.tmp.name, "metadata.json")
        with open(meta_path, "w") as f:
            json.dump(metadata, f)

        db.init_db(self.db_path)
        seeded = db.seed_from_metadata(self.db_path, meta_path)
        self.assertEqual(seeded, 2)
        db.insert_report({"case_id": "PETS-02", "case_type": "lost_pet"}, db_path=self.db_path)
        again = db.seed_from_metadata(self.db_path, meta_path)
        self.assertEqual(again, 3)  # did not duplicate

    def test_list_reports_newest_first(self):
        db.init_db(self.db_path)
        db.insert_report({"case_id": "PETS-01", "case_type": "lost_pet"}, db_path=self.db_path)
        db.insert_report({"case_id": "PETS-02", "case_type": "lost_pet"}, db_path=self.db_path)
        rows = db.list_reports(db_path=self.db_path)
        self.assertEqual([r["case_id"] for r in rows], ["PETS-02", "PETS-01"])


if __name__ == "__main__":
    unittest.main()