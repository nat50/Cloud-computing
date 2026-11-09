"""Draw detected boxes on frames, for the slides.

  python tools/draw_boxes.py <run_id> [how_many]

Takes the frames with the most objects from BigQuery, downloads them from Cloud Storage,
writes reports/figures/boxes/<frame_id>.jpg.
"""

import os
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from common import load_env, split_gcs_uri  # noqa: E402

load_env()
from google.cloud import bigquery, storage  # noqa: E402

run_id, limit = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 5
project, dataset = os.environ["PROJECT_ID"], os.environ["DATASET"]
bq, gcs = bigquery.Client(project=project), storage.Client(project=project)
out = ROOT / "reports" / "figures" / "boxes"
out.mkdir(parents=True, exist_ok=True)

rows = bq.query(
    f"SELECT frame_id, gcs_uri, objects FROM `{project}.{dataset}.detections_dedup` "
    f"WHERE frame_id LIKE '%-{run_id}-%' ORDER BY num_objects DESC LIMIT {limit}").result()
for row in rows:
    bucket, name = split_gcs_uri(row["gcs_uri"])
    img = cv2.imdecode(np.frombuffer(gcs.bucket(bucket).blob(name).download_as_bytes(), np.uint8), cv2.IMREAD_COLOR)
    for o in row["objects"]:
        x1, y1, x2, y2 = (int(o[k]) for k in ("x1", "y1", "x2", "y2"))
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 200, 0), 2)
        cv2.putText(img, f"{o['class_name']} {o['conf']:.2f}", (x1, max(y1 - 5, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
    cv2.imwrite(str(out / f"{row['frame_id']}.jpg"), img)
    print(f"{row['frame_id']}: {len(row['objects'])} objects")
