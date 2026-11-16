# Hướng dẫn chạy demo trên Google Cloud

Hạ tầng dựng bằng **Google Cloud Console** (https://console.cloud.google.com), không dùng Cloud Shell. Terminal **Git Bash** trên máy chỉ dùng cho: build image, cài KEDA + deploy, chạy producer.

**Tiền:** chỉ cluster GKE tốn tiền (~0,054 USD/giờ mỗi pod). Quay xong xoá cluster ngay (mục 6).

> Tên tài nguyên **in đậm** phải gõ đúng vì code và script dựa vào chúng. Mọi thứ dùng region **us-central1**. Tên nút trên Console có thể khác chút.

---

## 1. Chuẩn bị (một lần)

**Trên web:** tạo project, ghi lại **Project ID** và **Project number** (*Dashboard → Project info*). Tạo budget 30 USD (*Billing → Budgets & alerts*). Bật API bằng một link (thay `PROJECT_ID`):
```
https://console.cloud.google.com/flows/enableapi?apiid=pubsub.googleapis.com,storage.googleapis.com,bigquery.googleapis.com,container.googleapis.com,artifactregistry.googleapis.com,monitoring.googleapis.com&project=PROJECT_ID
```

**Trên máy:** cài Google Cloud CLI (`gcloud components install kubectl gke-gcloud-auth-plugin`), Helm, Docker Desktop, Python 3.11, ffmpeg.
```bash
gcloud auth login
gcloud auth application-default login
cp .env.example .env                       # chỉ sửa PROJECT_ID
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt ultralytics

mkdir -p data
ffmpeg -i video_tai_ve.mp4 -t 120 -vf scale=-2:720 -an data/traffic.mp4    # video giao thông Pexels/Pixabay
ffmpeg -i data/traffic.mp4 -ss 5 -frames:v 1 data/sample.jpg
python models/export_yolo26.py data/sample.jpg
```
Ghi lại `ms/frame` in ra; tốc độ một pod khoảng **C ≈ 1000 / ms** (frame/s), dùng ở mục 4.

## 2. Dựng hạ tầng trên Console

**Bucket:** *Cloud Storage → Create*: tên **`PROJECT_ID-yolo-frames`**, Region `us-central1`.

**BigQuery:** *BigQuery → Studio*, ⋮ cạnh project → *Create dataset*: **`yolo_pipeline`**, `us-central1`. Mở query mới, chạy (thay `PROJECT_ID`):
```sql
CREATE TABLE `PROJECT_ID.yolo_pipeline.detections` (
  frame_id STRING NOT NULL, camera_id STRING, gcs_uri STRING, num_objects INT64,
  objects ARRAY<STRUCT<class_id INT64, class_name STRING, conf FLOAT64, x1 FLOAT64, y1 FLOAT64, x2 FLOAT64, y2 FLOAT64>>,
  worker_pod STRING, delivery_attempt INT64, download_ms FLOAT64, infer_ms FLOAT64,
  published_at TIMESTAMP, processed_at TIMESTAMP NOT NULL);
CREATE TABLE `PROJECT_ID.yolo_pipeline.frames_published` (
  subscription_name STRING, message_id STRING, publish_time TIMESTAMP, data STRING, attributes STRING);
CREATE TABLE `PROJECT_ID.yolo_pipeline.dead_letters` (
  subscription_name STRING, message_id STRING, publish_time TIMESTAMP, data STRING, attributes STRING);
```
Rồi mở [infra/bigquery/views.sql](../infra/bigquery/views.sql), thay `__DATASET__` bằng `PROJECT_ID.yolo_pipeline`, dán và chạy (tạo 3 view).

**Pub/Sub topic:** *Pub/Sub → Topics → Create topic*, bỏ chọn *Add a default subscription*: **`frames`** và **`frames-dlq`**.

**Quyền cho Pub/Sub:** tài khoản của Pub/Sub là `service-PROJECT_NUMBER@gcp-sa-pubsub.iam.gserviceaccount.com`.
- *IAM & Admin → IAM → Grant access*: tài khoản trên, role **BigQuery Data Editor**.
- Topic `frames-dlq` → *Show info panel → Permissions → Add principal*: tài khoản trên, role **Pub/Sub Publisher**.

**Subscription** (*Pub/Sub → Subscriptions → Create*):

| ID | Topic | Cài đặt |
|---|---|---|
| **`frames-workers`** | `frames` | Pull; ack deadline **60 s**; retry backoff 5 s → 60 s; Dead lettering bật, topic `frames-dlq`, tối đa **5** lần |
| **`frames-audit`** | `frames` | *Write to BigQuery* → bảng `frames_published`, bật **Write metadata** |
| **`dlq-audit`** | `frames-dlq` | *Write to BigQuery* → bảng `dead_letters`, bật **Write metadata** |

Sau khi tạo `frames-workers`, cấp thêm cho tài khoản Pub/Sub ở trên role **Pub/Sub Subscriber** trên subscription này (*Show info panel → Permissions*). Nếu báo permission denied hoặc tài khoản chưa tồn tại, đợi 2 phút (hoặc tạo subscription trước rồi cấp quyền) và thử lại.

**Artifact Registry:** *Create repository*: **`yolo`**, Docker, Region `us-central1`.

**Service account** (*IAM & Admin → Service accounts*):
- **`yolo-worker`**: Pub/Sub Subscriber, Storage Object Viewer, BigQuery Data Editor
- **`keda-operator`**: Monitoring Viewer

**Dashboard:** mở [monitoring/dashboard.json](../monitoring/dashboard.json), thay `__SUBSCRIPTION__` → `frames-workers`, `__NAMESPACE__` → `yolo`, `__TOPIC__` → `frames`. *Monitoring → Dashboards → Create custom dashboard* → ⚙ Settings → tab **JSON** → dán → *Apply changes*.

*(Cách nhanh bằng lệnh: `bash infra/setup.sh` làm toàn bộ mục 2.)*

## 3. Cluster, image, deploy

1. **Cluster:** *Kubernetes Engine → Clusters → Create* → **Autopilot**, tên **`yolo-cluster`**, `us-central1` (~10 phút).
2. **Terminal:**
   ```bash
   bash infra/cluster.sh build     # build + push image
   bash infra/cluster.sh up        # nối Workload Identity, cài KEDA, deploy worker
   ```
3. **Kiểm tra:** *Kubernetes Engine → Workloads*: `worker` (namespace `yolo`) 1/1 OK; bấm vào pod → tab *Logs* thấy `model loaded`.

Lỗi hay gặp: pod `Pending` vài phút là bình thường; `ImagePullBackOff` là chưa push image; log `403` là role chưa có hiệu lực, đợi 1–2 phút rồi chạy lại `bash infra/cluster.sh up`.

## 4. Chạy demo

Mở sẵn hai tab: *Workloads* (số pod của `worker`) và dashboard Monitoring (khung 1 giờ, auto-refresh).

```bash
# Chạy thử: 1 frame/s trong 1 phút
python tools/run_scenario.py smoke --video data/traffic.mp4

# Tải đột biến: pod tăng rồi giảm (thay <C> bằng số ở mục 1)
python tools/run_scenario.py burst --video data/traffic.mp4 --capacity <C>

# Worker chết: xoá pod ngẫu nhiên khi đang xử lý, không mất frame
python tools/run_scenario.py kill --video data/traffic.mp4 --capacity <C>

# Frame lỗi: ~2% ảnh hỏng, sang dead-letter
python tools/run_scenario.py corrupt --video data/traffic.mp4 --capacity <C>
```
Mỗi lệnh in `run_id` (dạng `20261109-101010`). Số pod tăng sau 1–3 phút (số liệu backlog trên Cloud Monitoring trễ), dừng tải vài phút sau giảm về 1.

**Kiểm chứng:** đợi 1 phút sau mỗi lần chạy, mở [infra/bigquery/verify.sql](../infra/bigquery/verify.sql) trong BigQuery, thay `PROJECT_ID` và `run_id`, chạy. Đúng khi `lost` = 0 (với `corrupt`, `dead_lettered` ≈ 2% số frame; với `kill`, `frames_written_twice` có thể > 0, view dedup đã lọc).

Ảnh có bounding box cho slide: `python tools/draw_boxes.py <run_id> 5` (ra `reports/figures/boxes/`).

Nếu KEDA không scale: `kubectl logs -n keda deploy/keda-operator --tail=30`. Lỗi `PermissionDenied` thì kiểm tra role của `keda-operator`. Cách dự phòng: `bash infra/cluster.sh fixed 1` rồi `kubectl autoscale deployment worker -n yolo --cpu-percent=70 --min=1 --max=8`.

## 5. Quay video

Màn hình chia đôi: *Workloads* (hoặc `kubectl get pods -n yolo -w`) và dashboard. Thứ tự: lướt qua Console (bucket, topic + 3 subscription, dataset, cluster) → `burst` → `kill` → `corrupt` → `verify.sql` cho thấy `lost` = 0 → ảnh bounding box. Chi tiết kịch bản: [PLAN.md](../PLAN.md) mục 7.

## 6. Dọn dẹp

*Kubernetes Engine → Clusters* → tick `yolo-cluster` → **Delete** (hoặc `bash infra/cluster.sh down`). Danh sách phải trống. Bucket, Pub/Sub, BigQuery giữ lại gần như không tốn tiền; lần sau chỉ làm lại mục 3. Xem chi phí ở *Billing → Reports* hôm sau.
