# Training script for YOLO26 on the COMBINED dataset (old Kaggle set +
# a thinned-out slice of the new Roboflow set), on Apple Silicon.
#
# History of fixes to this script, so it's clear why it looks like this:
#   1. Originally used cache="disk" to speed up image loading - backfired,
#      each round got steadily slower (round 1: ~11 min, round 10: 5+
#      hours), almost certainly a memory build-up. Removed.
#   2. Then workers=8 was added back in without the "if __name__ ==
#      '__main__'" guard below. On a Mac, using multiple background
#      helper processes to load images requires that guard - without it,
#      each helper process re-runs this whole file from the top instead
#      of just loading images, which looks like the whole thing freezing.
#      Fixed by moving the training call inside the guard.
#
# Needs an up-to-date ultralytics package - run:
#   pip install -U ultralytics
# before running this, since YOLO26 support is newer than what was
# installed for the earlier YOLOv8 run.
from ultralytics import YOLO

if __name__ == "__main__":
    model = YOLO("yolo26s.pt")   # auto-downloads the pretrained weights on first run
    results = model.train(
        data="../data_combined_fast.yaml",
        epochs=60,
        imgsz=640,
        device="mps",   # Apple Silicon GPU
        batch=16,
        patience=15,
        workers=8,
        name="yolo26_combined",
    )
