"""Kiểm tra cấu trúc và tính hợp lệ của ba bộ dữ liệu ODS."""
import unittest
import json
import os
import tempfile
from unittest.mock import patch

import server


class ODSIntegrityTests(unittest.TestCase):
    def test_all_games_have_rows_and_unique_draw_keys(self):
        for game in server.GAMES:
            with self.subTest(game=game):
                rows = server.read_ods(game)
                self.assertTrue(rows)
                keys = [server.rowkey(game, row) for row in rows]
                self.assertEqual(len(keys), len(set(keys)), "trùng mã kỳ quay")
                self.assertEqual(keys, sorted(keys, reverse=True), "dữ liệu phải mới nhất ở đầu")

    def test_main_numbers_are_unique_and_in_range(self):
        for game, cfg in server.GAMES.items():
            for row in server.read_ods(game):
                with self.subTest(game=game, draw=server.rowkey(game, row)):
                    self.assertEqual(len(row["n"]), cfg["main"])
                    self.assertEqual(len(set(row["n"])), cfg["main"])
                    self.assertTrue(all(1 <= n <= cfg["maxn"] for n in row["n"]))

    def test_bonus_number_rules(self):
        for game, cfg in server.GAMES.items():
            if not cfg["bonus"]:
                continue
            for row in server.read_ods(game):
                with self.subTest(game=game, draw=server.rowkey(game, row)):
                    self.assertIsNotNone(row["b"])
                    self.assertGreaterEqual(row["b"], 1)
                    self.assertLessEqual(row["b"], cfg.get("bmax", cfg["maxn"]))
                    # Power 6/55 lấy số phụ trong 49 số còn lại; Lotto 5/35
                    # có số đặc biệt 1–12 và theo luật có thể trùng số chính.
                    if game == "655":
                        self.assertNotIn(row["b"], row["n"])

    def test_lotto_535_has_valid_draw_hours(self):
        for row in server.read_ods("535"):
            self.assertIn(row["h"], (13, 21))

    def test_shared_draw_validator_enforces_game_specific_bonus_rules(self):
        self.assertFalse(server.valid_draw_numbers("655", [1, 2, 3, 4, 5, 6, 1]))
        self.assertTrue(server.valid_draw_numbers("655", [1, 2, 3, 4, 5, 6, 7]))
        self.assertTrue(server.valid_draw_numbers("535", [1, 2, 3, 4, 5, 5]))
        self.assertFalse(server.valid_draw_numbers("535", [1, 2, 3, 4, 5, 13]))
        self.assertTrue(server.valid_draw_numbers("645", [1, 2, 3, 4, 5, 6]))
        self.assertFalse(server.valid_draw_numbers("645", [1, 2, 3, 4, 5, 6, 7]))

    def test_full_ods_validation_report(self):
        report = server.validate_ods_data()
        self.assertEqual(set(report), {"655", "645", "535"})
        self.assertTrue(all(count > 0 for count in report.values()))

    def test_source_parser_rejects_power_bonus_duplicate(self):
        invalid = "<div>T3, 24/11/2026 01 02 03 04 05 06 01</div>"
        valid = "<div>T3, 24/11/2026 01 02 03 04 05 06 07</div>"
        self.assertEqual(server.parse_source(invalid, "655"), [])
        self.assertEqual(len(server.parse_source(valid, "655")), 1)

    def test_sync_audit_is_append_only_and_records_source_consensus(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(server, "BASE", tmp):
                server.write_sync_audit("655", {"source_a": {"draw-1": {}}, "source_b": {"draw-1": {}}}, [], 1, "draw-0", "success")
                server.write_sync_audit("655", {"source_a": {"draw-2": {}}}, ["source_b timeout"], 0, "draw-1", "error")
                # Polling lặp lại cùng lỗi không được tạo commit/log trùng mỗi 5 phút.
                server.write_sync_audit("655", {"source_a": {"draw-2": {}}}, ["source_b timeout"], 0, "draw-1", "error")
            path = os.path.join(tmp, "sync_audit.jsonl")
            with open(path, encoding="utf-8") as audit_file:
                lines = [json.loads(line) for line in audit_file if line.strip()]
            self.assertEqual(len(lines), 2)
            self.assertEqual(lines[0]["source_names"], ["source_a", "source_b"])
            self.assertEqual(lines[0]["outcome"], "success")
            self.assertEqual(lines[1]["outcome"], "error")


if __name__ == "__main__":
    unittest.main()
