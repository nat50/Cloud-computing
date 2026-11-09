"""Fake camera: read a video, upload each frame to Cloud Storage, publish one small message per frame.

  python src/producer.py --video data/traffic.mp4 --schedule 60:1
  python src/producer.py --video data/traffic.mp4 --schedule 120:2,180:20,120:2 --corrupt-rate 0.02

--schedule is a list of duration_seconds:frames_per_second segments.
Reads PROJECT_ID, BUCKET, TOPIC from .env. Run `gcloud auth application-default login` once.
"""

from __future__ import annotations

import argparse
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor

import cv2

from common import FrameMessage, env, load_env, log, setup_logging, utc_now


def parse_schedule(text: str) -> list[tuple[float, float]]:
    """'60:2,120:20' -> [(60, 2), (120, 20)]"""
    segments = [tuple(map(float, part.split(":"))) for part in text.split(",")]
    if not segments or any(len(s) != 2 or s[0] <= 0 or s[1] < 0 for s in segments):
        raise ValueError(f"bad schedule {text!r}, expected e.g. 60:2,120:20")
    return segments


def send_times(schedule: list[tuple[float, float]]) -> list[float]:
    """Seconds after start at which each frame is sent."""
    times, start = [], 0.0
    for duration, fps in schedule:
        times += [start + i / fps for i in range(int(duration * fps))] if fps else []
        start += duration
    return times


def video_frames(path: str, width: int = 640):
    """JPEG bytes of each frame, looping the video forever."""
    cap = cv2.VideoCapture(path)
    while True:
        ok, frame = cap.read()
        if not ok:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = cap.read()
            if not ok:
                raise SystemExit(f"cannot read video {path}")
        h, w = frame.shape[:2]
        if w > width:
            frame = cv2.resize(frame, (width, round(h * width / w)))
        yield cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--video", required=True)
    p.add_argument("--schedule", required=True, help="e.g. 60:2,120:20")
    p.add_argument("--corrupt-rate", type=float, default=0.0, help="fraction of frames sent as broken bytes")
    p.add_argument("--run-id", default=time.strftime("%Y%m%d-%H%M%S"), help="part of every frame_id")
    p.add_argument("--camera-id", default="cam01")
    args = p.parse_args()

    load_env()
    logger = setup_logging()
    from google.cloud import pubsub_v1, storage

    project, bucket_name = env("PROJECT_ID"), env("BUCKET")
    bucket = storage.Client(project=project).bucket(bucket_name)
    publisher = pubsub_v1.PublisherClient()
    topic = publisher.topic_path(project, env("TOPIC", "frames"))
    times = send_times(parse_schedule(args.schedule))
    failed = 0

    def send(seq: int, jpeg: bytes) -> None:
        nonlocal failed
        frame_id = f"{args.camera_id}-{args.run_id}-{seq:06d}"
        name = f"frames/{args.run_id}/{frame_id}.jpg"
        payload = os.urandom(2048) if random.random() < args.corrupt_rate else jpeg
        try:
            bucket.blob(name).upload_from_string(payload, content_type="image/jpeg")
            msg = FrameMessage(frame_id, args.camera_id, f"gs://{bucket_name}/{name}", utc_now())
            publisher.publish(topic, msg.to_bytes()).result(timeout=60)
        except Exception as e:
            failed += 1
            log(logger, "send failed", frame_id=frame_id, error=repr(e))

    log(logger, "start", run_id=args.run_id, frames=len(times), schedule=args.schedule)
    frames, start = video_frames(args.video), time.monotonic()
    # Uploads run in parallel threads; the main loop only keeps the send rate.
    with ThreadPoolExecutor(max_workers=16) as pool:
        for seq, at in enumerate(times):
            jpeg = next(frames)
            time.sleep(max(0.0, start + at - time.monotonic()))
            pool.submit(send, seq, jpeg)
            if seq % 200 == 0:
                log(logger, "progress", sent=seq, elapsed_s=round(time.monotonic() - start))
    log(logger, "done", run_id=args.run_id, sent=len(times) - failed, failed=failed)


if __name__ == "__main__":
    main()
