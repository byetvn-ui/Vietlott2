# Big Update — ghi chú bàn giao

## Nền repo

- Repository: `byetvn-ui/Vietlott2`
- Branch: `main`
- Commit nguồn được xác minh: `12683a907425325e7171ac10d0ca2a09b112b604`
- Gói nguồn `Vietlott2-main(2).zip` có blob hash trùng các tệp mã nguồn và dữ liệu đã kiểm tra trên commit này.
- Các tệp dữ liệu ODS, `data.js`, `winners.json`, `server.py`, `analyze.py`, mascot và icon được giữ nguyên.

## Tệp thêm mới

- `analytics.py`, `analytics.json`
- `evaluation.py`, `evaluation.json`
- `prediction.py`, `predictions_log.jsonl`
- `analytics.js`
- `tests/test_engines.py`

## Tệp tích hợp/chỉnh sửa

- `index.html`: thêm khu AI Prediction Lab trong tab Dự đoán; giữ bố cục và tính năng hiện có.
- `sw.js`: nâng cache lên `vietlott-v3`, thêm `analytics.js`.
- `.github/workflows/update.yml`: giữ luồng test → sync → AI; thêm Analytics, Evaluation, Prediction; mở cron trước giờ quay để có thời gian khóa vé.
- `README.md`: tài liệu hóa engine, phương pháp, kiểm định và Prediction History.
- `.gitignore`: bỏ qua tệp tạm `*.tmp`.

## Kiểm tra thực hiện trước khi đóng gói

- `python3 -m unittest discover -s tests -t .` — **18 tests passed**.
- `analytics.py` chạy thành công trên ba bộ ODS; lần chạy lặp nhận diện dữ liệu không đổi và bỏ qua.
- `evaluation.py` chạy thành công trên ba bộ ODS; lần chạy lặp nhận diện dữ liệu không đổi và bỏ qua.
- `prediction.py` được kiểm tra tích hợp với đồng hồ/dữ liệu giả: khóa 3 game, 5 vé/game, lần chạy thứ hai không tạo bản ghi trùng; khi có kết quả, engine thêm event đối chiếu mà không sửa event dự đoán.
- `node --check analytics.js` — passed.
- JavaScript inline trong `index.html` — syntax check passed.
- YAML workflow — parse passed.

## Chưa thể xác nhận từ gói ZIP

GitHub Actions chưa được chạy trên branch `main` bởi gói này không tự commit/push. Sau khi người dùng tải ZIP lên repo, cần chạy thủ công workflow **Cập nhật kết quả** một lần và xác nhận run xanh. Gói không tuyên bố workflow GitHub đã xanh khi chưa thực thi trên GitHub.
