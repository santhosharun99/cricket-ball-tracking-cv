# resume_yolo26.py - restarts training from the last checkpoint in the
# newest run folder, picking up exactly where it left off (same settings,
# same progress). Used automatically by auto_restart_training.sh.
import glob, os
from ultralytics import YOLO

if __name__ == "__main__":
    runs = sorted(glob.glob(os.path.expanduser("~/runs/detect/yolo26_combined*")), key=os.path.getmtime)
    latest = runs[-1]
    print(f"Resuming from: {latest}")
    model = YOLO(os.path.join(latest, "weights", "last.pt"))
    model.train(resume=True)
