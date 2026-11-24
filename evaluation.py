#!/usr/bin/env python3
"""Evaluation Engine: strict walk-forward, random control, CI, BH correction, stability segments."""
import hashlib
import json
import math
import os
import random
import statistics
from collections import Counter

import server

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "evaluation.json")
METHODS = ("pos", "hot", "cold", "all", "bal", "wr", "rnd")
METHOD_LABELS = {
    "pos": "Trung bình theo vị trí",
    "hot": "Số nóng",
    "cold": "Số lâu chưa ra",
    "all": "Tần suất toàn thời gian",
    "bal": "Điểm tổng hợp",
    "wr": "Ngẫu nhiên có trọng số",
    "rnd": "Ngẫu nhiên thuần"
}
MIN_TRAIN = 60
DEFAULT_N = 20
RANDOM_REPS = 120
SEGMENT_SIZE = 100


def stable_seed(*parts):
    raw = "|".join(map(str, parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def zscores(arr, maximum):
    vals = [arr[n] for n in range(1, maximum + 1)]
    mean = sum(vals) / maximum
    sd = math.sqrt(sum((x - mean) ** 2 for x in vals) / maximum) or 1.0
    return [0.0] + [(arr[n] - mean) / sd for n in range(1, maximum + 1)]


def top_k(scores, maximum, k):
    return sorted(range(1, maximum + 1), key=lambda n: (-scores[n], n))[:k]


def weighted_pick(weights, maximum, k, rng, excluded=None):
    excluded = set(excluded or ())
    pool = {n: float(weights[n]) for n in range(1, maximum + 1) if n not in excluded}
    out = []
    for _ in range(k):
        total = sum(pool.values())
        if not pool or total <= 0:
            break
        point = rng.random() * total
        chosen = next(iter(pool))
        for n, weight in pool.items():
            point -= weight
            if point <= 0:
                chosen = n
                break
        out.append(chosen)
        del pool[chosen]
    return sorted(out)


def method_sets(game, train, n_window, seed):
    cfg = server.GAMES[game]
    maximum, k = cfg["maxn"], cfg["main"]
    n_window = min(max(1, n_window), len(train))
    recent = Counter(x for row in train[:n_window] for x in row["n"])
    total = Counter(x for row in train for x in row["n"])
    gap = {n: next((i for i, row in enumerate(train) if n in row["n"]), len(train))
           for n in range(1, maximum + 1)}
    f_recent = [0] + [recent[n] for n in range(1, maximum + 1)]
    f_total = [0] + [total[n] for n in range(1, maximum + 1)]
    f_gap = [0] + [gap[n] for n in range(1, maximum + 1)]
    zn, za, zg = (zscores(a, maximum) for a in (f_recent, f_total, f_gap))
    combined = [0.0] + [.4 * zn[n] + .3 * za[n] + .3 * zg[n]
                        for n in range(1, maximum + 1)]
    pos = []
    for i in range(k):
        mean = sum(sorted(r["n"])[i] for r in train[:n_window]) / n_window
        pos.append(math.floor(mean + 0.5))
    for i in range(k):
        pos[i] = max(pos[i], pos[i - 1] + 1 if i else 1)
    for i in range(k - 1, -1, -1):
        pos[i] = min(pos[i], maximum - (k - 1 - i))
    hot_scores = [0] + [recent[n] * 1000 + total[n] for n in range(1, maximum + 1)]
    deterministic = {
        "pos": sorted(pos),
        "hot": sorted(top_k(hot_scores, maximum, k)),
        "cold": sorted(top_k(f_gap, maximum, k)),
        "all": sorted(top_k(f_total, maximum, k)),
        "bal": sorted(top_k(combined, maximum, k))
    }
    rng = random.Random(seed)
    deterministic["wr"] = weighted_pick([0] + [recent[n] + 1 for n in range(1, maximum + 1)],
                                        maximum, k, rng)
    deterministic["rnd"] = weighted_pick([0] + [1] * maximum, maximum, k, rng)
    bonus = {}
    if cfg["bonus"]:
        bmax = cfg.get("bmax", maximum)
        b_recent = Counter(r.get("b") for r in train[:n_window] if r.get("b") is not None)
        b_total = Counter(r.get("b") for r in train if r.get("b") is not None)
        bgap = {n: next((i for i, r in enumerate(train) if r.get("b") == n), len(train))
                for n in range(1, bmax + 1)}
        bzn = zscores([0] + [b_recent[n] for n in range(1, bmax + 1)], bmax)
        bza = zscores([0] + [b_total[n] for n in range(1, bmax + 1)], bmax)
        bzg = zscores([0] + [bgap[n] for n in range(1, bmax + 1)], bmax)
        for method in METHODS:
            if method == "pos":
                bonus[method] = max(1, min(bmax, math.floor(sum((r.get("b") or 0) for r in train[:n_window]) / n_window + 0.5)))
            elif method == "hot":
                bonus[method] = max(range(1, bmax + 1), key=lambda n: (b_recent[n] * 1000 + b_total[n], -n))
            elif method == "cold":
                bonus[method] = max(range(1, bmax + 1), key=lambda n: (bgap[n], -n))
            elif method == "all":
                bonus[method] = max(range(1, bmax + 1), key=lambda n: (b_total[n], -n))
            elif method == "bal":
                bonus[method] = max(range(1, bmax + 1),
                                    key=lambda n: (.4*bzn[n] + .3*bza[n] + .3*bzg[n], -n))
            elif method == "wr":
                bonus[method] = weighted_pick([0] + [b_recent[n] + 1 for n in range(1, bmax + 1)],
                                              bmax, 1, rng)[0]
            else:
                bonus[method] = rng.randint(1, bmax)
            # 6/55: số phụ không trùng số chính; 5/35 đặc biệt được phép trùng.
            if game == "655" and bonus[method] in deterministic[method]:
                candidates = [n for n in range(1, bmax + 1) if n not in deterministic[method]]
                bonus[method] = candidates[0] if candidates else bonus[method]
    return deterministic, bonus


def wilson(successes, total, z=1.959963984540054):
    if total <= 0:
        return [None, None]
    p = successes / total
    den = 1 + z*z/total
    center = (p + z*z/(2*total)) / den
    half = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / den
    return [round(max(0, center-half), 5), round(min(1, center+half), 5)]


def normal_cdf(x):
    return .5 * (1 + math.erf(x / math.sqrt(2)))


def paired_pvalue(diffs):
    n = len(diffs)
    if n < 2:
        return 1.0
    mean = statistics.mean(diffs)
    sd = statistics.stdev(diffs)
    if sd == 0:
        return 1.0 if mean == 0 else 0.0
    z = mean / (sd / math.sqrt(n))
    return max(0.0, min(1.0, 1 - normal_cdf(z)))  # one-sided: method > random


def bh_adjust(pvalues):
    ordered = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(ordered)
    adjusted = {}
    running = 1.0
    for rank in range(m, 0, -1):
        key, p = ordered[rank - 1]
        running = min(running, p * m / rank)
        adjusted[key] = min(1.0, running)
    return adjusted


def evaluate_game(game, rows):
    cfg = server.GAMES[game]
    maximum, k = cfg["maxn"], cfg["main"]
    count = max(0, len(rows) - MIN_TRAIN)
    records = []
    method_hits = {m: [] for m in METHODS}
    method_ge2 = {m: [] for m in METHODS}
    method_bonus = {m: [] for m in METHODS}
    random_hits, random_ge2 = [], []
    # ODS rows newest-first: target t sees only rows[t+1:] (strict walk-forward).
    for t in range(count):
        target = rows[t]
        train = rows[t + 1:]
        key = server.rowkey(game, target)
        seed = stable_seed("evaluation-v1", game, key)
        sets, bonuses = method_sets(game, train, DEFAULT_N, seed)
        actual = set(target["n"])
        rec = {"draw": key, "methods": {}, "random_control": {}}
        for method in METHODS:
            hit = len(set(sets[method]) & actual)
            method_hits[method].append(hit)
            method_ge2[method].append(1 if hit >= 2 else 0)
            b_hit = bool(cfg["bonus"] and bonuses.get(method) == target.get("b"))
            method_bonus[method].append(1 if b_hit else 0)
            rec["methods"][method] = {"hits": hit, "ge2": hit >= 2,
                                      "ge3": hit >= 3, "ge4": hit >= 4,
                                      "bonus_hit": b_hit}
        rng = random.Random(stable_seed("random-control-v1", game, key))
        sim_hits, sim_ge2 = [], 0
        for _ in range(RANDOM_REPS):
            ticket = weighted_pick([0] + [1] * maximum, maximum, k, rng)
            h = len(set(ticket) & actual)
            sim_hits.append(h)
            sim_ge2 += int(h >= 2)
        # Random control's per-draw mean and event rate are retained for paired comparison.
        random_hits.append(statistics.mean(sim_hits))
        random_ge2.append(sim_ge2 / RANDOM_REPS)
        rec["random_control"] = {"mean_hits": round(statistics.mean(sim_hits), 4),
                                 "ge2_rate": round(sim_ge2 / RANDOM_REPS, 4)}
        records.append(rec)

    metrics, pvalues = {}, {}
    for method in METHODS:
        hits = method_hits[method]
        ge2 = sum(method_ge2[method])
        p = ge2 / count if count else 0
        diffs = [method_ge2[method][i] - random_ge2[i] for i in range(count)]
        pvalue = paired_pvalue(diffs)
        pvalues[method] = pvalue
        diff_mean = statistics.mean(diffs) if diffs else 0.0
        diff_se = (statistics.stdev(diffs) / math.sqrt(count)) if count > 1 else 0.0
        metrics[method] = {
            "label": METHOD_LABELS[method],
            "ge2_rate_diff_vs_random": round(diff_mean, 5) if count else None,
            "paired_diff_ci95": [round(diff_mean - 1.96*diff_se, 5), round(diff_mean + 1.96*diff_se, 5)] if count else [None, None],
            "mean_hits": round(statistics.mean(hits), 4) if hits else None,
            "ge2": ge2, "ge2_rate": round(p, 5) if count else None,
            "ge2_ci95": wilson(ge2, count),
            "ge3": sum(x >= 3 for x in hits),
            "ge3_rate": round(sum(x >= 3 for x in hits) / count, 5) if count else None,
            "ge4": sum(x >= 4 for x in hits),
            "bonus_hits": sum(method_bonus[method]),
            "best": max(hits) if hits else None,
            "paired_p_vs_random_one_sided": round(pvalue, 7)
        }
    adjusted = bh_adjust(pvalues)
    for method in METHODS:
        metrics[method]["bh_q_value"] = round(adjusted[method], 7)
        metrics[method]["significant_after_bh_0_05"] = adjusted[method] < .05

    random_total = count * RANDOM_REPS
    random_event_total = round(sum(random_ge2) * RANDOM_REPS)
    random_all_hits = sum(random_hits)
    random_rate = sum(random_ge2) / count if count else 0
    segments = []
    # Evaluation order newest to oldest; blocks are clearly labeled by offset from newest target.
    for start in range(0, count, SEGMENT_SIZE):
        end = min(count, start + SEGMENT_SIZE)
        block = {}
        for method in METHODS:
            block_hits = method_hits[method][start:end]
            block = block or {"target_offset": [start + 1, end], "draws": end-start}
            block[method] = {
                "mean_hits": round(statistics.mean(block_hits), 4),
                "ge2_rate": round(sum(x >= 2 for x in block_hits) / len(block_hits), 5),
                "ge3_rate": round(sum(x >= 3 for x in block_hits) / len(block_hits), 5)
            }
        segments.append(block)
    return {
        "name": cfg["name"], "draws_evaluated": count, "minimum_training_draws": MIN_TRAIN,
        "window": DEFAULT_N, "random_simulations_per_target": RANDOM_REPS,
        "random_control": {
            "mean_hits_per_ticket": round(random_all_hits / count, 5) if count else None,
            "ge2_rate": round(random_rate, 5) if count else None,
            "ge2_ci95": wilson(random_event_total, random_total),
            "simulation_count": random_total
        },
        "methods": metrics, "segments": segments,
        "interpretation": "Walk-forward không dùng kỳ đích. q-value BH hiệu chỉnh 7 phép thử; CI Wilson cho tỷ lệ đạt >=2. Không có ý nghĩa dự báo tương lai."
    }



def source_signature():
    import hashlib
    h = hashlib.sha256()
    for game in ("655", "645", "535"):
        with open(server.ods_path(game), "rb") as f:
            h.update(game.encode("ascii"))
            h.update(f.read())
    return h.hexdigest()


def main():
    signature = source_signature()
    try:
        with open(OUT, encoding="utf-8") as f:
            previous = json.load(f)
        if previous.get("source_signature") == signature:
            print("Evaluation Engine: dữ liệu không đổi, bỏ qua.")
            return previous
    except (OSError, ValueError, TypeError):
        pass
    games = {}
    for game in ("655", "645", "535"):
        games[game] = evaluate_game(game, server.read_ods(game))
    payload = {
        "schema_version": 1, "source_signature": signature, "generated_at": server.now_vn().isoformat(timespec="seconds"),
        "method_order": list(METHODS), "method_labels": METHOD_LABELS,
        "games": games
    }
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, OUT)
    print("Evaluation Engine: đã ghi evaluation.json")
    return payload


if __name__ == "__main__":
    main()
