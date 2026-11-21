# Kịch bản quay video demo (~6–8 phút thành phẩm)

> **Project ID:** `project001-480402` · **Region:** `us-central1` · **Capacity 1 pod (`C`):** `7` frame/s  
> Bám sát mục 7 của [PLAN.md](../PLAN.md) và [HUONG-DAN.md](HUONG-DAN.md).

---

## 0. Chuẩn bị trước khi bấm quay

- [ ] Kiểm tra pod `worker` đã về trạng thái sạch `1/1 Running`:
  ```powershell
  kubectl get pods -n yolo
  ```
- [ ] **Bố cục màn hình chia đôi (Split-Screen):**
  - **Nửa trái — 2 khung Terminal:**
    - Khung trên (theo dõi pod real-time):
      ```powershell
      kubectl get pods -n yolo -w
      ```
    - Khung dưới (đang bật `.venv` ở `F:\Cloud-computing`): dùng để gõ các lệnh demo.
  - **Nửa phải — Trình duyệt Google Cloud Console:** mở sẵn 4 tab theo đúng thứ tự ở **Cảnh 2** bên dưới.

---

## Cảnh 1 — Giới thiệu kiến trúc (30 giây)

- **Hiển thị:** Slide kiến trúc (Slide 4) hoặc sơ đồ luồng hệ thống.
- **Lời thuyết minh mẫu:**
  > *"Xin chào thầy/cô và các bạn. Hôm nay nhóm xin demo hệ thống xử lý luồng ảnh giao thông bằng YOLO26 tự động co giãn (autoscaling) trên Google Cloud. Producer đọc video, tải từng khung hình lên Cloud Storage và gửi tin nhắn vào Pub/Sub. Các Worker chạy mô hình YOLO26 ONNX trên GKE Autopilot rút tin nhắn về nhận diện và ghi kết quả vào BigQuery. KEDA theo dõi lượng tin nhắn tồn đọng trên Cloud Monitoring để tự động tăng giảm từ 1 đến 8 pod, còn ảnh lỗi được đẩy sang hàng đợi Dead-Letter."*

---

## Cảnh 2 — Lướt qua hạ tầng trên Google Cloud Console (45 giây)

Bấm lần lượt **4 tab** từ trái sang phải (~10 giây/tab):

