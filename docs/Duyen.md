Bạn làm theo thứ tự: **tạo 4 mẫu chữ trước, rồi copy ra từng đoạn, rồi sửa nội dung**. Làm vậy kiểu chữ sẽ đồng nhất và nhanh hơn nhiều so với gõ từng cái.

## Bước 1: tạo 4 mẫu chữ

Vào tab **Text** (góc trên trái) → **Default text** → bấm **+** (hoặc kéo xuống timeline). Bấm vào chữ, panel bên phải có **Basic** để chỉnh font, cỡ, màu và **Background** để bật nền.

| Loại | Cài đặt | Vị trí |
|---|---|---|
| **Tiêu đề phần** | Chữ trắng, in đậm, cỡ lớn. Bật Background màu xanh đậm, độ trong suốt khoảng 70–80% | Góc trên trái |
| **Chú thích** | Chữ trắng, cỡ vừa. Bật Background đen, Opacity 60%. Tối đa 2 dòng | Giữa, phía dưới |
| **Nhãn chỉ** | Chữ trắng, nền đen, thêm mũi tên hoặc khung đỏ (Stickers/Elements, gõ "arrow" hoặc "red frame") | Cạnh vùng cần chỉ |
| **Huy hiệu tốc độ** | Chữ vàng in đậm, ví dụ `x16` | Góc trên phải |

Cách làm mỗi mẫu: chỉnh xong, kéo chữ tới đúng vị trí trong màn hình xem trước, rồi kéo cạnh trên timeline cho vừa độ dài. Cuối panel Text có nút **Save as preset** để lưu. Để mỗi loại chữ nằm riêng một track (track 1 tiêu đề, track 2 chú thích, track 3 nhãn, track 4 huy hiệu) thì dễ nhìn hơn.

## Bước 2: copy và sửa nội dung

- Chọn chữ, **Ctrl + C**, đặt đầu phát chỗ cần, **Ctrl + V**.
- Bấm đúp vào chữ trong màn hình xem trước để gõ nội dung mới, kiểu chữ vẫn giữ nguyên.
- Kéo hai đầu trên timeline cho độ dài đúng. **Mỗi chú thích hiện ít nhất 4 giây** (câu 2 dòng thì 5–6 giây).

Nếu đoạn tua quá ngắn so với số câu cần hiện, **giảm tốc độ tua** (ví dụ 16x → 10x) chứ đừng cắt chữ.

## Bước 3: nội dung chữ theo từng phần

Chú thích và tiêu đề viết bằng tiếng Anh như file hướng dẫn. Các chú thích ghép đoạn theo thứ tự:

**Phần 0: ảnh slide (35 giây)**
Tiêu đề lớn giữa (0:00–0:06): *Autoscaled YOLO26 Stream Pipeline on Google Cloud* (dòng nhỏ: tên nhóm · Cloud Computing · HCMUT)
- Lần lượt 5 chú thích, mỗi câu 5–6 giây, về luồng frame → Pub/Sub, worker GKE + YOLO26 + BigQuery, KEDA 1–8 pod, dead-letter sau 5 lần, và 3 kịch bản.

**Phần 1** (tiêu đề **PART 1 · INFRASTRUCTURE**)
1a: *Cloud Storage bucket that stores the video frames (empty before the demo).*
1b: *GKE Autopilot cluster: the worker deployment is running 1 pod, the minimum when the system is idle.*
- 1b cuối: *Pub/Sub, BigQuery and Artifact Registry are all created by one script: `infra/setup.sh`.*

**Phần 2** (tiêu đề **PART 2 · TRAFFIC BURST & AUTOSCALING**)
2a: *One pod processes about 7 frames per second.* rồi *Load plan: 3.5 fps for 2 min → 35 fps for 3 min (5× one pod) → 3.5 fps for 2 min. 7,140 frames in total.*
2b: *Light load: a single pod keeps up, the charts stay flat.*
- 2c: *Load jumps to 35 fps – the Pub/Sub backlog grows quickly.* và *KEDA reads the backlog from Cloud Monitoring and adds 1 pod for every 10 waiting messages.* Nhãn chỉ vào dòng `Pending`: *Pending = Autopilot is provisioning a new node*. Cuối 2c, nhãn *1 → 8 pods* và chú thích về độ trễ 1–2 phút của Monitoring.
2d: *8 pods now process faster than frames arrive – the backlog drains.*
2e: *Backlog back to 0.*
- 2f: *No more load: KEDA removes the extra pods and the deployment returns to 1 pod.* rồi *The whole run used only 0.83 pod-hours ≈ $0.045.*

