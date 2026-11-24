#!/usr/bin/env python3
"""Prediction Engine: 5 vé đa dạng, khóa trước giờ quay, kết quả được ghi thành event mới."""
import hashlib
import json
import os
import random
from datetime import datetime, timedelta

import server
from evaluation import method_sets, stable_seed, weighted_pick

BASE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(BASE, "predictions_log.jsonl")
ALGORITHM_VERSION = "ensemble-diversity-v1"
STRATEGIES = [
    ("random_control", "Ngẫu nhiên thuần"),
    ("weighted", "Ngẫu nhiên có trọng số"),
    ("hot_short", "Tín hiệu tần suất ngắn hạn"),
    ("composite", "Ensemble tổng hợp"),
    ("coverage", "Phủ số đa dạng")
]


def append_event(event):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")


def read_events():
    if not os.path.exists(LOG):
        return []
    events = []
    with open(LOG, encoding="utf-8") as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except (ValueError, TypeError):
                continue
    return events


def next_draw(game, now, rows):
    cfg = server.GAMES[game]
    latest = server.rowkey(game, rows[0]) if rows else ""
    for offset in range(0, 15):
        day = (now + timedelta(days=offset)).date()
        if day.weekday() not in cfg["days"]:
            continue
        for hour in server.hrs(game):
            dt = datetime.combine(day, datetime.min.time(), tzinfo=server.VN).replace(hour=hour)
            key = day.isoformat() + ("T%02d" % hour if server.multi(game) else "")
            if dt > now and key > latest:
                return dt, key
    return None, None


def _weighted_from_scores(scores, maximum, k, rng):
    weights = [0.0] + [max(.01, float(scores[n])) for n in range(1, maximum + 1)]
    return weighted_pick(weights, maximum, k, rng)


def _candidate_sets(game, rows, seed, count=320):
    cfg = server.GAMES[game]
    maximum, k = cfg["maxn"], cfg["main"]
    nwin = min(20, len(rows))
    recent_counts = [0] + [sum(n in r["n"] for r in rows[:nwin]) for n in range(1, maximum + 1)]
    all_counts = [0] + [sum(n in r["n"] for r in rows) for n in range(1, maximum + 1)]
    gap = [0] + [next((i for i, r in enumerate(rows) if n in r["n"]), len(rows))
                 for n in range(1, maximum + 1)]
    def z(a):
        vals = a[1:]
        mean = sum(vals) / maximum
        sd = (sum((v-mean)**2 for v in vals) / maximum) ** .5 or 1
        return [0] + [(a[n]-mean)/sd for n in range(1, maximum+1)]
    zr, za, zg = z(recent_counts), z(all_counts), z(gap)
    composite = [0] + [.4*zr[n]+.3*za[n]+.3*zg[n] for n in range(1, maximum+1)]
    short = [0] + [recent_counts[n]+1 for n in range(1, maximum+1)]
    longmix = [0] + [.65*(recent_counts[n]+1)+.35*(all_counts[n]+1) for n in range(1, maximum+1)]
    rng = random.Random(seed)
    pools = {name: [] for name, _ in STRATEGIES}
    # Fixed strategy anchors are included, but no historical method is treated as a proven signal.
    fixed, _ = method_sets(game, rows, nwin, seed)
    pools["hot_short"].append(fixed["hot"])
    pools["composite"].append(fixed["bal"])
    pools["coverage"].append(fixed["cold"])
    for _ in range(count):
        pools["random_control"].append(weighted_pick([0]+[1]*maximum, maximum, k, rng))
        pools["weighted"].append(weighted_pick([0]+[recent_counts[n]+1 for n in range(1,maximum+1)], maximum,k,rng))
        pools["hot_short"].append(_weighted_from_scores(short,maximum,k,rng))
        pools["composite"].append(_weighted_from_scores([0]+[max(.01, 1+composite[n]) for n in range(1,maximum+1)],maximum,k,rng))
        pools["coverage"].append(_weighted_from_scores(longmix,maximum,k,rng))
    return pools, recent_counts, all_counts


