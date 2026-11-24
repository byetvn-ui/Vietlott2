# Vietlott2 2.0 – changelog của gói nâng cấp

## Nền mã nguồn
- Đối chiếu bản ZIP đầu vào `Vietlott2-fixed-push-retry.zip` với commit GitHub `83beb3e956f2779ebbfb1504f055a90fc0e39991`.
- Các blob SHA của 13 file lõi (giao diện, engines, tests, workflow, manifest, service worker và README) trùng với `main` tại thời điểm lấy snapshot.
- Không ghi bất kỳ thay đổi nào lên GitHub.

## File đã sửa
- `.github/workflows/update.yml`: thêm bước `server.py --validate-data` sau đồng bộ; validator luôn chạy cả khi sync có lỗi/partial update; nếu validator lỗi thì chặn Analytics, Evaluation, Prediction và bước lưu/push; bước lưu chỉ chạy khi validator thành công; giữ nguyên đủ 5 chỉ thị `continue-on-error` gốc, thêm 1 chỉ thị cho validator và giữ cơ chế push retry. Nếu validator lỗi, các engine và bước lưu/push bị chặn.
- `server.py`: validator dùng chung cho luật ba game; xác nhận ngày; kiểm tra toàn bộ ODS; CLI `--validate-data`; ghi nhật ký đồng bộ append-only `sync_audit.jsonl` với nguồn, số bản ghi, lỗi, trạng thái và số kỳ thêm; bỏ qua sự kiện lặp để tránh commit mỗi lần polling 5 phút.
- `prediction.py`: xác định miền số phụ Power 6/55 bằng fallback `maxn=55`; tối ưu tìm gap bằng một lượt quét lịch sử.
- `analytics.py`: thêm kỳ vọng cặp/bộ ba theo mô hình rút đều, z xấp xỉ có cảnh báo đa kiểm định; tách thống kê 535 theo 13h/21h; tối ưu gap.
- `evaluation.py`: thêm backtest walk-forward cho danh mục 5 vé production so với 120 danh mục random/kỳ có cùng giới hạn overlap; ghi nhận tỷ lệ có ít nhất một vé đạt ≥2 số, tỷ lệ vé ≥2, trung bình số trùng và best-ticket hits. Backtest dùng pool 64 ứng viên/nhánh thay vì 320 ở production để giảm thời gian chạy; được ghi rõ trong output.
- `server.py`: audit đồng bộ thêm fingerprint SHA-256 theo nguồn cho tối đa 10 kỳ mới nhất, đánh dấu đồng thuận/mâu thuẫn.
- `analytics.js`: hiển thị baseline cặp/bộ ba, phân tầng 535 và so sánh danh mục 5 vé với random portfolio.
- `sw.js`: nâng cache lên `vietlott-v7`.
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

## Giới hạn còn lại
- Backtest 5 vé tái sử dụng 5 nhánh và giới hạn overlap production nhưng giảm pool tìm kiếm từ 320 xuống 64 ứng viên/nhánh; không phải mô phỏng bit-for-bit của tham số production.
- Audit fingerprint chỉ bắt đầu có hiệu lực ở các lần đồng bộ mới; chưa có hash nguồn lịch sử cho các kỳ trước đó.
- Kiểm thử trình duyệt thực, accessibility bằng screen reader và kiểm thử offline PWA trên iPhone/Android cần thiết bị thật.
- Trợ lý Anthropic chưa được gọi live vì không có API key được cấp trong môi trường kiểm thử.