**Phần 3** (tiêu đề **PART 3 · WORKER FAILURES**)
- 3a: *21 fps for 5 min (6,300 frames), while a script deletes a random worker pod every 30 seconds.* Nhãn chỉ vào dòng `deleted pod/…`: *A pod is killed*.
- 3b: nhãn *Killed pod* (vào `Terminating`), *Kubernetes starts a replacement* (vào `Pending`), và hai chú thích về ack sau khi lưu BigQuery, Pub/Sub giao lại sau 60 giây.
- 3c: *Pods keep getting killed for 5 minutes while KEDA keeps scaling with the load.*
- 3d: *Verification query in BigQuery after the run.*
- 3e (freeze): khung nổi *Published 6,300 · Processed 6,300 · Written twice 1 · Lost 0* và chú thích về view `detections_dedup`.

**Phần 4** (tiêu đề **PART 4 · CORRUPTED FRAMES & DEAD-LETTER QUEUE**)
4a: *7 fps for 5 min (2,100 frames); about 2% of them are random bytes, not valid images.*
4b: *Waiting for the metrics to reach Cloud Monitoring (1–2 min delay).*
- 4c: *A worker cannot decode a broken frame, so it returns the message to Pub/Sub.* rồi *Pub/Sub retries with a 5 s → 60 s backoff; after 5 failed attempts the message moves to `frames-dlq`.* Hai nhãn chỉ: *Messages moved to the dead-letter topic* (vào các cột xanh) và *Valid frames keep flowing – the queue never gets stuck* (vào đường acked).
- Hai ảnh BigQuery bạn vừa tìm thấy: khung nổi *Published 2,100 · Processed 2,060 · Dead-lettered 40 (1.9%) · Lost 0* (lên ảnh 1), và chú thích *Each dead-lettered frame was retried 5 times before moving to `frames-dlq`, and is saved in the BigQuery table `dead_letters`.* (lên ảnh 2).

**Phần 5** (tiêu đề **PART 5 · DETECTION RESULTS**)
5a: *`draw_boxes.py` reads the box coordinates stored in BigQuery and draws them on the original frames.*
- 5b: *YOLO26 detects 18–19 vehicles per frame.* (nhớ sửa số cho khớp ảnh bạn chọn).

**Phần 6** (tiêu đề **PART 6 · SUMMARY & CLEAN-UP**)
6a: *`collect.py` gathers the results of all 3 runs from BigQuery and Cloud Monitoring.*
- 6b: bảng tổng kết nổi giữa màn hình (bảng 3 dòng burst / kill / corrupt trong file hướng dẫn) và chú thích *No frame was lost in any scenario, and each run cost only a few cents.*
6c: *Deleting the GKE cluster with one command to stop all hourly charges.*
6d: *Cluster deleted.*

**Phần 7:** chữ lớn giữa màn hình *Thank you for watching!* (dòng nhỏ: link repo GitHub).

## Bước 4: huy hiệu tốc độ

Với mỗi đoạn tua (`x16`, `x6`, `x8`, `x4`, `x3`), tạo chữ vàng ở góc trên phải, kéo dài đúng bằng đoạn đó. Chỉ cần làm một cái rồi copy, sửa số.

## Bước 5: kiểm tra

Xem lại cả video một lượt, kiểm tra các điểm sau:
- Mỗi chú thích hiện đủ 4 giây.
- Chú thích **không che** biểu đồ hay dòng terminal đang được nói tới. Nếu che, nâng lên hoặc dời sang bên.
- Không còn đoạn `lost = 978` và `collect.py` báo lỗi.
- Thông báo chat ở cảnh 5 (và cảnh 3 nếu có) đã được che.

Bạn muốn mình viết sẵn khung nổi hoặc bảng tổng kết ở 6b dưới dạng chữ gọn để copy vào CapCut không?