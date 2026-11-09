"""YOLO26n on CPU with ONNX Runtime.

YOLO26 is end-to-end (NMS-free): the ONNX output is already the final box list,
shape [1, N, 6], each row = x1, y1, x2, y2, score, class_id in model-input pixels.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

import cv2
import numpy as np


class BadImage(ValueError):
    """Bytes are not a decodable image. Retrying will not help."""


@dataclass(frozen=True)
class Detection:
    class_name: str
    conf: float
    x1: float
    y1: float
    x2: float
    y2: float


def decode_image(data: bytes) -> np.ndarray:
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise BadImage(f"cannot decode image ({len(data)} bytes)")
    return img


def letterbox(img: np.ndarray, size: int) -> tuple[np.ndarray, float, int, int]:
    """Resize keeping aspect ratio and pad to size x size with gray.
    Returns the model input [1,3,size,size] float32 RGB 0..1, plus scale and padding to map boxes back."""
    h, w = img.shape[:2]
    scale = min(size / h, size / w)
    nh, nw = round(h * scale), round(w * scale)
    top, left = (size - nh) // 2, (size - nw) // 2
    canvas = np.full((size, size, 3), 114, np.uint8)
    canvas[top:top + nh, left:left + nw] = cv2.resize(img, (nw, nh))
    blob = canvas[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255
    return np.ascontiguousarray(blob), scale, left, top


def to_detections(output: np.ndarray, scale: float, left: int, top: int, img_shape: tuple[int, int],
                  names: list[str], conf_threshold: float) -> list[Detection]:
    rows = np.asarray(output).reshape(-1, output.shape[-1])
    if rows.shape[1] != 6:
        raise ValueError(f"expected end-to-end output [1, N, 6], got {output.shape}; export with YOLO26")
    h, w = img_shape
    result = []
    for x1, y1, x2, y2, score, cls in rows[rows[:, 4] >= conf_threshold]:
        c = int(cls)
        result.append(Detection(
            names[c] if c < len(names) else str(c), round(float(score), 3),
            round(float(np.clip((x1 - left) / scale, 0, w)), 1), round(float(np.clip((y1 - top) / scale, 0, h)), 1),
            round(float(np.clip((x2 - left) / scale, 0, w)), 1), round(float(np.clip((y2 - top) / scale, 0, h)), 1),
        ))
    return result


class Detector:
    def __init__(self, model_path: str, conf_threshold: float = 0.25):
        import onnxruntime as ort  # imported here so tests run without it

        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 1  # the pod has 1 vCPU
        self.session = ort.InferenceSession(model_path, opts, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.size = self.session.get_inputs()[0].shape[2]
        names = ast.literal_eval(self.session.get_modelmeta().custom_metadata_map["names"])  # {0: 'person', ...}
        self.names = [names[i] for i in sorted(names)]
        self.conf_threshold = conf_threshold

    def detect(self, img: np.ndarray) -> list[Detection]:
        blob, scale, left, top = letterbox(img, self.size)
        output = self.session.run(None, {self.input_name: blob})[0]
        return to_detections(output, scale, left, top, img.shape[:2], self.names, self.conf_threshold)
