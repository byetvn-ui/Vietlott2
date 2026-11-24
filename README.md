# Vietlott2 — dữ liệu, thống kê, kiểm định và dự đoán tham khảo

Website tĩnh chạy trên GitHub Pages, bot Python chạy qua GitHub Actions. Dự án xử lý riêng ba game:

- **Power 6/55** — 6 số chính và 1 số phụ; số phụ không trùng 6 số chính.
- **Mega 6/45** — 6 số chính.
- **Lotto 5/35** — 5 số chính và 1 số đặc biệt trong 1–12; số đặc biệt có thể trùng số chính; quay 13h và 21h mỗi ngày.

Đây là dự án cá nhân, không phải website chính thức của Vietlott. Dự đoán chỉ mang tính tham khảo/giải trí.

## Các thành phần

### Thành phần sẵn có được giữ lại

- `index.html` — giao diện dò vé, thống kê, lịch sử, các game, giao diện sáng/tối/tự động, hiệu ứng bi và Thần Tài, số người trúng giải, jackpot, cảnh báo dữ liệu cũ và backtest cũ.
- `server.py` — đồng bộ kết quả từ nhiều nguồn, đối chiếu nguồn, cập nhật ODS, sinh `data.js`, lấy số người trúng, bổ sung jackpot và gửi Telegram.
- `analyze.py` — nhận xét AI tùy chọn; cần secret `ANTHROPIC_API_KEY`.
- `sw.js` — service worker; cache đã được nâng lên `vietlott-v3` để tránh giữ JavaScript cũ.
- `655.ods`, `645.ods`, `535.ods`, `data.js`, `winners.json` — dữ liệu nguồn/bot quản lý; không sửa tay.

### Engine mới

- `analytics.py` → `analytics.json`: tần suất theo cửa sổ 20/60/120/toàn bộ kỳ; số lâu chưa xuất hiện; khoảng cách/chu kỳ giữa các lần xuất hiện; cặp/bộ ba; phân phối tổng, chẵn/lẻ, nửa thấp/cao; cảnh báo độ lệch mô tả; thống kê số phụ/đặc biệt riêng. 5/35 còn tách số kỳ theo 13h/21h.
- `evaluation.py` → `evaluation.json`: đánh giá 7 phương pháp bằng walk-forward nghiêm ngặt; mô phỏng đối chứng ngẫu nhiên seed cố định; khoảng tin cậy 95%; hiệu chỉnh Benjamini–Hochberg cho 7 phép thử; báo cáo các đoạn 100 kỳ.
- `prediction.py` → `predictions_log.jsonl`: sinh 5 vé theo ensemble có kiểm soát giao nhau; khóa bản ghi trước giờ quay; sau khi kết quả xuất hiện, thêm một event đối chiếu mới. Bản ghi dự đoán cũ không bị sửa.
- `analytics.js`: khu **AI Prediction Lab** trên website. Chỉ tải JSON do Actions tạo; không chạy backtest hay mô phỏng nặng trên điện thoại.
- `tests/test_engines.py`: kiểm tra quy tắc riêng game, tính tái lập, walk-forward, BH, độ đa dạng và lịch sử dự đoán.

## Bảy phương pháp được kiểm toán

| Mã | Phương pháp | Vai trò/giới hạn |
|---|---|---|
| `pos` | Trung bình theo vị trí đã sắp xếp | Giữ làm đối chứng nghiên cứu; trung bình vị trí không có cơ sở xác suất rõ ràng |
| `hot` | Tần suất gần đây | Mô tả quá khứ, không chứng minh số nóng tiếp tục xuất hiện |
| `cold` | Khoảng vắng mặt | Không phải số “đến hạn”; các kỳ độc lập |
| `all` | Tần suất toàn bộ lịch sử | Dễ trùng lặp với `hot` |
| `bal` | 40% gần đây + 30% toàn thời gian + 30% khoảng vắng | Điểm tổng hợp có thể cộng gộp tín hiệu tương quan |
| `wr` | Ngẫu nhiên có trọng số theo tần suất gần đây | Không có bằng chứng làm tăng xác suất |
| `rnd` | Ngẫu nhiên thuần | Đối chứng cơ bản |

Bảy phương pháp được giữ để có thể so sánh công bằng; không phương pháp nào được mặc định là có lợi thế.

## Quy tắc kiểm định

