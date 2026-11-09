# Worker image. Needs yolo26n.onnx in models/ (python models/export_yolo26.py).
#   docker build -t <image> .
FROM python:3.11-slim

# Print logs immediately so Cloud Logging gets them in real time
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Dependencies first: this layer stays cached when only the code changes
COPY requirements-worker.txt .
RUN pip install --no-cache-dir -r requirements-worker.txt

COPY models/yolo26n.onnx src/common.py src/detector.py src/worker.py ./

# Run as a normal user, not root
USER 10001
CMD ["python", "worker.py"]
