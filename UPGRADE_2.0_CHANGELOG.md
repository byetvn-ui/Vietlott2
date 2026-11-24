# Vietlott2 2.0 – changelog của gói nâng cấp

## Nền mã nguồn
- Đối chiếu bản ZIP đầu vào `Vietlott2-fixed-push-retry.zip` với commit GitHub `83beb3e956f2779ebbfb1504f055a90fc0e39991`.
- Các blob SHA của 13 file lõi (giao diện, engines, tests, workflow, manifest, service worker và README) trùng với `main` tại thời điểm lấy snapshot.
- Không ghi bất kỳ thay đổi nào lên GitHub.

## File đã sửa
- `.github/workflows/update.yml`: thêm bước `server.py --validate-data` sau đồng bộ; validator luôn chạy cả khi sync có lỗi/partial update; nếu validator lỗi thì chặn Analytics, Evaluation, Prediction và bước lưu/push; bước lưu chỉ chạy khi validator thành công; giữ nguyên đủ 5 chỉ thị `continue-on-error` gốc, thêm 1 chỉ thị cho validator và giữ cơ chế push retry. Nếu validator lỗi, các engine và bước lưu/push bị chặn.
- `server.py`: validator dùng chung cho luật ba game; xác nhận ngày; kiểm tra toàn bộ ODS; CLI `--validate-data`; ghi nhật ký đồng bộ append-only `sync_audit.jsonl` với nguồn, số bản ghi, lỗi, trạng thái và số kỳ thêm; bỏ qua sự kiện lặp để tránh commit mỗi lần polling 5 phút.
- `prediction.py`: sửa metadata miền số phụ Power 6/55, dùng fallback `maxn=55` thay vì 0.
- `index.html`: chuyển sang 6 tab; tách Lab; gom 3 công cụ vào Công cụ; mặc định Gọn; lưu lựa chọn density trên từng trình duyệt; thu gọn backtest, Analytics, Evaluation, lịch sử và Jackpot; gộp biểu đồ/bảng Jackpot; giảm hiệu ứng card và cải thiện responsive.
- `analytics.js`: đồng bộ 5 vé đã khóa lên trang Dự đoán; hiển thị lịch sử dự đoán trong Lab.
- `manifest.json`: cập nhật tên và mô tả PWA cho cả ba game.
- `sw.js`: tăng cache version để trình duyệt nhận giao diện mới.
- `tests/test_data_integrity.py`: test luật số phụ 655, validator ODS, parser nguồn và audit append-only.
- `tests/test_engines.py`: kiểm tra metadata `special_range` của cả ba game trong event dự đoán thực tế.

## File thêm
- `tests/test_ui_structure.py`: kiểm tra 6 tab, Lab độc lập, gom công cụ và tùy chọn Gọn.
- `tests/test_workflow_guards.py`: kiểm tra lỗi validator chặn engine và bước lưu/push.
- `sync_audit.jsonl` được tạo khi workflow đồng bộ lần đầu; không thêm bản ghi giả vào ZIP.
- `VIETLOTT2_2.0_ROADMAP.md`: phạm vi, lộ trình, tiêu chí nghiệm thu và các hạng mục chưa được đánh dấu hoàn thành.

## File dữ liệu cố ý giữ nguyên
- `535.ods`, `645.ods`, `655.ods`
- `data.js`, `analytics.json`, `evaluation.json`, `winners.json`
- `predictions_log.jsonl`

## Kiểm thử
- Unit tests: `python -m unittest discover -v` → **26/26 đạt**.
- `python server.py --validate-data`: xác nhận ODS cả ba game.
- `python -m py_compile server.py prediction.py analytics.py evaluation.py`.
- `node --check analytics.js`.
- Parse HTML, kiểm tra ID duy nhất và 6 tab.
- Parse YAML workflow; xác nhận đúng 5 `continue-on-error: true`.
- Kiểm thử trình duyệt tự động chưa hoàn tất vì môi trường chạy chặn truy cập cả localhost và `file://`; không coi đó là test đạt.

## Phạm vi chưa được tuyên bố hoàn tất
Evaluation Engine vẫn cần backtest trực tiếp logic `build_five()` với danh mục random tương đương; Analytics cần kiểm tra sâu hơn về hiệu chỉnh kỳ vọng; cần kiểm thử giao diện trên thiết bị thật; audit nguồn lịch sử cần thêm bước đối soát lại các kỳ cũ. Xem `VIETLOTT2_2.0_ROADMAP.md`.
