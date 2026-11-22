# Hướng dẫn dựng video demo từ 6 file đã quay

Video thành phẩm dài khoảng **8–9 phút**, gồm 8 phần làm lần lượt từ trên xuống. Mỗi phần ghi rõ: **cắt đoạn nào – tua bao nhiêu – chèn chữ gì, lúc nào**.

---

## Bước chuẩn bị

1. **Phần mềm:** CapCut bản máy tính (miễn phí). Chỉ cần các thao tác: *Tách* (`Ctrl + B`), *Tốc độ* (Speed), *Văn bản* (Text), *Làm mờ* (Blur/Mosaic), *Phóng to bằng keyframe*, *Đóng băng khung hình* (Freeze).
2. Tạo project mới tỉ lệ **16:9**, kéo cả 6 file vào thư viện. File gốc 2560×1380 rộng hơn 16:9 một chút → để chế độ *Fit*, chấp nhận viền đen mỏng trên/dưới.
3. Kéo thêm vào thư viện: **ảnh slide kiến trúc** (slide 4) và **3 ảnh** bất kỳ trong `F:\Cloud-computing\reports\figures\boxes\`.
4. **Tắt âm thanh gốc** của mọi clip. Nếu muốn, thêm một bản nhạc nền không lời, âm lượng thấp (khoảng 15–20%).
5. Màn hình quay chia nhiều cửa sổ nên chữ rất nhỏ. Ở những chỗ ghi **[Zoom: …]**, **phóng to vào vùng đó (Scale 160–200%) trong 3–5 giây rồi thu về**.
6. Mốc `mm:ss` là thời gian **trong file gốc**, sai số khoảng ±15 giây → kéo thanh thời gian quanh mốc để tìm đúng khoảnh khắc.

**Bố cục màn hình trong các file (để biết chỗ cần zoom):**
- **Trái trên:** terminal `kubectl get pods -n yolo -w` – danh sách pod và trạng thái (`Pending` → `ContainerCreating` → `Running` → `Terminating`).
- **Trái dưới:** terminal gõ lệnh demo.
- **Phải:** Dashboard *YOLO26 Stream Pipeline* gồm 6 biểu đồ: *Backlog* (trên trái), *Worker pods running* (trên phải), *Oldest unacked message age* (giữa trái), *Messages/s: published vs acked* (giữa phải), *Worker CPU* (dưới trái), *Dead-lettered messages* (dưới phải).

**4 loại chữ dùng thống nhất cho cả video:**

| Loại | Vị trí | Kiểu chữ | Thời gian hiện |
|---|---|---|---|
| **Tiêu đề phần** | Góc trên trái | Nền xanh đậm hơi trong suốt, chữ trắng in đậm, cỡ lớn | Suốt phần đó |
| **Chú thích** (caption) | Giữa, phía dưới màn hình | Nền đen mờ 60%, chữ trắng, tối đa 2 dòng | **Ít nhất 4 giây** mỗi câu |
| **Nhãn chỉ** | Cạnh vùng cần nhìn | Chữ trắng nền đen + mũi tên hoặc khung đỏ | 3–5 giây |
| **Huy hiệu tốc độ** | Góc trên phải | Chữ vàng (`x16`, `x8`…) | Chỉ ở đoạn tua |

> [!IMPORTANT]
> Mỗi câu chú thích phải hiện **ít nhất 4 giây** để người xem đọc kịp; câu dài 2 dòng thì 5–6 giây. Nếu một đoạn tua quá ngắn so với số câu cần hiện, **giảm tốc độ tua** của đoạn đó (ví dụ x16 → x10) thay vì cắt bớt chữ.

---

## Bản đồ video

| # | Phần | Lấy từ file | Thời lượng sau dựng |
|---|---|---|---|
| 0 | Mở đầu & kiến trúc | ảnh slide | 0:35 |
| 1 | Hạ tầng trên Console | cảnh 1 (đầu file) | 0:30 |
| 2 | Tải đột biến & tự co giãn | cảnh 1 (phần còn lại) + cảnh 1.2 | 2:10 |
| 3 | Worker bị chết giữa chừng | cảnh 2 + một đoạn cuối cảnh 3 | 1:40 |
| 4 | Ảnh lỗi & hàng đợi Dead-Letter | cảnh 3 | 1:30 |
| 5 | Kết quả nhận diện | cảnh 4 + 3 ảnh | 0:40 |
| 6 | Tổng kết số liệu & xoá cluster | cảnh 5 | 1:15 |
| 7 | Kết thúc | nền chữ | 0:08 |

> [!IMPORTANT]
> Kết quả BigQuery ở **cuối file cảnh 2** được chụp lúc worker **chưa xử lý xong** (`lost = 978`) → **bỏ đoạn này**. Kết quả đúng (`lost = 0`) nằm ở **cuối file cảnh 3** → cắt đoạn đó mang sang **Phần 3**.

---

## Phần 0 — Mở đầu & kiến trúc (0:35)

**Cắt ghép**
1. 0:00–0:06: nền đen + màn hình tiêu đề.
2. 0:06–0:35: ảnh slide kiến trúc, phóng to chậm từ 100% lên 110% cho đỡ tĩnh. Các chú thích bên dưới hiện lần lượt trên ảnh này.

**Chữ chèn vào video**

| Hiện lúc | Loại | Nội dung chữ |
|---|---|---|
| 0:00–0:06 | Tiêu đề lớn giữa màn hình | **Autoscaled YOLO26 Stream Pipeline on Google Cloud** <br> *(dòng nhỏ)* Group … · Cloud Computing · HCMUT |
| 0:06–0:12 | Chú thích | A simulated camera splits a traffic video into frames, uploads each frame to Cloud Storage and publishes a message to Pub/Sub. |
| 0:12–0:18 | Chú thích | Worker pods on GKE Autopilot pull the messages, run YOLO26 object detection and write the results to BigQuery. |
| 0:18–0:24 | Chú thích | KEDA watches the Pub/Sub backlog and scales the workers between 1 and 8 pods. |
| 0:24–0:29 | Chú thích | Frames that fail 5 times are moved to a dead-letter topic instead of blocking the queue. |
| 0:29–0:35 | Chú thích | This demo runs 3 scenarios: a traffic burst, workers crashing, and corrupted frames. |

---

## Phần 1 — Hạ tầng trên Console (0:30)

**Cắt ghép** (file **cảnh 1**)

| Đoạn | Mốc trong file | Tốc độ | Thấy gì |
|---|---|---|---|
| 1a | 00:00–00:25 | 1.5x | Trang bucket `project001-480402-yolo-frames` (đang trống) |
| 1b | 00:25–00:45 | 1.5x | Trang *Deployment details* của `worker`, dấu tích xanh, 1 pod |

**[Zoom: tên bucket]** ở 1a; **[Zoom: chữ `worker` + dòng *Replicas* "1 ready"]** ở 1b.

**Chữ chèn vào video**

| Đoạn | Loại | Nội dung chữ |
|---|---|---|
| Cả phần | Tiêu đề phần | **PART 1 · INFRASTRUCTURE** |
| 1a | Chú thích | Cloud Storage bucket that stores the video frames (empty before the demo). |
| 1b | Chú thích | GKE Autopilot cluster: the worker deployment is running 1 pod, the minimum when the system is idle. |
| 1b (cuối) | Chú thích | Pub/Sub, BigQuery and Artifact Registry are all created by one script: `infra/setup.sh`. |

> [!NOTE]
> Bản quay chưa có trang Pub/Sub, BigQuery, Artifact Registry. Nếu muốn đầy đủ, cần chạy lại `infra/setup.sh` (tài nguyên đã bị xoá hết) rồi quay thêm khoảng 20 giây lướt ba trang đó, chèn vào cuối phần này.

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

**Chữ chèn vào video**

| Đoạn | Loại | Nội dung chữ |
|---|---|---|
| Cả phần | Tiêu đề phần | **PART 2 · TRAFFIC BURST & AUTOSCALING** |
| 2a | Chú thích | One pod processes about 7 frames per second. |
| 2a | Chú thích | Load plan: 3.5 fps for 2 min → 35 fps for 3 min (5× one pod) → 3.5 fps for 2 min. 7,140 frames in total. |
| 2b | Chú thích | Light load: a single pod keeps up, the charts stay flat. |
| 2c (đầu) | Chú thích | Load jumps to 35 fps – the Pub/Sub backlog grows quickly. |
| 2c (giữa) | Chú thích | KEDA reads the backlog from Cloud Monitoring and adds 1 pod for every 10 waiting messages. |
| 2c (giữa) | Nhãn chỉ (vào dòng `Pending`) | Pending = Autopilot is provisioning a new node |
| 2c (cuối) | Nhãn chỉ (vào biểu đồ pod) | 1 → 8 pods |
| 2c (cuối) | Chú thích | Monitoring metrics lag 1–2 min, so the first new pods arrive about 2 min 20 s after the spike. |
| 2d | Chú thích | 8 pods now process faster than frames arrive – the backlog drains. |
| 2e | Chú thích | Backlog back to 0. |
| 2f | Chú thích | No more load: KEDA removes the extra pods and the deployment returns to 1 pod. |
| 2f (cuối) | Chú thích | The whole run used only 0.83 pod-hours ≈ $0.045. |

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

**Chữ chèn vào video**

| Đoạn | Loại | Nội dung chữ |
|---|---|---|
| Cả phần | Tiêu đề phần | **PART 3 · WORKER FAILURES** |
| 3a | Chú thích | 21 fps for 5 min (6,300 frames), while a script deletes a random worker pod every 30 seconds. |
| 3a | Nhãn chỉ (vào dòng `deleted pod/…`) | A pod is killed |
| 3b | Nhãn chỉ (vào `Terminating`) | Killed pod |
| 3b | Nhãn chỉ (vào `Pending`) | Kubernetes starts a replacement |
| 3b | Chú thích | A worker acknowledges a message only after its result is saved in BigQuery. |
| 3b | Chú thích | If a pod dies mid-frame, Pub/Sub redelivers that frame to another pod after the 60 s ack deadline. |
| 3c | Chú thích | Pods keep getting killed for 5 minutes while KEDA keeps scaling with the load. |
| 3d | Chú thích | Verification query in BigQuery after the run. |
| 3e | Khung nổi giữa màn hình | **Published 6,300 · Processed 6,300 · Written twice 1 · Lost 0** |
| 3e | Chú thích | 1 frame was written twice (at-least-once delivery); the `detections_dedup` view removes the duplicate. |

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

**Chữ chèn vào video**

| Đoạn | Loại | Nội dung chữ |
|---|---|---|
| Cả phần | Tiêu đề phần | **PART 4 · CORRUPTED FRAMES & DEAD-LETTER QUEUE** |
| 4a | Chú thích | 7 fps for 5 min (2,100 frames); about 2% of them are random bytes, not valid images. |
| 4b | Chú thích | Waiting for the metrics to reach Cloud Monitoring (1–2 min delay). |
| 4c | Chú thích | A worker cannot decode a broken frame, so it returns the message to Pub/Sub. |
| 4c | Chú thích | Pub/Sub retries with a 5 s → 60 s backoff; after 5 failed attempts the message moves to `frames-dlq`. |
| 4c | Nhãn chỉ (vào các cột xanh) | Messages moved to the dead-letter topic |
| 4c | Nhãn chỉ (vào đường acked) | Valid frames keep flowing – the queue never gets stuck |
| 4d | Khung nổi giữa màn hình | **Published 2,100 · Processed 2,060 · Dead-lettered 40 (1.9%) · Lost 0** |
| 4d | Chú thích | Dead-lettered frames are saved in the BigQuery table `dead_letters` for later inspection. |

---

## Phần 5 — Kết quả nhận diện (0:40)

**Cắt ghép**

| Đoạn | Nguồn | Tốc độ | Sau dựng | Thấy gì |
|---|---|---|---|---|
| **BỎ** | cảnh 4, 00:00–00:25 | — | — | Dashboard đứng yên |
| 5a | cảnh 4, 00:25–hết file | x3 | 0:28 | Chạy `draw_boxes.py` cho 3 lần chạy, thư mục `boxes` hiện 15 ảnh |
| 5b | 3 ảnh trong `reports\figures\boxes\` | — | 0:12 | Mỗi ảnh full màn hình 4 giây |

**[Zoom: dòng `… 18 objects` / `19 objects` trong terminal]** ở 5a.

**Chữ chèn vào video**

| Đoạn | Loại | Nội dung chữ |
|---|---|---|
| Cả phần | Tiêu đề phần | **PART 5 · DETECTION RESULTS** |
| 5a | Chú thích | `draw_boxes.py` reads the box coordinates stored in BigQuery and draws them on the original frames. |
| 5b | Chú thích | YOLO26 detects 18–19 vehicles per frame. |

---

## Phần 6 — Tổng kết số liệu & xoá cluster (1:15)

**Cắt ghép** (file **cảnh 5**)

| Đoạn | Mốc trong file | Tốc độ | Sau dựng | Thấy gì |
|---|---|---|---|---|
| **BỎ** | 00:00–00:15 | — | — | Lệnh `collect.py` gõ thiếu tham số, báo lỗi `usage` |
| 6a | 00:15–01:00 | 1.5x | 0:30 | `collect.py` in số liệu của burst, kill, corrupt |
| 6b | Đóng băng khung cuối 6a | — | 0:15 | Hiện bảng tổng kết đè lên |
| 6c | 01:00–06:00 | x16 | 0:19 | Gõ `cluster.sh down`, chờ xoá |
| 6d | 06:00–hết file | x2 | 0:11 | Dòng `Deleted [...] yolo-cluster` |

> [!WARNING]
> Khoảng **02:30** có thông báo chat *"Nhóm: FL framework"* bật lên ở góc phải dưới → dùng *Mosaic/Blur* che vùng đó, hoặc dán một khung đen nhỏ lên.

**[Zoom: dòng `published processed written_twice dead_lettered lost` của từng kịch bản]** ở 6a; **[Zoom: dòng `Deleted …`]** ở 6d.

**Chữ chèn vào video**

| Đoạn | Loại | Nội dung chữ |
|---|---|---|
| Cả phần | Tiêu đề phần | **PART 6 · SUMMARY & CLEAN-UP** |
| 6a | Chú thích | `collect.py` gathers the results of all 3 runs from BigQuery and Cloud Monitoring. |
| 6b | Bảng nổi giữa màn hình | Xem bảng ngay dưới đây |
| 6b | Chú thích | No frame was lost in any scenario, and each run cost only a few cents. |
| 6c | Chú thích | Deleting the GKE cluster with one command to stop all hourly charges. |
| 6d | Chú thích | Cluster deleted. |

Bảng nổi ở 6b (tạo bằng Text hoặc chèn ảnh chụp bảng):

| Scenario | Published | Processed | Written twice | Dead-lettered | Lost | Max pods | Cost |
|---|---|---|---|---|---|---|---|
| Traffic burst | 7,140 | 7,140 | 0 | 0 | 0 | 8 | $0.045 |
| Worker failures | 6,300 | 6,300 | 1 | 0 | 0 | 8 | $0.035 |
| Corrupted frames | 2,100 | 2,060 | 0 | 40 | 0 | 8 | $0.035 |

---

## Phần 7 — Kết thúc (0:08)

**Cắt ghép:** nền đen 8 giây.

**Chữ chèn vào video**

| Hiện lúc | Loại | Nội dung chữ |
|---|---|---|
| 0:00–0:08 | Chữ lớn giữa màn hình | **Thank you for watching!** <br> *(dòng nhỏ)* link repo GitHub |

---

## Hoàn thiện & xuất file

1. **Dựng xong toàn bộ hình trước** (cắt, tốc độ, zoom) theo Phần 0 → 7, sau đó mới chèn chữ.
2. **Chèn chữ:** tạo sẵn 1 mẫu cho mỗi loại chữ (tiêu đề phần, chú thích, nhãn chỉ, huy hiệu tốc độ), lưu thành *preset*, rồi copy cho các đoạn để kiểu chữ đồng nhất.
3. **Xem lại toàn bộ video một lượt** và kiểm tra:
   - Mỗi câu chú thích hiện ít nhất 4 giây, đọc kịp.
   - Chú thích không che biểu đồ hay dòng terminal đang được nói tới (nếu che thì nâng lên hoặc dời sang bên).
   - Không còn đoạn BigQuery `lost = 978` (cuối cảnh 2).
   - Không còn đoạn `collect.py` báo lỗi `usage` (đầu cảnh 5).
   - Thông báo chat ở cảnh 5 đã được che.
   - Tổng thời lượng khoảng 8–9 phút.
4. **Xuất:** MP4 H.264, 30 fps, độ phân giải 1440p (nếu được, để chữ terminal rõ hơn) hoặc 1080p. Upload YouTube (*Unlisted*) hoặc Google Drive.
