"""Export YOLO26n to ONNX (once) and check it on an image.

  pip install ultralytics
  python models/export_yolo26.py data/sample.jpg

Writes models/yolo26n.onnx (git-ignored; the Dockerfile copies it into the image).
Prints the output shape (expected [1, 300, 6]) and the CPU time per frame.
"""

import shutil
import sys
import time
from pathlib import Path

import cv2
from ultralytics import YOLO

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
from detector import Detector  # noqa: E402

onnx = HERE / "yolo26n.onnx"
shutil.move(YOLO("yolo26n.pt").export(format="onnx", imgsz=640), onnx)  # downloads yolo26n.pt the first time

det = Detector(str(onnx))
print("output shape:", det.session.get_outputs()[0].shape)
img = cv2.imread(sys.argv[1])
det.detect(img)  # warm-up
t0 = time.perf_counter()
for _ in range(20):
    boxes = det.detect(img)
print(f"{(time.perf_counter() - t0) * 50:.1f} ms/frame on 1 CPU thread, {len(boxes)} objects:")
for b in boxes:
    print(f"  {b.class_name:<12} {b.conf:.2f}")
