#!/usr/bin/env python3
"""Analytics Engine: thống kê mô tả riêng cho từng game, không suy luận chéo."""
import json
import math
import os
import statistics
from collections import Counter
from datetime import datetime, timezone

import server

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "analytics.json")
WINDOWS = (20, 60, 120)


def _zscore(values):
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    var = sum((x - mean) ** 2 for x in values) / len(values)
    sd = math.sqrt(var)
    return (max(values) - mean) / sd if sd else 0.0


def _top(counter, limit=12):
    return [{"number": n, "count": c} for n, c in sorted(counter.items(), key=lambda x: (-x[1], x[0]))[:limit]]


def analyze_game(game, rows):
    cfg = server.GAMES[game]
    maximum, k = cfg["maxn"], cfg["main"]
    if not rows:
        return {"draw_count": 0, "windows": {}, "warning": "Không có dữ liệu."}
    result = {
        "name": cfg["name"], "draw_count": len(rows),
        "latest_draw": server.rowkey(game, rows[0]),
        "windows": {}, "gap": [], "pairs": [], "triples": [],
        "distribution": {}, "anomaly": {},
        "methodology": "Thống kê mô tả; tần suất/gap không làm tăng xác suất của kỳ tiếp theo."
    }
    for window in WINDOWS + (len(rows),):
        label = "all" if window == len(rows) else str(window)
        sample = rows[:min(window, len(rows))]
        freq = Counter(n for row in sample for n in row["n"])
        result["windows"][label] = {
            "draws": len(sample),
            "frequency": _top(freq, 15),
            "least_frequent": [{"number": n, "count": freq.get(n, 0)}
                               for n in sorted(range(1, maximum + 1), key=lambda n: (freq.get(n, 0), n))[:10]]
        }
    gaps = {}
    for n in range(1, maximum + 1):
        gaps[n] = next((i for i, row in enumerate(rows) if n in row["n"]), len(rows))
    result["gap"] = [{"number": n, "draws_absent": gaps[n]}
                     for n in sorted(gaps, key=lambda n: (-gaps[n], n))[:12]]

    # Chu kỳ = khoảng cách giữa các lần xuất hiện trong lịch sử; chỉ là mô tả hồi cứu.
    cycles = []
    for n in range(1, maximum + 1):
        positions = [i for i, row in enumerate(rows) if n in row["n"]]
        intervals = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
        if intervals:
            mean_cycle = statistics.mean(intervals)
            sd_cycle = statistics.pstdev(intervals) if len(intervals) > 1 else 0.0
            cycles.append({
                "number": n, "occurrences": len(positions), "current_gap": positions[0],
                "mean_interval": round(mean_cycle, 2), "median_interval": statistics.median(intervals),
                "interval_sd": round(sd_cycle, 2),
                "interval_cv": round(sd_cycle / mean_cycle, 3) if mean_cycle else None
            })
    result["cycles"] = sorted(cycles, key=lambda x: (x["interval_cv"] if x["interval_cv"] is not None else 9, x["number"]))[:12]

    pair_counts, triple_counts = Counter(), Counter()
    for row in rows:
        nums = sorted(row["n"])
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                pair_counts[(nums[i], nums[j])] += 1
                for q in range(j + 1, len(nums)):
                    triple_counts[(nums[i], nums[j], nums[q])] += 1
    result["pairs"] = [{"numbers": list(ns), "count": c}
                       for ns, c in pair_counts.most_common(15)]
    result["triples"] = [{"numbers": list(ns), "count": c}
                         for ns, c in triple_counts.most_common(10)]

    sums = [sum(r["n"]) for r in rows]
    odd = [sum(n % 2 for n in r["n"]) for r in rows]
    low = [sum(n <= maximum // 2 for n in r["n"]) for r in rows]
    result["distribution"] = {
        "sum": {"min": min(sums), "max": max(sums), "mean": round(statistics.mean(sums), 2),
                "median": statistics.median(sums)},
        "odd_count": _top(Counter(odd), k + 1),
        "low_half_count": _top(Counter(low), k + 1),
        "sample_size": len(rows)
    }
    recent = rows[:min(60, len(rows))]
    recent_freq = Counter(n for r in recent for n in r["n"])
    # Chuẩn hoá theo kỳ: số lần kỳ vọng = draws*k/max; z-score dùng xấp xỉ nhị thức.
    expected = len(recent) * k / maximum
    variance = len(recent) * (k / maximum) * (1 - k / maximum)
    sd = math.sqrt(variance) if variance > 0 else 1
    deviations = [(n, (recent_freq[n] - expected) / sd) for n in range(1, maximum + 1)]
    peak = max((abs(z) for _, z in deviations), default=0)
    result["anomaly"] = {
        "window_draws": len(recent), "expected_count_per_number": round(expected, 3),
        "max_abs_z": round(peak, 3),
        "level": "cao" if peak >= 3.5 else "vừa" if peak >= 2.5 else "thấp",
        "largest_deviations": [{"number": n, "z": round(z, 3)}
                               for n, z in sorted(deviations, key=lambda x: -abs(x[1]))[:8]],
        "caveat": "Cảnh báo mô tả, chưa hiệu chỉnh đa kiểm định; không phải bằng chứng có gian lận."
    }
    if cfg["bonus"]:
        bmax = cfg.get("bmax", maximum)
        bc = Counter(r["b"] for r in rows if r.get("b") is not None)
        bonus_gap = {n: next((i for i, r in enumerate(rows) if r.get("b") == n), len(rows))
                     for n in range(1, bmax + 1)}
        bonus_cycles = []
        for n in range(1, bmax + 1):
            positions = [i for i, r in enumerate(rows) if r.get("b") == n]
            intervals = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
            if intervals:
                mean_cycle = statistics.mean(intervals)
                sd_cycle = statistics.pstdev(intervals) if len(intervals) > 1 else 0.0
                bonus_cycles.append({"number": n, "occurrences": len(positions),
                                     "current_gap": positions[0], "mean_interval": round(mean_cycle, 2),
                                     "interval_cv": round(sd_cycle/mean_cycle, 3) if mean_cycle else None})
        result["bonus"] = {
            "range": [1, bmax], "frequency": _top(bc, bmax),
            "gap": [{"number": n, "draws_absent": bonus_gap[n]}
                    for n in sorted(bonus_gap, key=lambda n: (-bonus_gap[n], n))],
            "cycles": sorted(bonus_cycles, key=lambda x: (x["interval_cv"] if x["interval_cv"] is not None else 9, x["number"]))[:bmax]
        }
    if game == "535":
        result["draws_by_hour"] = {
            str(hour): sum(1 for r in rows if r.get("h") == hour) for hour in (13, 21)
        }
    return result



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
            print("Analytics Engine: dữ liệu không đổi, bỏ qua.")
            return previous
    except (OSError, ValueError, TypeError):
        pass
    games = {}
    for game in ("655", "645", "535"):
        games[game] = analyze_game(game, server.read_ods(game))
    payload = {
        "schema_version": 1, "source_signature": signature,
        "generated_at": server.now_vn().isoformat(timespec="seconds"),
        "games": games
    }
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, OUT)
    print("Analytics Engine: đã ghi analytics.json")
    return payload


if __name__ == "__main__":
    main()
