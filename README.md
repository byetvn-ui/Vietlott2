# Thống kê Vietlott 6/45 & 6/55

Web tĩnh (GitHub Pages) + script Python (chỉ thư viện chuẩn) tự lấy kết quả mỗi kỳ quay.

- `index.html` – giao diện: kết quả mới nhất, dò số, thống kê, dự đoán (giải trí), lịch sử. Có PWA + dark mode.
- `server.py` – `--sync-once` cập nhật 1 lần · `--build` tạo lại `data.js` · không tham số = chạy web local tại :8000.
- Nguồn: ketquadientoan.com (chính) + minhngoc.net.vn (dự phòng). Ghi kỳ mới khi >=2 nguồn khớp; nếu chỉ 1 nguồn thì chờ 45 phút sau giờ quay; nếu lệch nhau thì không ghi và báo lỗi.
- `655.ods`, `645.ods` – dữ liệu gốc (mới nhất ở hàng đầu). `data.js` được sinh từ 2 file này.
- `tests/` – test bộ đọc HTML. Chạy: `python3 -m unittest discover -s tests`.

Trang cá nhân phi thương mại, không phải trang chính thức của Vietlott. Xổ số là ngẫu nhiên.
