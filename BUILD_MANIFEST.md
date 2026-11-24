# Vietlott2 2.0 — biên bản bản nâng cấp tích hợp

## Nguồn và nguyên tắc bảo toàn
- Repository: https://github.com/byetvn-ui/Vietlott2
- GitHub `main` snapshot đối chiếu: `55dd2976696643407f54f2c9ba9ed35b41f25000` (2026-11-24).
- Gói nền cục bộ: `Vietlott2-phase1-AI-Analyst.zip` (SHA-256: `8bba88da34b850c1aa20f0e4e3477c5ddcfa6b20be0ea2d8b9120299c24cb2f2`).
- Không có thao tác commit, push hoặc upload lên GitHub.
- Không thay kiến trúc static HTML/JS + Python + GitHub Actions; không viết lại bằng React.
- Giữ nguyên 5 dòng `continue-on-error: true` trong `.github/workflows/update.yml`.

## Tính năng tích hợp
- 6 tab điều hướng, Lab riêng, nhóm Công cụ, chế độ Gọn/Đầy đủ.
- AI Assistant opt-in qua backend Anthropic; API key chỉ ở server, không có key thì AI hội thoại tắt.
- Validator dữ liệu cho 655/645/535 và cổng chặn engine khi ODS không hợp lệ.
- Analytics v2: cửa sổ tần suất, gap/cycle, cặp/bộ ba có kỳ vọng uniform, phân phối, anomaly cảnh báo; 535 phân tầng 13h/21h.
- Evaluation v2: 7 phương pháp walk-forward, random control một vé, danh mục 5 vé so với 120 danh mục random/kỳ cùng giới hạn overlap, CI và BH.
- Prediction: 5 vé, seed ổn định, khóa một lần, append-only evaluation; metadata special range 655 mới là `[1,55]`.
- Audit đồng bộ mới có fingerprint SHA-256 từng nguồn cho tối đa 10 kỳ mới nhất, agreement/conflict và lỗi.
- Metadata lỗi của event 655 `dd36d0cd9905cd58dfd2` được chú giải trong `prediction_metadata_audit.jsonl`; không sửa event dự đoán gốc hoặc 5 vé đã khóa.

## Dữ liệu giữ nguyên
- `535.ods`, `645.ods`, `655.ods`
- `data.js`, `winners.json`
- `predictions_log.jsonl` (giữ nguyên toàn bộ event gốc)
- Các tài nguyên giao diện/branding gốc.

## File thay đổi so với gói Phase 1
- `README.md`, `UPGRADE_2.0_CHANGELOG.md`, `VIETLOTT2_2.0_ROADMAP.md`, `BUILD_MANIFEST.md`
- `analytics.py`, `analytics.json`, `analytics.js`
- `evaluation.py`, `evaluation.json`
- `prediction.py`, `server.py`, `sw.js`
- `tests/test_data_integrity.py`, `tests/test_engines.py`, `tests/test_ui_structure.py`
- Thêm `prediction_metadata_audit.jsonl`, `tests/test_outputs.py`

## Kiểm thử và dữ liệu tại thời điểm đóng gói
- Unit/integration tests: `python -m unittest discover -v` → 37/37 đạt.
- `python server.py --validate-data`: 655 = 1.428 kỳ; 645 = 1.592 kỳ; 535 = 1.026 kỳ.
- Python compile: `server.py`, `analytics.py`, `evaluation.py`, `prediction.py`, `analyze.py` đạt.
- JavaScript syntax: `analytics.js`, `sw.js` và 2 script nội tuyến trong HTML đạt.
- HTML: 114 ID, không trùng; 6 tab được test cấu trúc.
- JSON/JSONL parse: `analytics.json`, `evaluation.json`, `predictions_log.jsonl`, `prediction_metadata_audit.jsonl` đạt.
- Workflow: giữ đúng 5 `continue-on-error: true` gốc.
- Backtest walk-forward: 655 = 1.368 kỳ; 645 = 1.532 kỳ; 535 = 966 kỳ.

### Kết quả danh mục 5 vé (mô tả hồi cứu)
| Game | Có ít nhất 1 vé đạt ≥2 số — ensemble | Random 5 vé | Chênh lệch |
|---|---:|---:|---:|
| 655 | 54,02% | 48,09% | +5,93 điểm % |
| 645 | 67,62% | 61,97% | +5,66 điểm % |
| 535 | 60,46% | 52,92% | +7,54 điểm % |

**Giới hạn quan trọng:** backtest danh mục dùng cùng 5 nhánh và giới hạn overlap production nhưng giảm pool tìm kiếm từ 320 xuống 64 ứng viên/nhánh để chạy được trên toàn lịch sử. Random baseline dùng cùng số vé và overlap cap. Đây là kết quả hồi cứu khám phá, không chứng minh lợi thế dự báo tương lai; không dùng để khẳng định xác suất jackpot tăng.

## Chưa thể xác nhận trong môi trường này
- Chưa chạy trợ lý Anthropic live vì không có API key được cấp; không phát sinh API token trong kiểm thử.
- Chưa có kiểm thử trình duyệt thực trên iPhone/Android, screen reader và offline PWA bằng thiết bị thật.
- Audit fingerprint áp dụng cho các lần đồng bộ mới; chưa có fingerprint nguồn cho toàn bộ lịch sử cũ.
