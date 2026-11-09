# Hướng dẫn chạy trên Google Cloud

Làm theo thứ tự. Các lệnh chạy từ thư mục gốc repo, bằng **Git Bash** (Windows) hoặc **Cloud Shell**.

**Tiền:** chỉ cluster GKE là tốn tiền đáng kể (~0,054 USD/giờ mỗi pod). Xong buổi nào chạy `bash infra/cluster.sh down` buổi đó.

---

## 1. Chuẩn bị (một lần)

**Công cụ:** Google Cloud CLI, `gcloud components install kubectl gke-gcloud-auth-plugin`, Helm (`winget install Helm.Helm`), Docker Desktop, Python 3.11. Nếu Git Bash lỗi với `gcloud`, dùng Cloud Shell (có sẵn tất cả).

```bash
gcloud auth login
gcloud auth application-default login      # cho code Python
cp .env.example .env                       # sửa PROJECT_ID
python -m venv .venv && source .venv/Scripts/activate   # Cloud Shell: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest                           # 5 passed
```

**Budget alert** (làm tay, 1 phút): Billing → Budgets & alerts → Create budget → chọn project → 30 USD → ngưỡng 33%, 66%, 100%.

**Video và model:**
```bash
mkdir -p data
# tải 1 video giao thông từ Pexels/Pixabay, cắt 2 phút 720p:
ffmpeg -i video_tai_ve.mp4 -t 120 -vf scale=-2:720 -an data/traffic.mp4
ffmpeg -i data/traffic.mp4 -ss 5 -frames:v 1 data/sample.jpg
pip install ultralytics
python models/export_yolo26.py data/sample.jpg
```
Ghi lại 2 số in ra: `output shape` (phải là `[1, 300, 6]`) và `ms/frame`.

## 2. Dựng hạ tầng (một lần)

```bash
bash infra/setup.sh
```
Tạo: bucket, topic `frames` + `frames-dlq`, subscription `frames-workers` (pull, ack 60 s, dead-letter sau 5 lần), `frames-audit` và `dlq-audit` (ghi thẳng vào BigQuery), dataset `yolo_pipeline`, Artifact Registry, 2 service account, dashboard Monitoring. Chạy lại không sao.

Kiểm tra:
```bash
gcloud pubsub subscriptions list --format="table(name,ackDeadlineSeconds,deadLetterPolicy.maxDeliveryAttempts,bigqueryConfig.table)"
```

| Lỗi | Xử lý |
|---|---|
| Tạo `frames-audit` báo permission denied | Quyền mới cấp chưa có hiệu lực; script tự thử lại, vẫn lỗi thì đợi 2 phút rồi chạy lại |
| `--bigquery-table` sai định dạng | Trong `setup.sh` đổi `$PROJECT_ID:$DATASET.xxx` thành `$PROJECT_ID.$DATASET.xxx` |

## 3. Build image và dựng cluster

```bash
bash infra/cluster.sh build      # build + push image worker
bash infra/cluster.sh up         # cluster Autopilot (~10 phút lần đầu) + KEDA + worker
kubectl get pods -n yolo         # READY 1/1
kubectl logs -n yolo -l app=worker --tail=5   # có "model loaded" và "listening"
```
Sửa code worker: tăng `IMAGE_TAG` trong `.env`, chạy `build` rồi `keda` (hoặc `fixed N`).

| Triệu chứng | Xử lý |
|---|---|
| Pod `Pending` vài phút | Bình thường, Autopilot đang thêm node |
| `ImagePullBackOff` | Chưa push hoặc sai `IMAGE_TAG` |
| Log `403` / `PermissionDenied` | Workload Identity chưa nối: chạy lại `bash infra/cluster.sh up` |

## 4. Chạy thử end-to-end

```bash
python tools/run_scenario.py smoke --video data/traffic.mp4
python tools/collect.py reports/results/<thư mục vừa in ra>
```
Đúng khi `published` = `processed` và `lost` = 0. Cùng số liệu xem được bằng cách dán `infra/bigquery/verify.sql` vào BigQuery console.

