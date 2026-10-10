# Cleaned-up training script for Apple Silicon (removes the unused/broken
# tensorflow import from the original repo script, and points explicitly
# at the Mac's GPU via "mps").
from ultralytics import YOLO

model = YOLO("yolov8s.pt")
results = model.train(
    data="../data.yaml",
    epochs=60,          # start smaller than the repo's default 100 to see results sooner;
                         # bump this up and re-run later if it looks promising
    imgsz=640,
    device="mps",        # Apple Silicon GPU
    batch=16,
    patience=15,
)
