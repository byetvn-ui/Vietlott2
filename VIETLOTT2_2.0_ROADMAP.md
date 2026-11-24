# Vietlott2 2.0 – kế hoạch nâng cấp và tiêu chuẩn nghiệm thu

## Phạm vi
Hoàn thiện đồng đều Power 6/55, Mega 6/45 và Lotto 5/35. Không thay kiến trúc static site + Python + GitHub Actions; không xóa dữ liệu ODS, `data.js`, `analytics.json`, `evaluation.json`, `predictions_log.jsonl` hoặc lịch sử vé.

## Thiết kế giao diện đã chốt
- 6 tab: Dò số, Dự đoán, Lab, Thống kê, Kết quả, Công cụ.
- Công cụ gom Lồng cầu, Lồng cầu hard và Bộ đếm trúng giải.
- Mặc định Gọn; lựa chọn Gọn/Đầy đủ được lưu theo trình duyệt/thiết bị bằng localStorage.
- Giữ đỏ/vàng thương hiệu; giảm bóng, viền và card lặp; Lab tách khỏi Dự đoán.
- Các bảng phụ, backtest và giải thích dài thu gọn; dữ liệu cốt lõi không bị xóa.

## Data Engine — đã triển khai
- Dùng validator chung cho ba luật game.
- 655: số phụ 1–55 và không trùng 6 số chính.
- 645: đúng 6 số chính, không có số phụ.
- 535: 5 số chính 1–35; số đặc biệt 1–12, được phép trùng số chính; giờ quay 13h/21h.
- Kiểm tra ngày, khóa kỳ, thứ tự, trùng kỳ và dữ liệu ODS.
- Chạy cổng `server.py --validate-data` sau sync, trước khi tạo báo cáo mới.
- Audit đồng bộ mới ghi tên nguồn, timestamp, fingerprint SHA-256 từng nguồn cho tối đa 10 kỳ gần nhất, đồng thuận/mâu thuẫn và lỗi. Chưa tái dựng audit cho toàn bộ lịch sử cũ.

## Analytics Engine — đã triển khai
- Tách thống kê số chính và số phụ/đặc biệt.
- 535 phân tầng theo giờ 13h/21h.
- Cặp/bộ ba có mốc kỳ vọng theo mô hình rút đều; z-score xấp xỉ chỉ dùng sàng lọc mô tả, không phải tín hiệu dự báo.
- 535 phân tầng tần suất số chính/số đặc biệt theo 13h và 21h.
- Kiểm thử schema, tính xác định và tính toàn vẹn output.

## Evaluation Engine — đã triển khai với giới hạn được công bố
- Backtest walk-forward, không lookahead.
- So sánh danh mục 5 vé dùng 5 nhánh production với 120 danh mục random mỗi kỳ, cùng số vé và giới hạn overlap.
- Báo cáo tỷ lệ có ít nhất một vé ≥2 số, tỷ lệ vé ≥2, số trúng trung bình, best-ticket hits, CI, p-value, BH và phân đoạn.
- Giới hạn: backtest dùng pool 64 ứng viên/nhánh thay vì 320 ở production để kiểm soát thời gian; đây không phải tái tạo bit-for-bit toàn bộ ngân sách tìm kiếm production.
- Không tuyên bố có lợi thế nếu hiệu ứng không ổn định và không tái lập.

## Prediction Engine — đã triển khai
- Lưu phiên bản thuật toán, seed, tham số, signature dữ liệu và target draw.
- Sửa metadata miền số phụ cho dự đoán mới; giữ event lịch sử bất biến và chú giải metadata sai cũ bằng audit append-only.
- Kiểm soát overlap/coverage nhưng không tuyên bố tăng xác suất trúng.
- Backtest đúng logic tạo 5 vé production.

## UI/PWA — cấu trúc và cache đã triển khai; kiểm thử thiết bị còn lại
- Kiểm thử mobile-first, bàn phím, screen reader, reduced motion.
- Kiểm thử cache, offline fallback và nâng phiên bản service worker.
- Trạng thái dữ liệu phải phân biệt xác nhận, chờ nguồn, stale và lỗi; không biến thiếu dữ liệu thành 0.

## Release gate — đang nghiệm thu
- Unit + integration + regression tests.
- Validate ODS trước và sau sync.
- Parse JSON/JSONL và kiểm tra schema.
- Kiểm thử workflow và đường khôi phục khi nguồn mâu thuẫn.
- Gói ZIP đầy đủ, kèm manifest thay đổi, kết quả test và checksum.

## Tiêu chí phát hành
Không còn lỗi P0/P1 chưa xử lý; mọi thay đổi dữ liệu có thể truy vết; các phép so sánh thống kê tái lập được; dự đoán cũ không bị sửa; cả ba game đều qua cùng bộ tiêu chuẩn. Chất lượng sản phẩm có thể cải thiện, nhưng không thể đảm bảo dự đoán xổ số chính xác hơn ngẫu nhiên.

## Trạng thái trong bản ZIP này
- Đã thêm validator dùng chung và CLI kiểm tra ODS.
- Đã thêm cổng kiểm tra sau sync trong workflow; nếu dữ liệu không hợp lệ thì chặn các engine và chặn bước lưu/push.
- Đã sửa metadata special range cho 655.
- Đã triển khai cấu trúc điều hướng 6 tab, Lab riêng, Công cụ gom nhóm và Gọn/Đầy đủ.
- Analytics/Evaluation 2.0 đầy đủ, audit nguồn chi tiết và kiểm thử trình duyệt vẫn là các hạng mục tiếp theo, không được đánh dấu hoàn thành giả.