def build_five(game, rows, seed):
    cfg = server.GAMES[game]
    maximum, k = cfg["maxn"], cfg["main"]
    pools, recent_counts, all_counts = _candidate_sets(game, rows, seed)
    max_overlap = max(1, k - 3) if k >= 5 else k - 1
    selected, used = [], set()
    for idx, (strategy, label) in enumerate(STRATEGIES):
        candidates = list(dict.fromkeys(tuple(sorted(x)) for x in pools[strategy]))
        rng = random.Random(stable_seed(seed, strategy))
        rng.shuffle(candidates)
        best, best_score = None, None
        for candidate in candidates:
            if len(candidate) != k or len(set(candidate)) != k:
                continue
            overlaps = [len(set(candidate) & set(s)) for s in selected]
            if overlaps and max(overlaps) > max_overlap:
                continue
            novelty = len(set(candidate) - used)
            overlap_penalty = sum(overlaps)
            freq_score = sum(recent_counts[n] for n in candidate) / max(1, k)
            # Diversification is the portfolio objective, not an increase in draw probability.
            score = novelty * 4.0 - overlap_penalty * 1.5
            if strategy == "hot_short":
                score += freq_score * .05
            if best_score is None or score > best_score:
                best, best_score = candidate, score
        if best is None:
            # Relax only the pairwise overlap bound as a last resort; retain distinct tickets.
            best = min(candidates, key=lambda c: (sum(len(set(c)&set(s)) for s in selected),
                                                  -len(set(c)-used)))
        selected.append(list(best))
        used.update(best)
    tickets = []
    bmax = cfg.get("bmax", maximum) if cfg["bonus"] else 0
    bonus_freq = [0] + [sum(r.get("b") == n for r in rows) for n in range(1,bmax+1)] if bmax else []
    for i, ((strategy,label), nums) in enumerate(zip(STRATEGIES, selected)):
        bonus = None
        if cfg["bonus"]:
            brng = random.Random(stable_seed(seed, "bonus", strategy))
            excluded = nums if game == "655" else []
            candidates = [n for n in range(1,bmax+1) if n not in excluded]
            weights = [0.0] + [float(bonus_freq[n]+1) for n in range(1,bmax+1)]
            # For Lotto 5/35, special number 1–12 may overlap main numbers by design.
            bonus = weighted_pick(weights, bmax, 1, brng, excluded)[0]
        tickets.append({"strategy": strategy, "label": label, "numbers": nums, "bonus": bonus})
    return tickets, {"max_pair_overlap": max_overlap, "unique_main_numbers_covered": len(used),
                     "pairwise_overlap": [[len(set(a)&set(b)) for b in selected] for a in selected]}


def source_signature():
    h = hashlib.sha256()
    for game in ("655","645","535"):
        path = server.ods_path(game)
        with open(path,"rb") as f:
            h.update(game.encode()); h.update(f.read())
    return h.hexdigest()


def evaluate_locked(rows_by_game, events):
    already = {e.get("prediction_id") for e in events if e.get("event_type") == "evaluation"}
    appended = 0
    for event in events:
        if event.get("event_type") != "prediction" or event.get("prediction_id") in already:
            continue
        game, target = event.get("game"), event.get("target_draw")
        if game not in rows_by_game:
            continue
        match = next((r for r in rows_by_game[game] if server.rowkey(game,r) == target), None)
        if not match:
            continue
        scored = []
        for ticket in event.get("tickets", []):
            hits = sorted(set(ticket["numbers"]) & set(match["n"]))
            bonus_hit = bool(ticket.get("bonus") is not None and ticket.get("bonus") == match.get("b"))
            scored.append({"strategy":ticket["strategy"],"main_hits":len(hits),
                           "matched_numbers":hits,"bonus_hit":bonus_hit})
        append_event({
            "event_type":"evaluation","prediction_id":event["prediction_id"],
            "game":game,"target_draw":target,"result_numbers":match["n"],
            "result_bonus":match.get("b"),"evaluated_at":server.now_vn().isoformat(timespec="seconds"),
            "tickets":scored
        })
        already.add(event["prediction_id"])
        appended += 1
    return appended


def main():
    rows_by_game = {g: server.read_ods(g) for g in ("655","645","535")}
    events = read_events()
    evaluated = evaluate_locked(rows_by_game, events)
    if evaluated:
        print("Prediction History: đã ghi %d event đối chiếu" % evaluated)
    events = read_events()
    existing = {(e.get("game"),e.get("target_draw")) for e in events
                if e.get("event_type") == "prediction"}
    now = server.now_vn()
    sig = source_signature()
    created = 0
    for game in ("655","645","535"):
        rows = rows_by_game[game]
        if not rows:
            continue
        dt, target = next_draw(game, now, rows)
        if not target or (game,target) in existing:
            continue
        seed = stable_seed(ALGORITHM_VERSION, game, target, server.rowkey(game,rows[0]))
        tickets, diversity = build_five(game, rows, seed)
        pid = hashlib.sha256(("%s|%s|%s|%s" % (game,target,seed,ALGORITHM_VERSION)).encode()).hexdigest()[:20]
        append_event({
            "event_type":"prediction","prediction_id":pid,"created_at":now.isoformat(timespec="seconds"),
            "game":game,"target_draw":target,"target_time":dt.isoformat(timespec="minutes"),
            "source_latest_draw":server.rowkey(game,rows[0]),"source_signature":sig,
            "algorithm_version":ALGORITHM_VERSION,"seed":seed,
            "parameters":{"window":min(20,len(rows)),"ticket_count":5,"max_pair_overlap":diversity["max_pair_overlap"],
                          "candidate_pool_per_strategy":320,"main_number_range":[1,server.GAMES[game]["maxn"]],
                          "special_range":[1,server.GAMES[game].get("bmax",0)] if server.GAMES[game]["bonus"] else None},
            "diversity":diversity,"tickets":tickets,
            "disclaimer":"Các kỳ quay độc lập; đa dạng hóa chỉ giảm trùng lặp giữa vé, không tăng xác suất của một vé."
        })
        created += 1
        print("Đã khóa 5 bộ %s cho kỳ %s" % (game,target))
    if created:
        print("Prediction History: thêm %d bản ghi dự đoán" % created)
    return {"created":created,"evaluated":evaluated}


if __name__ == "__main__":
    main()
