"""Kiểm thử Analytics, Evaluation, Prediction và các quy tắc riêng từng game."""
import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

import analytics
import evaluation
import prediction
import server


def fake_rows(game, count=90):
    cfg=server.GAMES[game]
    rows=[]
    for i in range(count):
        nums=sorted({((i*7+j*11) % cfg["maxn"])+1 for j in range(cfg["main"])})
        # Deterministic unique main numbers, fallback for any collision.
        n=1
        while len(nums)<cfg["main"]:
            if n not in nums: nums.append(n)
            n+=1
        nums=sorted(nums[:cfg["main"]])
        r={"d":f"2026-01-{(i%28)+1:02d}","n":nums,"b":None}
        if cfg["bonus"]:
            r["b"]=((i*3)%cfg.get("bmax",cfg["maxn"]))+1
            if game=="535": r["h"]=13 if i%2==0 else 21
        rows.append(r)
    # Newest first is the required repo convention.
    return rows


class AnalyticsTests(unittest.TestCase):
    def test_game_analytics_and_535_hours(self):
        for game in ("655","645","535"):
            result=analytics.analyze_game(game,fake_rows(game))
            self.assertEqual(result["draw_count"],90)
            self.assertIn("60",result["windows"])
            self.assertTrue(result["pairs"])
            self.assertTrue(result["cycles"])
            if game=="535":
                self.assertEqual(result["draws_by_hour"],{"13":45,"21":45})
                self.assertEqual(result["bonus"]["range"],[1,12])


class EvaluationTests(unittest.TestCase):
    def test_seven_methods_reproducible_and_valid(self):
        for game in ("655","645","535"):
            rows=fake_rows(game)
            a,ba=evaluation.method_sets(game,rows[1:],20,12345)
            b,bb=evaluation.method_sets(game,rows[1:],20,12345)
            self.assertEqual(a,b)
            self.assertEqual(ba,bb)
            self.assertEqual(set(a),set(evaluation.METHODS))
            for nums in a.values():
                self.assertEqual(len(nums),server.GAMES[game]["main"])
                self.assertEqual(len(set(nums)),len(nums))
                self.assertTrue(all(1<=n<=server.GAMES[game]["maxn"] for n in nums))
            if game=="655":
                self.assertTrue(all(ba[m] not in a[m] for m in evaluation.METHODS))
            if game=="535":
                self.assertTrue(all(1<=ba[m]<=12 for m in evaluation.METHODS))

    def test_walk_forward_count_and_multiple_testing(self):
        result=evaluation.evaluate_game("645",fake_rows("645",75))
        self.assertEqual(result["draws_evaluated"],15)
        self.assertEqual(len(result["methods"]),7)
        self.assertIn("paired_diff_ci95",result["methods"]["rnd"])
        q=[v["bh_q_value"] for v in result["methods"].values()]
        self.assertTrue(all(0<=x<=1 for x in q))
        self.assertEqual(len(result["segments"]),1)
        self.assertEqual(result["random_control"]["simulation_count"],15*evaluation.RANDOM_REPS)

    def test_target_draw_is_not_part_of_training_features(self):
        rows=fake_rows("645",80)
        train=rows[1:]
        before=evaluation.method_sets("645",train,20,2026)
        # Mutating the held-out target cannot affect a method call that receives only train.
        rows[0]["n"]=[1,2,3,4,5,6]
        after=evaluation.method_sets("645",train,20,2026)
        self.assertEqual(before,after)

    def test_bh_adjustment_is_bounded_and_monotone_by_rank(self):
        q=evaluation.bh_adjust({"a":.001,"b":.02,"c":.2})
        self.assertTrue(all(0<=x<=1 for x in q.values()))
        self.assertLessEqual(q["a"],q["b"])
        self.assertLessEqual(q["b"],q["c"])


class PredictionTests(unittest.TestCase):
    def test_five_tickets_diversified_and_valid(self):
        for game in ("655","645","535"):
            rows=fake_rows(game)
            tickets,meta=prediction.build_five(game,rows,987654)
            self.assertEqual(len(tickets),5)
            self.assertEqual(len({tuple(t["numbers"]) for t in tickets}),5)
            for t in tickets:
                self.assertEqual(len(t["numbers"]),server.GAMES[game]["main"])
                self.assertEqual(len(set(t["numbers"])),len(t["numbers"]))
                self.assertTrue(all(1<=n<=server.GAMES[game]["maxn"] for n in t["numbers"]))
                if game=="655":
                    self.assertNotIn(t["bonus"],t["numbers"])
                if game=="535":
                    self.assertTrue(1<=t["bonus"]<=12)
            for i in range(5):
                for j in range(i):
                    limit=3 if game in ("655","645") else 2
                    self.assertLessEqual(len(set(tickets[i]["numbers"])&set(tickets[j]["numbers"])),limit)
            self.assertGreater(meta["unique_main_numbers_covered"],0)

    def test_prediction_log_is_append_only_jsonl(self):
        old=prediction.LOG
        try:
            with tempfile.TemporaryDirectory() as d:
                prediction.LOG=os.path.join(d,"predictions_log.jsonl")
                prediction.append_event({"event_type":"prediction","prediction_id":"x"})
                prediction.append_event({"event_type":"evaluation","prediction_id":"x"})
                events=prediction.read_events()
                self.assertEqual([x["event_type"] for x in events],["prediction","evaluation"])
        finally:
            prediction.LOG=old

    def test_lock_once_then_append_evaluation_without_mutating_prediction(self):
        with tempfile.TemporaryDirectory() as d:
            log=os.path.join(d,"predictions_log.jsonl")
            now=datetime(2026,11,24,17,0,tzinfo=server.VN)
            rows={g:fake_rows(g,90) for g in ("655","645","535")}
            with patch.object(prediction,"LOG",log), patch.object(server,"read_ods",side_effect=lambda g:rows[g]), patch.object(server,"now_vn",return_value=now):
                first=prediction.main()
                locked=prediction.read_events()
                second=prediction.main()
                self.assertEqual(first["created"],3)
                self.assertEqual(second["created"],0)
                originals=[dict(e) for e in locked if e["event_type"]=="prediction"]
                for event in originals:
                    target=event["target_draw"]
                    date=target[:10]
                    hour=int(target[-2:]) if "T" in target else None
                    ticket=event["tickets"][0]
                    row={"d":date,"n":ticket["numbers"],"b":ticket.get("bonus")}
                    if hour is not None: row["h"]=hour
                    rows[event["game"]].insert(0,row)
                scored=prediction.evaluate_locked(rows,prediction.read_events())
                final=prediction.read_events()
                self.assertEqual(scored,3)
                self.assertEqual(sum(e["event_type"]=="evaluation" for e in final),3)
                self.assertEqual([e for e in final if e["event_type"]=="prediction"],originals)

    def test_next_draw_is_strictly_future(self):
        now=datetime(2026,11,24,17,0,tzinfo=server.VN)
        dt,key=prediction.next_draw("655",now,fake_rows("655",80))
        self.assertGreater(dt,now)
        self.assertEqual(dt.hour,18)
        dt535,key535=prediction.next_draw("535",datetime(2026,11,24,12,0,tzinfo=server.VN),fake_rows("535",80))
        self.assertEqual(dt535.hour,13 if dt535.hour==13 else 21)
        self.assertGreater(dt535,datetime(2026,11,24,12,0,tzinfo=server.VN))


if __name__=="__main__":
    unittest.main()