1. **Walk-forward:** ODS lưu mới nhất ở đầu. Khi đánh giá mục tiêu tại vị trí `t`, engine chỉ truyền `rows[t+1:]` (các kỳ cũ hơn) vào bộ sinh số. Kỳ đích không tham gia tính đặc trưng.
2. **Không tối ưu trên kỳ đích:** cửa sổ mặc định 20 kỳ và công thức được cố định trước khi đánh giá; không dùng kết quả mục tiêu để điều chỉnh tham số.
3. **Đối chứng ngẫu nhiên:** 120 vé ngẫu nhiên có seed ổn định cho mỗi kỳ mục tiêu, tái lập được.
4. **Khoảng tin cậy:** CI 95% Wilson cho tỷ lệ đạt ít nhất 2 số; CI cho đối chứng ngẫu nhiên và CI chênh lệch ghép cặp so với random được báo riêng.
5. **Nhiều phép thử:** p-value một phía của chênh lệch ghép cặp tỷ lệ đạt ≥2 so với đối chứng được hiệu chỉnh Benjamini–Hochberg trên 7 phương pháp. q-value không phải bằng chứng dự báo.
6. **Ổn định theo thời gian:** kết quả được chia đoạn 100 kỳ mục tiêu, tính từ kỳ đích gần nhất.
7. **Tách game:** 6/55, 6/45 và 5/35 được phân tích riêng. Số phụ/đặc biệt được chấm riêng; 5/35 dùng miền 1–12 và được phép trùng số chính.

## Prediction History — lịch sử đã khóa

- Workflow gọi `prediction.py` sau bước đồng bộ.
- Engine tìm kỳ quay kế tiếp còn ở tương lai theo lịch riêng từng game. Nếu giờ quay đã qua, engine không tạo dự đoán hồi tố cho kỳ đó.
- Mỗi game/kỳ mục tiêu chỉ được ghi một event `prediction`, gồm thời điểm tạo, kỳ mục tiêu, kỳ dữ liệu nguồn mới nhất, tham số, seed, phiên bản thuật toán và 5 vé.
- Khi ODS có kết quả đúng kỳ mục tiêu, engine thêm event `evaluation` tham chiếu `prediction_id`. Không sửa event `prediction` cũ.
- File `predictions_log.jsonl` là JSON Lines: mỗi dòng là một event độc lập, phù hợp với cách ghi nối tiếp.

Năm vé được tạo theo năm nhánh (ngẫu nhiên thuần, ngẫu nhiên có trọng số, tần suất ngắn hạn, ensemble tổng hợp, phủ số). Engine chọn ứng viên để giới hạn giao nhau giữa các vé: tối đa 3 số chung cho game 6 số và tối đa 2 số chung cho 5/35. Nếu không tìm được ứng viên thỏa giới hạn trong pool, engine có bước nới điều kiện dự phòng. Đa dạng hóa tăng độ phủ giữa các vé, **không tăng xác suất của một vé**.

## GitHub Actions

Workflow `.github/workflows/update.yml` giữ luồng hiện có và thêm ba bước engine:

1. Unit tests.
2. Đồng bộ kết quả (`server.py --sync-once`).
3. Phân tích AI tùy chọn (`analyze.py`).
4. Analytics Engine.
5. Evaluation Engine.
6. Prediction Engine (đối chiếu các dự đoán đã khóa và khóa kỳ tương lai).
7. Commit các dữ liệu bot sinh nếu có thay đổi.

Lịch chạy hiện tại vẫn theo cron trong workflow. Có thể chạy thủ công bằng **Actions → Cập nhật kết quả → Run workflow**. Người dùng chỉ cần thao tác trên GitHub bằng iPhone; không cần chạy Python tại máy.

## Chạy kiểm thử cục bộ

```bash
python3 -m unittest discover -s tests -t .
```

Các engine chỉ dùng thư viện chuẩn Python và bộ đọc ODS sẵn có trong `server.py`.

## Lệnh engine

```bash
python3 analytics.py
python3 evaluation.py
python3 prediction.py
```

`analytics.json` và `evaluation.json` lưu `source_signature`; nếu ODS không đổi thì engine bỏ qua tính toán để tránh tạo commit mới không cần thiết mỗi 5 phút. `predictions_log.jsonl` chỉ thêm event khi có kỳ mục tiêu mới hoặc kết quả mới để chấm.

## Cách hiểu kết quả

- Tần suất, cặp/bộ ba, khoảng vắng mặt và mức độ lệch là thống kê mô tả trên mẫu lịch sử.
- Cảnh báo bất thường là cờ sàng lọc mô tả, không phải bằng chứng có can thiệp hay gian lận.
- Backtest lịch sử không chứng minh khả năng dự đoán tương lai; mọi tổ hợp hợp lệ của cùng game có xác suất cơ bản như nhau.
- Chênh lệch nhỏ giữa phương pháp và đối chứng có thể do nhiễu lấy mẫu. Cần xem CI, q-value và tính ổn định qua các đoạn; không chỉ nhìn một đoạn có kết quả cao.
