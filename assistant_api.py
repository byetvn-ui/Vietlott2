#!/usr/bin/env python3
"""Vietlott2 isolated AI API. Read-only: analytics.json + evaluation.json only."""
import json
import os
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "https://byetvn-ui.github.io").rstrip("/")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = os.environ.get("ANTHROPIC_MODEL", "")
API_URL = os.environ.get("ANTHROPIC_API_URL", "https://api.anthropic.com/v1/messages")
PORT = int(os.environ.get("PORT", "10000"))
WINDOW = 60
MAX_PER_WINDOW = 3
MAX_PER_DAY = 30
requests_by_ip = defaultdict(deque)

def load_json(name):
    try:
        with (BASE / name).open(encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None

def game_context(game):
    analytics = (load_json("analytics.json") or {}).get("games", {}).get(game)
    evaluation = (load_json("evaluation.json") or {}).get("games", {}).get(game)
    if not analytics and not evaluation:
        raise ValueError("Chưa có dữ liệu Analytics/Evaluation cho game này.")
    methods = {}
    for key, val in (evaluation or {}).get("methods", {}).items():
        methods[key] = {k: val.get(k) for k in (
            "label", "mean_hits", "ge2_rate", "ge2_ci95",
            "ge2_rate_diff_vs_random", "paired_diff_ci95",
            "bh_q_value", "significant_after_bh_0_05")}
    return {
        "game": game,
        "analytics": {
            "draw_count": (analytics or {}).get("draw_count"),
            "latest_draw": (analytics or {}).get("latest_draw"),
            "windows": {
                w: {
                    "draws": (analytics or {}).get("windows", {}).get(w, {}).get("draws"),
                    "frequency_top": (analytics or {}).get("windows", {}).get(w, {}).get("frequency", [])[:8],
                } for w in ("20", "60", "120", "all")
                if w in (analytics or {}).get("windows", {})
            },
            "gap_top": (analytics or {}).get("gap", [])[:8],
            "pairs_top": (analytics or {}).get("pairs", [])[:5],
            "triples_top": (analytics or {}).get("triples", [])[:3],
            "distribution": (analytics or {}).get("distribution"),
            "anomaly": (analytics or {}).get("anomaly"),
            "bonus": (analytics or {}).get("bonus"),
        } if analytics else None,
        "evaluation": {
            "draws_evaluated": (evaluation or {}).get("draws_evaluated"),
            "minimum_training_draws": (evaluation or {}).get("minimum_training_draws"),
            "random_control": (evaluation or {}).get("random_control"),
            "methods": methods,
            "segments_recent": (evaluation or {}).get("segments", [])[:3],
            "interpretation": (evaluation or {}).get("interpretation"),
        } if evaluation else None,
    }

def call_model(game, message):
    context = game_context(game)
    system = (
        "Bạn là AI Analyst của Vietlott2. Trả lời tiếng Việt, chính xác và súc tích. "
        "Chỉ kết luận những gì JSON dữ liệu hỗ trợ; nêu rõ khi thiếu dữ liệu. "
        "Phân biệt thống kê mô tả quá khứ với suy luận. Các kỳ quay độc lập; "
        "không khẳng định có thể dự đoán kết quả, không hứa tăng xác suất trúng, "
        "không khuyến khích mua vé. Không tự tạo số liệu hoặc số kỳ."
    )
    prompt = "DỮ LIỆU ĐƯỢC CUNG CẤP:\n" + json.dumps(context, ensure_ascii=False) + \
             "\n\nCÂU HỎI:\n" + message
    payload = json.dumps({
        "model": MODEL, "max_tokens": 800,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = Request(API_URL, payload, {
        "content-type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
    })
    with urlopen(req, timeout=40) as response:
        data = json.load(response)
    return "".join(x.get("text", "") for x in data.get("content", [])
                   if x.get("type") == "text").strip()

class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(raw)

    def cors_ok(self):
        origin = self.headers.get("Origin", "").rstrip("/")
        return origin == ALLOWED_ORIGIN

    def do_OPTIONS(self):
        if not self.cors_ok():
            return self.send_json(403, {"error": "Origin không được phép."})
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_GET(self):
        if not self.cors_ok():
            return self.send_json(403, {"error": "Origin không được phép."})
        if self.path.split("?")[0] != "/api/assistant/status":
            return self.send_json(404, {"error": "Không tìm thấy endpoint."})
        return self.send_json(200, {
            "available": bool(API_KEY and MODEL),
            "provider": "Anthropic" if API_KEY and MODEL else None,
        })

    def do_POST(self):
        if not self.cors_ok():
            return self.send_json(403, {"error": "Origin không được phép."})
        if self.path.split("?")[0] != "/api/assistant":
            return self.send_json(404, {"error": "Không tìm thấy endpoint."})
        if not API_KEY or not MODEL:
            return self.send_json(503, {"error": "AI backend chưa cấu hình API key/model."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 4096:
                return self.send_json(400, {"error": "Kích thước yêu cầu không hợp lệ."})
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            game = str(body.get("game", "655"))
            message = str(body.get("message", "")).strip()
            if game not in ("655", "645", "535") or not message or len(message) > 1200:
                return self.send_json(400, {"error": "Chọn game hợp lệ và nhập câu hỏi tối đa 1.200 ký tự."})
            ip = self.client_address[0]
            now = time.time()
            q = requests_by_ip[ip]
            while q and now - q[0] > 86400:
                q.popleft()
            recent = [t for t in q if now - t < WINDOW]
            if len(recent) >= MAX_PER_WINDOW or len(q) >= MAX_PER_DAY:
                return self.send_json(429, {"error": "Đã đạt giới hạn tạm thời. Thử lại sau."})
            q.append(now)
            answer = call_model(game, message)
            if not answer:
                return self.send_json(502, {"error": "AI không trả về nội dung. Thử lại sau."})
            return self.send_json(200, {"answer": answer})
        except ValueError as e:
            return self.send_json(400, {"error": str(e)})
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError):
            return self.send_json(502, {"error": "Không gọi được AI. Kiểm tra cấu hình máy chủ hoặc thử lại sau."})

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.client_address[0], fmt % args), flush=True)

if __name__ == "__main__":
    if not API_KEY or not MODEL:
        print("WARNING: set ANTHROPIC_API_KEY and ANTHROPIC_MODEL to enable chat.", flush=True)
    print("Vietlott2 AI API listening on port", PORT, flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