1. **Tab 1 — BigQuery Studio** ([mở tab](https://console.cloud.google.com/bigquery?project=project001-480402)): chỉ dataset `yolo_pipeline` (3 bảng + 3 view), dán sẵn query ở Phụ lục để dùng lại cho Cảnh 4 & 5.
2. **Tab 2 — Artifact Registry** ([mở tab](https://console.cloud.google.com/artifacts?project=project001-480402)): chỉ kho `yolo` chứa image `worker:v1`.
3. **Tab 3 — GKE Workloads** ([mở tab](https://console.cloud.google.com/kubernetes/workload/overview?project=project001-480402)): chỉ `worker` đang `1/1 Running`, bấm tab **Logs** thấy `model loaded`.
4. **Tab 4 — Dashboard Monitoring** ([mở tab](https://console.cloud.google.com/monitoring/dashboards?project=project001-480402)): mở `YOLO26 Stream Pipeline` (khung **`15 phút`**, bật **Auto-refresh**), giữ nguyên tab này để nối thẳng sang **Cảnh 3 (`burst`)**.

---

## Cảnh 3 — Kịch bản 1: Tải đột biến & Autoscale (`burst`) (1,5 phút sau khi tua)

- **Bố cục:** Trái là `kubectl get pods -n yolo -w`, phải là Dashboard **YOLO26 Stream Pipeline**.
- **Lệnh chạy:**
  ```powershell
  python tools/run_scenario.py burst --video data/traffic.mp4 --capacity 7
  ```
- **Ghi lại `run_id`** in ra trên terminal.
- **Diễn biến cần quay rõ** *(tua nhanh `x4`–`x8` ở đoạn chờ)*:
  1. **2 phút đầu (3.5 fps):** 1 pod xử lý dư sức, backlog gần `0`.
  2. **3 phút tải đột biến (35 fps):**
     - Biểu đồ **Backlog** vọt lên.
     - Cửa sổ trái xuất hiện các pod mới (`Pending` → `ContainerCreating` → `Running`), tăng từ **1 → 8 pod**.
     - Biểu đồ **Worker pods running** và **Worker CPU** tăng theo, sau đó **Backlog** giảm nhanh.
  3. **2 phút hạ tải + 3 phút kết thúc:** producer dừng → backlog về `0` → các pod dư chuyển sang `Terminating` và **tự giảm về 1 pod** *(chứng minh scale-down khi rảnh)*.
- **Lời thuyết minh mẫu:**
  > *"Ở kịch bản burst, tải tăng đột ngột gấp 5 lần năng lực 1 pod lên 35 frame/giây. Sau độ trễ metric khoảng 1–2 phút của Cloud Monitoring, KEDA lập tức tăng số pod từ 1 lên tối đa 8 pod để xử lý nhanh hàng đợi tồn đọng. Khi tải giảm và dừng hẳn, hệ thống tự động thu hồi về lại 1 pod tối thiểu để tối ưu chi phí."*

---

## Cảnh 4 — Kịch bản 2: Worker chết giữa chừng (`kill`) (1 phút sau khi tua)

- **Lệnh chạy:**
  ```powershell
  python tools/run_scenario.py kill --video data/traffic.mp4 --capacity 7
  ```
- **Ghi lại `run_id`** in ra trên terminal.
- **Diễn biến cần quay rõ:**
  - Terminal in liên tục `deleted pod/worker-...` mỗi 30 giây.
  - Cửa sổ `kubectl get pods -n yolo -w` cho thấy pod bị `Terminating` và Kubernetes lập tức tạo pod mới thay thế.
  - **Đợi 1 phút sau khi xong**, chuyển sang **BigQuery** chạy query kiểm chứng với `run_id` của lần `kill`:
    - Chỉ rõ **`lost = 0`** (không mất frame nào).
    - Nếu `frames_written_twice > 0`, giải thích: cơ chế *at-least-once* của Pub/Sub giao lại frame khi pod chết, và view `detections_dedup` đã tự động loại trùng.

---

## Cảnh 5 — Kịch bản 3: Frame lỗi & Dead-Letter Queue (`corrupt`) (1 phút sau khi tua)

- **Lệnh chạy:**
  ```powershell
  python tools/run_scenario.py corrupt --video data/traffic.mp4 --capacity 7
  ```
- **Ghi lại `run_id`** in ra trên terminal.
- **Diễn biến cần quay rõ:**
  - Trên Dashboard Monitoring: chỉ vào biểu đồ **Dead-lettered messages** có cột tăng lên, trong khi các frame hợp lệ vẫn xử lý bình thường, hàng đợi không bị kẹt.
  - **Đợi 1 phút sau khi xong**, chạy query kiểm chứng trên **BigQuery** với `run_id` của lần `corrupt`:
    - Chỉ rõ **`lost = 0`** và **`dead_lettered` ≈ 2%** số `published`.
  - *(Tùy chọn)* Chạy nhanh query xem chi tiết bảng dead-letter:
    ```sql
    SELECT * FROM `project001-480402.yolo_pipeline.dead_letters_v` LIMIT 10;
    ```
    Chỉ vào cột `delivery_count = 5` (thử lại 5 lần thất bại mới chuyển sang DLQ).

---

## Cảnh 6 — Ảnh kết quả nhận diện Bounding Box (30 giây)

- **Lệnh chạy** (thay `<RUN_ID>` bằng mã của lần `burst` hoặc `corrupt`):
  ```powershell
  python tools/draw_boxes.py <RUN_ID> 5
  ```
- **Thao tác:** Mở thư mục `reports/figures/boxes/` và lướt qua 3–5 ảnh `.jpg` có bounding box (`car`, `truck`, `bus`... kèm điểm confidence).
- **Lời thuyết minh mẫu:**
  > *"Đây là các khung hình thực tế được vẽ lại bounding box trực tiếp từ tọa độ mà worker YOLO26 đã ghi vào BigQuery."*

---

## Cảnh 7 — Thu số liệu báo cáo, dọn dẹp cluster & Kết luận (30 giây)

- **Trước khi xóa cluster** (để lấy CSV + biểu đồ cho báo cáo/slide, có thể làm ngoài đoạn quay hoặc quay lướt):
  ```powershell
  python tools/collect.py reports/results/<ten_thu_muc_burst>
  python tools/collect.py reports/results/<ten_thu_muc_kill>
  python tools/collect.py reports/results/<ten_thu_muc_corrupt>
  ```
- **Lệnh xóa cluster (quay lại bước này cho kết video):**
  ```powershell
  & "C:\Program Files\Git\bin\bash.exe" infra/cluster.sh down
  ```
- **Lời thuyết minh mẫu:**
  > *"Cuối cùng, nhóm xóa cluster GKE bằng một lệnh duy nhất để dừng phát sinh chi phí, trong khi toàn bộ dữ liệu kết quả trên BigQuery và Dashboard vẫn được giữ lại. Cảm ơn thầy/cô và các bạn đã theo dõi!"*

---

## Phụ lục: Query kiểm chứng BigQuery (dán sẵn vào BigQuery Studio)

Chỉ cần thay `THAY_RUN_ID_VAO_DAY` bằng `run_id` của từng lần chạy rồi bấm **Run**:

```sql
DECLARE run_id STRING DEFAULT 'THAY_RUN_ID_VAO_DAY';

WITH
pub AS (
  SELECT DISTINCT frame_id FROM `project001-480402.yolo_pipeline.frames_published_v`
  WHERE frame_id LIKE CONCAT('%-', run_id, '-%')
),
det AS (
  SELECT frame_id, COUNT(*) AS n FROM `project001-480402.yolo_pipeline.detections`
  WHERE frame_id LIKE CONCAT('%-', run_id, '-%')
  GROUP BY frame_id
),
dead AS (
  SELECT DISTINCT frame_id FROM `project001-480402.yolo_pipeline.dead_letters_v`
  WHERE frame_id LIKE CONCAT('%-', run_id, '-%')
)
SELECT
  (SELECT COUNT(*) FROM pub) AS published,
  (SELECT COUNT(*) FROM det) AS processed,
  (SELECT IFNULL(SUM(n), 0) FROM det) AS raw_rows,
  (SELECT COUNTIF(n > 1) FROM det) AS frames_written_twice,
  (SELECT COUNT(*) FROM dead) AS dead_lettered,
  (SELECT COUNT(*) FROM pub
     WHERE frame_id NOT IN (SELECT frame_id FROM det)
       AND frame_id NOT IN (SELECT frame_id FROM dead)) AS lost;
```

## Mẹo hậu kỳ
- Quay màn hình trọn vẹn trước, sau đó **tua nhanh `x4`–`x8`** các đoạn chờ scale/chạy tải (gắn nhãn `x4` ở góc màn hình) để tổng thời lượng thành phẩm gọn trong **6–8 phút**.
- Thu âm lồng tiếng hoặc thêm phụ đề ngắn cho từng bước sau khi cắt ghép sẽ mượt và rõ hơn vừa gõ vừa nói.
