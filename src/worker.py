"""Worker: pull a frame message, download the image, run YOLO26n, write to BigQuery, then ACK.

Run in the container as `python worker.py`. Environment (set in k8s/worker.yaml):
  PROJECT_ID, SUBSCRIPTION, BQ_TABLE, MODEL_PATH, POD_NAME
"""

from __future__ import annotations

import logging
import socket
import signal
import threading
import time
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from common import FrameMessage, InvalidMessage, env, log, setup_logging, split_gcs_uri, utc_now
from detector import BadImage, Detector, decode_image

logger = logging.getLogger("app")


class Handler:
    """Processes one Pub/Sub message. ACK only after the result is written.

    Any failure -> NACK -> Pub/Sub redelivers (maybe to another pod).
    After 5 failed deliveries Pub/Sub moves the message to the dead-letter topic.
    GCP calls are passed in, so this class is tested without GCP (tests/test_worker.py).
    """

    def __init__(self, download, detect, write_row, pod_name: str):
        self.download, self.detect, self.write_row, self.pod_name = download, detect, write_row, pod_name

    def __call__(self, message) -> None:
        attempt = message.delivery_attempt or 1
        try:
            frame = FrameMessage.from_bytes(message.data)
            t0 = time.perf_counter()
            img = decode_image(self.download(frame.gcs_uri))
            t1 = time.perf_counter()
            objects = self.detect(img)
            t2 = time.perf_counter()
            row = {
                "frame_id": frame.frame_id,
                "camera_id": frame.camera_id,
                "gcs_uri": frame.gcs_uri,
                "num_objects": len(objects),
                "objects": [asdict(o) for o in objects],
                "worker_pod": self.pod_name,
                "delivery_attempt": attempt,
                "download_ms": round((t1 - t0) * 1000, 1),
                "infer_ms": round((t2 - t1) * 1000, 1),
                "published_at": frame.published_at,
                "processed_at": utc_now(),
            }
            self.write_row(row)
        except (InvalidMessage, BadImage) as e:  # broken frame: will end in the dead-letter topic
            log(logger, "bad frame", logging.WARNING, attempt=attempt, error=str(e))
            message.nack()
            return
        except Exception as e:  # network / BigQuery error: retry
            log(logger, "processing failed", logging.ERROR, attempt=attempt, error=repr(e))
            message.nack()
            return
        message.ack()
        log(logger, "frame done", frame_id=row["frame_id"], attempt=attempt, objects=row["num_objects"],
            infer_ms=row["infer_ms"], download_ms=row["download_ms"])


def main() -> None:
    setup_logging()
    from google.cloud import bigquery, pubsub_v1, storage

    project, table = env("PROJECT_ID"), env("BQ_TABLE")
    ready = threading.Event()

    # /healthz returns 200 only after the model is loaded: Kubernetes counts the pod as ready from then on.
    class Health(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200 if ready.is_set() else 503)
            self.end_headers()

        def log_message(self, *args):
            pass

    threading.Thread(target=ThreadingHTTPServer(("", 8080), Health).serve_forever, daemon=True).start()

    t0 = time.perf_counter()
    detector = Detector(env("MODEL_PATH", "/app/yolo26n.onnx"))
    log(logger, "model loaded", model_load_ms=round((time.perf_counter() - t0) * 1000))

    gcs, bq = storage.Client(project=project), bigquery.Client(project=project)

    def download(uri: str) -> bytes:
        bucket, name = split_gcs_uri(uri)
        return gcs.bucket(bucket).blob(name).download_as_bytes()

    def write_row(row: dict) -> None:
        # row_ids = frame_id: BigQuery drops a duplicate insert of the same frame sent shortly after.
        errors = bq.insert_rows_json(table, [row], row_ids=[row["frame_id"]])
        if errors:
            raise RuntimeError(f"BigQuery insert failed: {errors}")

    handler = Handler(download, detector.detect, write_row, env("POD_NAME", socket.gethostname()))
    subscriber = pubsub_v1.SubscriberClient()
    subscription = subscriber.subscription_path(project, env("SUBSCRIPTION", "frames-workers"))
    # Flow control: at most 1 unacked message per pod. Otherwise one pod would lease a big part
    # of the backlog and adding pods would not help. The client extends the ack deadline while we work.
    future = subscriber.subscribe(subscription, callback=handler,
                                  flow_control=pubsub_v1.types.FlowControl(max_messages=1))

    def shutdown(*_):  # pod deleted / scaled down: stop pulling; unacked messages go to other pods
        ready.clear()
        future.cancel()

    signal.signal(signal.SIGTERM, shutdown)
    ready.set()
    log(logger, "listening", subscription=subscription)
    try:
        future.result()
    except Exception:
        if not future.cancelled():
            raise
    finally:
        subscriber.close()


if __name__ == "__main__":
    main()
