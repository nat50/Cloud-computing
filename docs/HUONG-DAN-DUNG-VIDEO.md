# Hướng dẫn dựng video demo từ 6 file đã quay

Video thành phẩm dài khoảng **8–9 phút**, gồm 8 phần theo đúng thứ tự dưới đây. Làm lần lượt từ trên xuống. Mỗi phần ghi rõ: **cắt đoạn nào – tua bao nhiêu – chữ gì hiện trên màn hình – nói gì**. Phần "Lời thuyết minh" dùng luôn làm lời thuyết trình nếu trình bày trực tiếp.

---

## Bước chuẩn bị

1. **Phần mềm:** CapCut bản máy tính (miễn phí). Chỉ cần các thao tác: *Tách* (`Ctrl + B`), *Tốc độ* (Speed), *Văn bản* (Text), *Phụ đề tự động* (Auto captions), *Làm mờ* (Blur/Mosaic), *Phóng to bằng keyframe*, *Đóng băng khung hình* (Freeze).
2. Tạo project mới tỉ lệ **16:9**, kéo cả 6 file vào thư viện. File gốc 2560×1380 rộng hơn 16:9 một chút → để chế độ *Fit*, chấp nhận viền đen mỏng trên/dưới.
3. Kéo thêm vào thư viện: **ảnh slide kiến trúc** (slide 4) và **3 ảnh** bất kỳ trong `F:\Cloud-computing\reports\figures\boxes\`.
4. Màn hình quay chia nhiều cửa sổ nên chữ rất nhỏ. Mỗi khi lời nói nhắc tới một biểu đồ hay một dòng terminal, **phóng to vào vùng đó (Scale 160–200%) trong 3–5 giây rồi thu về**. Trong hướng dẫn ghi là **[Zoom: …]**.
5. Mốc `mm:ss` là thời gian **trong file gốc**, sai số khoảng ±15 giây → kéo thanh thời gian quanh mốc để tìm đúng khoảnh khắc.

**Bố cục màn hình trong các file (để biết chỗ cần zoom):**
- **Trái trên:** terminal `kubectl get pods -n yolo -w` – danh sách pod và trạng thái (`Pending` → `ContainerCreating` → `Running` → `Terminating`).
- **Trái dưới:** terminal gõ lệnh demo.
- **Phải:** Dashboard *YOLO26 Stream Pipeline* gồm 6 biểu đồ: *Backlog* (trên trái), *Worker pods running* (trên phải), *Oldest unacked message age* (giữa trái), *Messages/s: published vs acked* (giữa phải), *Worker CPU* (dưới trái), *Dead-lettered messages* (dưới phải).

**Kiểu chữ dùng thống nhất cho cả video:**
- **Tiêu đề phần:** góc trên trái, nền xanh đậm hơi trong suốt, chữ trắng in đậm, giữ suốt phần đó.
- **Huy hiệu tốc độ:** góc trên phải, chữ vàng (`x16`, `x8`…), chỉ hiện ở đoạn tua.
- **Nhãn chú thích:** chữ trắng trên nền đen mờ, kèm mũi tên hoặc khung đỏ chỉ vào chỗ cần nhìn.

---

## Bản đồ video

| # | Phần | Lấy từ file | Thời lượng sau dựng |
|---|---|---|---|
| 0 | Mở đầu & kiến trúc | ảnh slide | 0:30 |
| 1 | Hạ tầng trên Console | cảnh 1 (đầu file) | 0:30 |
| 2 | Tải đột biến & tự co giãn | cảnh 1 (phần còn lại) + cảnh 1.2 | 2:10 |
| 3 | Worker bị chết giữa chừng | cảnh 2 + một đoạn cuối cảnh 3 | 1:40 |
| 4 | Ảnh lỗi & hàng đợi Dead-Letter | cảnh 3 | 1:30 |
| 5 | Kết quả nhận diện | cảnh 4 + 3 ảnh | 0:40 |
| 6 | Tổng kết số liệu & xoá cluster | cảnh 5 | 1:10 |
| 7 | Kết thúc | nền chữ | 0:10 |

> [!IMPORTANT]
> Kết quả BigQuery ở **cuối file cảnh 2** được chụp lúc worker **chưa xử lý xong** (`lost = 978`) → **bỏ đoạn này**. Kết quả đúng (`lost = 0`) nằm ở **cuối file cảnh 3** → cắt đoạn đó mang sang **Phần 3**.

---

## Phần 0 — Mở đầu & kiến trúc (0:30)

**Cắt ghép**
1. 0:00–0:05: nền đen + chữ tiêu đề.
2. 0:05–0:30: ảnh slide kiến trúc, phóng to chậm từ 100% lên 110% cho đỡ tĩnh.

**Chữ trên màn hình**
- Giữa màn hình (0:00–0:05): **"Autoscaled YOLO26 Stream Pipeline on Google Cloud"**, dòng nhỏ bên dưới: *"Nhóm … · Cloud Computing · HCMUT"*.
- Trên ảnh kiến trúc: không thêm chữ (slide đã có).

**Lời thuyết minh**
> "Xin chào thầy và các bạn. Nhóm em xin demo hệ thống nhận diện phương tiện giao thông theo luồng, tự động co giãn trên Google Cloud. Luồng dữ liệu như sau: một camera giả lập đọc video, cắt từng khung hình, tải ảnh lên Cloud Storage và gửi một tin nhắn nhỏ vào Pub/Sub. Các worker chạy mô hình YOLO26 trên GKE Autopilot nhận tin nhắn, tải ảnh về, nhận diện rồi ghi kết quả vào BigQuery. KEDA theo dõi số tin nhắn đang tồn trong hàng đợi để tăng hoặc giảm số worker từ 1 đến 8. Ảnh nào xử lý thất bại 5 lần sẽ bị chuyển sang một hàng đợi riêng gọi là dead-letter. Video gồm ba kịch bản: tải tăng đột biến, worker bị chết giữa chừng và ảnh bị hỏng."

---

## Phần 1 — Hạ tầng trên Console (0:30)

**Cắt ghép** (file **cảnh 1**)

| Đoạn | Mốc trong file | Tốc độ | Thấy gì |
|---|---|---|---|
| 1a | 00:00–00:25 | 1.5x | Trang bucket `project001-480402-yolo-frames` (đang trống) |
| 1b | 00:25–00:45 | 1.5x | Trang *Deployment details* của `worker`, dấu tích xanh, 1 pod |

**[Zoom: tên bucket]** ở 1a; **[Zoom: chữ `worker` + dòng *Replicas* "1 ready"]** ở 1b.

**Chữ trên màn hình**
- Tiêu đề phần: **"PHẦN 1 · HẠ TẦNG"**
- Ở 1a: *"Cloud Storage – nơi lưu ảnh khung hình"*
- Ở 1b: *"GKE Autopilot – worker đang chạy 1 pod"*

**Lời thuyết minh**
> "Đây là bucket Cloud Storage dùng để chứa ảnh khung hình; hiện đang trống vì nhóm đã dọn dữ liệu trước khi quay. Còn đây là cluster GKE Autopilot, deployment worker đang chạy 1 pod – đây là mức tối thiểu khi hệ thống rảnh. Các thành phần còn lại gồm Pub/Sub, BigQuery và Artifact Registry đều được tạo tự động bằng một script."

> [!NOTE]
> Bản quay chưa có trang Pub/Sub, BigQuery, Artifact Registry. Các tài nguyên này vẫn còn (chỉ cluster đã bị xoá). Nếu muốn đầy đủ, quay thêm khoảng 20 giây lướt ba trang đó rồi chèn vào cuối phần này.

---

## Phần 2 — Tải đột biến & tự co giãn (2:10)

**Kịch bản:** gửi 3,5 ảnh/giây trong 2 phút → **35 ảnh/giây trong 3 phút** (gấp 5 lần sức 1 pod) → 3,5 ảnh/giây trong 2 phút. Tổng **7.140 ảnh**, `run_id` **20261121-185741**.

**Cắt ghép** (file **cảnh 1** rồi nối **cảnh 1.2**)

| Đoạn | File & mốc | Tốc độ | Sau dựng | Thấy gì |
|---|---|---|---|---|
| 2a | cảnh 1, 00:45–01:05 | 1x | 0:20 | Gõ lệnh `burst`, in ra `run_id` |
| 2b | cảnh 1, 01:05–04:30 | x16 | 0:13 | Tải nhẹ, các biểu đồ gần như phẳng |
| 2c | cảnh 1, 04:30–08:00 | x6 | 0:35 | Backlog vọt lên; pod mới `Pending` → `ContainerCreating` → `Running`; biểu đồ pod tăng lên 8 |
| 2d | cảnh 1, 08:00–hết file | x16 | 0:20 | 8 pod cùng xử lý, backlog đi xuống |
| 2e | cảnh 1.2, 00:00–04:00 | x16 | 0:15 | Backlog về 0 |
| 2f | cảnh 1.2, 04:00–hết file | x8 | 0:34 | Pod thừa `Terminating`, biểu đồ pod rơi về 1 |

- **[Zoom: terminal dưới – lệnh và `run_id`]** ở 2a.
- **[Zoom: biểu đồ Backlog]** rồi **[Zoom: terminal trên – cột STATUS có `Pending`]** ở 2c.
- **[Zoom: biểu đồ Worker pods running]** ở cuối 2c và ở 2f.

**Chữ trên màn hình**
- Tiêu đề phần: **"PHẦN 2 · TẢI ĐỘT BIẾN & TỰ CO GIÃN"**
- Huy hiệu tốc độ ở các đoạn 2b–2f.
- 2a: *"burst --capacity 7 · 1 pod xử lý ~7 ảnh/giây"*
- 2b: *"Tải nhẹ 3,5 ảnh/giây – 1 pod đủ sức"*
- 2c (đầu): *"Tải tăng vọt: 35 ảnh/giây"* → (giữa): *"Backlog tăng → KEDA tăng số pod"* → mũi tên chỉ dòng `Pending`: *"Pending = Autopilot đang cấp máy mới"*
- 2d: *"8 pod cùng xử lý – backlog giảm dần"*
- 2f: *"Hết tải → tự giảm về 1 pod"*

**Lời thuyết minh**
- **2a:** "Kịch bản đầu tiên là tải tăng đột biến. Một pod xử lý được khoảng 7 ảnh mỗi giây. Producer gửi nhẹ 3,5 ảnh mỗi giây trong 2 phút, rồi đột ngột tăng lên 35 ảnh mỗi giây trong 3 phút, tức gấp 5 lần sức một pod, sau đó hạ lại."
- **2b:** "Giai đoạn đầu tải nhẹ nên 1 pod xử lý kịp, các biểu đồ gần như đứng yên."
- **2c:** "Khi tải tăng vọt, số tin nhắn tồn trong hàng đợi – biểu đồ Backlog – tăng rất nhanh. KEDA đọc con số này từ Cloud Monitoring, chia cho ngưỡng 10 tin nhắn mỗi pod và yêu cầu thêm pod. Ở terminal bên trái, các pod mới xuất hiện ở trạng thái Pending vì GKE Autopilot phải cấp thêm máy, sau đó chuyển sang ContainerCreating rồi Running. Số pod tăng từ 1 lên tối đa 8. Lưu ý là số liệu trên Cloud Monitoring trễ khoảng 1 đến 2 phút, nên từ lúc tải tăng tới lúc có pod mới mất khoảng 2 phút 20 giây."
- **2d + 2e:** "Khi đủ pod, tốc độ xử lý vượt tốc độ gửi, backlog đi xuống và về 0."
- **2f:** "Khi không còn tải, KEDA giảm dần số pod. Các pod thừa chuyển sang Terminating và hệ thống trở về 1 pod để tiết kiệm chi phí. Cả lần chạy 7.140 ảnh chỉ tốn khoảng 0,8 pod-giờ, tương đương 0,045 đô la."

---

## Phần 3 — Worker bị chết giữa chừng (1:40)

**Kịch bản:** gửi **21 ảnh/giây trong 5 phút** (6.300 ảnh), đồng thời **cứ 30 giây script xoá ngẫu nhiên 1 pod** đang chạy. `run_id` **20261121-192426**.

**Cắt ghép** (file **cảnh 2**, cuối phần lấy thêm 1 đoạn từ **cảnh 3**)

| Đoạn | File & mốc | Tốc độ | Sau dựng | Thấy gì |
|---|---|---|---|---|
| 3a | cảnh 2, 00:00–00:45 | 1.5x | 0:30 | Gõ lệnh `kill`, in `run_id`, dòng `deleted pod/worker-…` đầu tiên |
| 3b | cảnh 2, 00:45–02:15 | x3 | 0:30 | Pod bị xoá `Terminating` → pod mới `Pending` → `Running`, mỗi 30 giây thêm một dòng `deleted` |
| 3c | cảnh 2, 02:15–09:15 | x16 | 0:26 | Tải cao, pod tăng, việc xoá pod vẫn tiếp tục, producer chạy xong |
| **BỎ** | cảnh 2, 09:15–hết file | — | — | Tab BigQuery lúc chưa xử lý xong (`lost = 978`) |
| 3d | cảnh 3, khoảng 11:10–11:55 – đoạn tab BigQuery hiện khung JSON có `"lost": "0"` | 1x | 0:08 | Kết quả kiểm chứng cuối cùng |
| 3e | Đóng băng khung hình cuối của 3d | — | 0:06 | Giữ kết quả cho người xem đọc |

- **[Zoom: terminal dưới – các dòng `deleted pod/worker-…`]** ở 3a.
- **[Zoom: terminal trên – dòng `Terminating` và `Pending`]** ở 3b.
- **[Zoom: khung JSON kết quả]** ở 3d–3e.

**Chữ trên màn hình**
- Tiêu đề phần: **"PHẦN 3 · WORKER BỊ CHẾT GIỮA CHỪNG"**
- 3a: *"Cứ 30 giây xoá ngẫu nhiên 1 pod đang xử lý"*
- 3b: mũi tên chỉ `Terminating`: *"Pod bị xoá"*; mũi tên chỉ `Pending`: *"Kubernetes tự tạo pod thay thế"*
- 3e (khung nổi giữa màn hình): **"Gửi 6.300 · Xử lý 6.300 · Ghi trùng 1 · Mất 0"**

**Lời thuyết minh**
- **3a:** "Kịch bản thứ hai kiểm tra khả năng chịu lỗi. Producer gửi 21 ảnh mỗi giây trong 5 phút, đồng thời cứ 30 giây script lại xoá ngẫu nhiên một pod đang chạy – giống như máy bị hỏng đột ngột."
- **3b:** "Mỗi lần một pod bị xoá, nó chuyển sang Terminating và Kubernetes tự tạo pod mới thay thế. Worker chỉ xác nhận với Pub/Sub sau khi đã ghi kết quả vào BigQuery, nên ảnh mà pod chết đang xử lý dở vẫn còn trong hàng đợi và được Pub/Sub giao lại cho pod khác sau thời hạn 60 giây."
- **3c:** "Quá trình này lặp lại suốt 5 phút, trong khi KEDA vẫn tăng số pod theo tải."
- **3d + 3e:** "Sau khi xử lý xong, nhóm kiểm chứng bằng BigQuery: gửi 6.300 ảnh, xử lý đủ 6.300, mất 0. Có đúng 1 ảnh bị ghi 2 lần – đó là ảnh mà pod đã ghi kết quả nhưng bị xoá trước khi kịp xác nhận, nên Pub/Sub giao lại cho pod khác. Đây là cơ chế giao ít nhất một lần của Pub/Sub, và view detections_dedup trong BigQuery đã lọc bỏ bản trùng."

---

## Phần 4 — Ảnh lỗi & hàng đợi Dead-Letter (1:30)

**Kịch bản:** gửi **7 ảnh/giây trong 5 phút** (2.100 ảnh), khoảng **2% là dữ liệu hỏng** không đọc được thành ảnh. `run_id` **20261121-194408**.

**Cắt ghép** (file **cảnh 3**)

| Đoạn | Mốc trong file | Tốc độ | Sau dựng | Thấy gì |
|---|---|---|---|---|
| 4a | 00:10–00:40 | 1.5x | 0:20 | Gõ lệnh `corrupt`, in `run_id` |
| 4b | 00:40–05:30 | x16 | 0:18 | Chờ tải lên, số liệu Monitoring còn trễ |
| 4c | 05:30–10:00 | x8 | 0:34 | Pod tăng; xuất hiện các cột xanh ở biểu đồ *Dead-lettered messages* |
| 4d | 10:00–11:10 | x4 | 0:18 | Backlog về 0, pod về 1, đủ các cột dead-letter |
| **BỎ** | 11:10–hết file | — | — | Đoạn 11:10–11:55 đã dùng ở Phần 3; phần còn lại là tab BigQuery trống |

- **[Zoom: biểu đồ Dead-lettered messages]** (dưới phải) ở 4c.
- **[Zoom: biểu đồ Messages/s – đường acked vẫn đi lên]** ở 4c.

**Chữ trên màn hình**
- Tiêu đề phần: **"PHẦN 4 · ẢNH LỖI & HÀNG ĐỢI DEAD-LETTER"**
- 4a: *"2% dữ liệu gửi đi là ảnh hỏng"*
- 4c: mũi tên chỉ các cột xanh: *"Ảnh hỏng thử 5 lần thất bại → chuyển sang frames-dlq"*
- 4d (khung nổi giữa màn hình): **"Gửi 2.100 · Xử lý 2.060 · Dead-letter 40 (1,9%) · Mất 0"** – số liệu này lấy từ lệnh `collect.py` ở Phần 6.

**Lời thuyết minh**
- **4a:** "Kịch bản cuối mô phỏng dữ liệu hỏng. Producer gửi 7 ảnh mỗi giây trong 5 phút, trong đó khoảng 2% là dữ liệu rác không đọc được thành ảnh."
- **4b:** "Tương tự như trước, cần chờ 1 đến 2 phút để số liệu lên Cloud Monitoring."
- **4c:** "Worker không đọc được ảnh hỏng nên báo lỗi và trả tin nhắn lại cho Pub/Sub. Pub/Sub thử giao lại với thời gian chờ tăng dần từ 5 đến 60 giây; sau 5 lần thất bại, tin nhắn được chuyển sang topic frames-dlq – chính là các cột trên biểu đồ Dead-lettered messages. Trong lúc đó các ảnh bình thường vẫn được xử lý, hàng đợi không bị kẹt."
- **4d:** "Kết quả: 2.100 ảnh gửi đi, 2.060 ảnh xử lý thành công, 40 ảnh – khoảng 1,9% – vào dead-letter và được ghi lại trong bảng dead_letters để tra cứu sau. Không mất ảnh nào."

---

## Phần 5 — Kết quả nhận diện (0:40)

**Cắt ghép**

| Đoạn | Nguồn | Tốc độ | Sau dựng | Thấy gì |
|---|---|---|---|---|
| **BỎ** | cảnh 4, 00:00–00:25 | — | — | Dashboard đứng yên |
| 5a | cảnh 4, 00:25–hết file | x3 | 0:28 | Chạy `draw_boxes.py` cho 3 lần chạy, thư mục `boxes` hiện 15 ảnh |
| 5b | 3 ảnh trong `reports\figures\boxes\` | — | 0:12 | Mỗi ảnh full màn hình 4 giây |

**[Zoom: dòng `… 18 objects` / `19 objects` trong terminal]** ở 5a.

**Chữ trên màn hình**
- Tiêu đề phần: **"PHẦN 5 · KẾT QUẢ NHẬN DIỆN"**
- 5a: *"draw_boxes.py vẽ lại khung từ toạ độ lưu trong BigQuery"*
- 5b: *"Mỗi khung hình nhận diện 18–19 phương tiện"*

**Lời thuyết minh**
> "Để kiểm tra chất lượng nhận diện, script draw_boxes đọc toạ độ khung mà worker đã ghi vào BigQuery rồi vẽ lại lên ảnh gốc. Mỗi khung hình nhận diện được khoảng 18 đến 19 phương tiện. Đây là một vài ảnh kết quả."

---

## Phần 6 — Tổng kết số liệu & xoá cluster (1:10)

**Cắt ghép** (file **cảnh 5**)

| Đoạn | Mốc trong file | Tốc độ | Sau dựng | Thấy gì |
|---|---|---|---|---|
| **BỎ** | 00:00–00:15 | — | — | Lệnh `collect.py` gõ thiếu tham số, báo lỗi `usage` |
| 6a | 00:15–01:00 | 1.5x | 0:30 | `collect.py` in số liệu của burst, kill, corrupt |
| 6b | Đóng băng khung cuối 6a | — | 0:10 | Hiện bảng tổng kết đè lên |
| 6c | 01:00–06:00 | x16 | 0:19 | Gõ `cluster.sh down`, chờ xoá |
| 6d | 06:00–hết file | x2 | 0:11 | Dòng `Deleted [...] yolo-cluster` |

> [!WARNING]
> Khoảng **02:30** có thông báo chat *"Nhóm: FL framework"* bật lên ở góc phải dưới → dùng *Mosaic/Blur* che vùng đó, hoặc dán một khung đen nhỏ lên.

**[Zoom: dòng `published processed written_twice dead_lettered lost` của từng kịch bản]** ở 6a; **[Zoom: dòng `Deleted …`]** ở 6d.

**Chữ trên màn hình**
- Tiêu đề phần: **"PHẦN 6 · TỔNG KẾT & DỌN DẸP"**
- 6b – bảng nổi giữa màn hình:

| Kịch bản | Gửi | Xử lý | Ghi trùng | Dead-letter | Mất | Pod tối đa | Chi phí |
|---|---|---|---|---|---|---|---|
| Tải đột biến | 7.140 | 7.140 | 0 | 0 | 0 | 8 | 0,045 USD |
| Worker chết | 6.300 | 6.300 | 1 | 0 | 0 | 8 | 0,035 USD |
| Ảnh lỗi | 2.100 | 2.060 | 0 | 40 | 0 | 8 | 0,035 USD |

- 6c: *"Xoá cluster để ngừng tính tiền"*

**Lời thuyết minh**
- **6a + 6b:** "Script collect tổng hợp số liệu của cả ba lần chạy từ BigQuery và Cloud Monitoring. Cả ba kịch bản đều không mất ảnh nào; hệ thống tự tăng lên tối đa 8 pod khi tải cao, và mỗi lần chạy chỉ tốn khoảng 3 đến 5 xu đô la."
- **6c + 6d:** "Cuối cùng, nhóm xoá cluster GKE bằng một lệnh để ngừng tính tiền. Bucket, Pub/Sub và BigQuery được giữ lại vì gần như không tốn phí; lần sau chỉ cần tạo lại cluster."

---

## Phần 7 — Kết thúc (0:10)

**Cắt ghép:** nền đen 10 giây.

**Chữ trên màn hình:** **"Cảm ơn thầy và các bạn đã theo dõi"**, dòng nhỏ bên dưới: link repo GitHub.

**Lời thuyết minh**
> "Cảm ơn thầy và các bạn đã theo dõi."

---

## Hoàn thiện: thu giọng, phụ đề, xuất file

1. **Dựng xong toàn bộ hình trước** (cắt, tốc độ, zoom, chữ) theo Phần 0 → 7.
2. **Tắt âm thanh gốc** của tất cả clip (bản quay màn hình không có tiếng hữu ích).
3. **Thu giọng:** dùng *Ghi âm* (Record voiceover) của CapCut, phát từng phần và đọc đúng "Lời thuyết minh" của phần đó. Nếu lời dài hơn hình, **giảm tốc độ tua của đoạn đó** (ví dụ x16 → x12) thay vì nói nhanh.
4. **Phụ đề:** *Text → Auto captions → Tiếng Việt*, sau đó đọc lại và sửa các từ chuyên ngành (Pub/Sub, KEDA, BigQuery, dead-letter, pod, Autopilot). Đặt phụ đề ở giữa phía dưới, chữ trắng viền đen; nếu che terminal dưới thì nâng lên một chút.
5. **Kiểm tra trước khi xuất:**
   - Không còn đoạn BigQuery `lost = 978` (cuối cảnh 2).
   - Không còn đoạn `collect.py` báo lỗi `usage` (đầu cảnh 5).
   - Thông báo chat ở cảnh 5 đã được che.
   - Tổng thời lượng khoảng 8–9 phút.
6. **Xuất:** MP4 H.264, 30 fps, độ phân giải 1440p (nếu được, để chữ terminal rõ hơn) hoặc 1080p. Upload YouTube (*Unlisted*) hoặc Google Drive.

> [!TIP]
> **Nếu thuyết trình trực tiếp** thay vì thu giọng: phát video không tiếng, đọc đúng "Lời thuyết minh" của từng phần, và **tạm dừng video ở các khung kết quả** (cuối Phần 3, cuối Phần 4, bảng ở Phần 6) để giải thích số liệu.