Ảnh có bounding box cho slide:
```bash
python tools/draw_boxes.py <run_id> 5      # -> reports/figures/boxes/
```

## 5. Kiểm tra KEDA

```bash
kubectl get scaledobject -n yolo           # READY True
kubectl get pods -n yolo -w                # để mở ở terminal khác
python src/producer.py --video data/traffic.mp4 --schedule 300:20
```
1–3 phút sau số pod tăng; dừng producer, vài phút sau giảm về 1. Chậm 1–2 phút là do số liệu backlog trên Cloud Monitoring trễ, ghi vào báo cáo.

KEDA không scale: `kubectl describe scaledobject worker -n yolo` và `kubectl logs -n keda deploy/keda-operator --tail=30`. Lỗi `PermissionDenied` thì chạy lại `bash infra/cluster.sh up`. Nếu KEDA không chạy được trên Autopilot, dùng HPA theo CPU:
```bash
bash infra/cluster.sh fixed 1
kubectl autoscale deployment worker -n yolo --cpu-percent=70 --min=1 --max=8
```

## 6. Kiểm thử (gom vào 1 buổi, ~2 giờ, < 2 USD)

**Đo C** (frame/s một pod xử lý được):
```bash
bash infra/cluster.sh fixed 1
python tools/run_scenario.py capacity --video data/traffic.mp4 --capacity 20 --label capacity
python tools/collect.py reports/results/<thư mục>
gcloud pubsub subscriptions seek frames-workers --time=$(date -u +%Y-%m-%dT%H:%M:%SZ)   # bỏ backlog còn tồn
```
`C` = `processed_per_s_max` trong `stats.json`. Bỏ qua `lost` của lần chạy này (do lệnh seek).

**So sánh cố định và KEDA:**
```bash
bash infra/cluster.sh fixed 1 && python tools/run_scenario.py burst --video data/traffic.mp4 --capacity <C> --label fixed1
bash infra/cluster.sh fixed 8 && python tools/run_scenario.py burst --video data/traffic.mp4 --capacity <C> --label fixed8
bash infra/cluster.sh keda    && python tools/run_scenario.py burst --video data/traffic.mp4 --capacity <C> --label keda
# collect từng thư mục, rồi:
python tools/collect.py --compare reports/results/*_burst_*      # -> reports/figures/compare_burst.png
```

**Các kịch bản còn lại** (chế độ `keda`):

| Kịch bản | Lệnh | Xem gì |
|---|---|---|
| Tải đều | `run_scenario.py steady ...` | pod tăng khi tải 3C, `lost` = 0 |
| Lúc rảnh | `run_scenario.py idle ...` | `timeline.png`: pod giảm về 1 sau khi dừng |
| Worker chết | `run_scenario.py kill ...` | `lost` = 0; `written_twice` có thể > 0 (bị view dedup lọc) |
| Frame lỗi | `run_scenario.py corrupt ...` | `dead_lettered` ≈ 2% số frame, backlog không kẹt |

Sau **mỗi** lần chạy, đợi 1 phút rồi `python tools/collect.py reports/results/<thư mục>`. Phải chạy trước khi xoá cluster. Commit cả thư mục `reports/results/` lên GitHub.

**Quay video demo trong buổi này:** trái là terminal `kubectl get pods -n yolo -w`, phải là dashboard Monitoring (khung 1 giờ, bật auto-refresh). Chạy `burst` và `kill` trong lúc quay, cuối cùng mở `verify.sql` cho thấy `lost` = 0.

## 7. Dọn dẹp

```bash
bash infra/cluster.sh down
gcloud container clusters list            # phải trống
```
Bucket, Pub/Sub, BigQuery giữ lại cho buổi sau (gần như không tốn tiền; ảnh tự xoá sau 7 ngày). Kiểm tra chi phí ở Billing → Reports vào hôm sau. Nộp bài xong mới xoá hẳn project: IAM & Admin → Settings → Shut down.
