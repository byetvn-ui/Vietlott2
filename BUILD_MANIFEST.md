# Vietlott2 2.0 – biên bản đóng gói

## Nguồn nền
- Repository: https://github.com/byetvn-ui/Vietlott2
- Branch: `main`
- Commit nguồn đã đối chiếu: `83beb3e956f2779ebbfb1504f055a90fc0e39991`
- Gói Claude dùng làm bản vá giao diện/validator: `Vietlott2_2.0_Cai_Dat.zip`
- Không có thao tác commit, push hoặc upload lên GitHub.

## Phạm vi trong ZIP
- Giao diện 6 tab: Dò số, Dự đoán, Lab, Thống kê, Kết quả, Công cụ.
- Công cụ gom Lồng cầu, Lồng cầu hard, Bộ đếm trúng giải.
- Mặc định Gọn; Gọn/Đầy đủ lưu riêng theo trình duyệt bằng localStorage.
- Lab tách khỏi Dự đoán; giữ 5 vé dự đoán đã khóa và các dữ liệu lịch sử.
- Validator luật số cho 655/645/535; sửa metadata special range 655.
- Audit đồng bộ append-only, tự tạo khi workflow chạy.
- Workflow kiểm tra dữ liệu sau sync; validator luôn chạy, engine bị chặn khi validator thất bại, bước lưu/push chỉ chạy khi validator thành công.
- Lộ trình Vietlott2 2.0 và changelog được đóng gói cùng repo.

## Kiểm thử trong môi trường đóng gói
- Unit tests: 26/26 đạt.
- `python server.py --validate-data`: 535 = 1.026; 655 = 1.428; 645 = 1.592.
- Python compile: đạt.
- `node --check analytics.js`: đạt.
- 4 khối script nội tuyến trong HTML: kiểm tra cú pháp Node.js đạt.
- 108 HTML ID: không trùng.
- Điều hướng: đúng 6 tab.
- Workflow YAML parse: đạt; 6 `continue-on-error` gồm 5 chỉ thị gốc được giữ và 1 chỉ thị mới cho validator.
- ZIP integrity: kiểm tra CRC đạt.

## File được bảo toàn nguyên trạng từ snapshot nguồn
- `535.ods`, `645.ods`, `655.ods`
- `data.js`, `analytics.json`, `evaluation.json`, `winners.json`
- `predictions_log.jsonl`
- `analytics.py`, `evaluation.py`, `tests/test_winners.py`
- `BIGUPDATE_NOTES.md`, `analyze.py`, `icon.svg`, `thantai.png`

## Các file sửa/thêm
Sửa:
- `.github/workflows/update.yml`
- `server.py`
- `prediction.py`
- `index.html`
- `analytics.js`
- `manifest.json`
- `sw.js`
- `tests/test_data_integrity.py`
- `tests/test_engines.py`

Thêm:
- `tests/test_ui_structure.py`
- `tests/test_workflow_guards.py`
- `VIETLOTT2_2.0_ROADMAP.md`
- `UPGRADE_2.0_CHANGELOG.md`
- `BUILD_MANIFEST.md`

## Chưa tuyên bố hoàn tất
- Backtest trực tiếp danh mục 5 vé production so với danh mục random cùng ngân sách.
- Kiểm định sâu hơn Analytics và độ ổn định theo phân đoạn thời gian.
- Kiểm thử tương tác bằng trình duyệt thực và trên thiết bị iPhone/Android.
- Đối soát lịch sử từng kỳ với hash/nguồn chi tiết.
- Đo tải, hiệu năng và kiểm thử offline PWA trên thiết bị thật.

Đây là gói nâng cấp tích hợp và có kiểm thử mã nguồn; chưa phải bằng chứng rằng mọi hạng mục lộ trình 2.0 đã hoàn thành hoặc rằng dự đoán có lợi thế so với ngẫu nhiên.
