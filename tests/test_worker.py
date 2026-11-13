"""Unit tests, no GCP needed:  python -m pytest"""

import cv2
import numpy as np
import pytest

from common import FrameMessage, InvalidMessage
from detector import Detection, letterbox, to_detections
from producer import parse_schedule, send_times
from worker import Handler

JPEG = cv2.imencode(".jpg", np.zeros((10, 10, 3), np.uint8))[1].tobytes()
FRAME = FrameMessage("cam01-r1-000001", "cam01", "gs://b/f.jpg", "2026-11-09T10:00:00.000+00:00")


class FakeMessage:
    def __init__(self, data):
        self.data, self.delivery_attempt, self.result = data, 1, None

    def ack(self):
        self.result = "ack"

    def nack(self):
        self.result = "nack"


def run(data, download=lambda uri: JPEG, write_ok=True):
    rows = []

    def write_row(row):
        if not write_ok:
            raise ConnectionError("BigQuery down")
        rows.append(row)

    msg = FakeMessage(data)
    Handler(download, lambda img: [Detection(2, "car", 0.9, 1, 2, 3, 4)], write_row, "pod-a")(msg)
    return msg.result, rows


def test_ack_only_after_write():
    result, rows = run(FRAME.to_bytes())
    assert result == "ack" and rows[0]["frame_id"] == FRAME.frame_id and rows[0]["num_objects"] == 1
    assert rows[0]["objects"][0]["class_id"] == 2


def test_nack_when_write_fails():
    assert run(FRAME.to_bytes(), write_ok=False) == ("nack", [])


def test_nack_on_broken_image_or_message():
    assert run(FRAME.to_bytes(), download=lambda uri: b"garbage") == ("nack", [])
    assert run(b"not json") == ("nack", [])
    with pytest.raises(InvalidMessage):
        FrameMessage.from_bytes(b'{"frame_id": "x"}')


def test_boxes_map_back_to_original_image():
    img = np.zeros((720, 1280, 3), np.uint8)
    blob, scale, left, top = letterbox(img, 640)  # scale 0.5, 140 px gray band top and bottom
    assert blob.shape == (1, 3, 640, 640) and (scale, left, top) == (0.5, 0, 140)
    out = np.zeros((1, 300, 6), np.float32)
    out[0, 0] = [100, 190, 200, 290, 0.9, 2]  # kept
    out[0, 1] = [0, 0, 10, 10, 0.1, 0]  # below threshold
    [d] = to_detections(out, scale, left, top, (720, 1280), ["person", "bicycle", "car"], 0.25)
    assert (d.class_id, d.class_name, d.x1, d.y1, d.x2, d.y2) == (2, "car", 200, 100, 400, 300)


def test_schedule():
    assert send_times(parse_schedule("2:2,1:0,1:4")) == [0, 0.5, 1, 1.5, 3, 3.25, 3.5, 3.75]
