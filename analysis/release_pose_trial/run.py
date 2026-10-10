"""
release_pose_trial: does the bowler's wrist (mediapipe pose) actually separate from the
ball right around the reviewed release frame? Single-clip proof of concept before
committing to all five.

Clip: C1 (f81d092b...), reviewed release interval 90-91 (last-attached to first-detached,
per the project notes). FPS 25.

Inputs (read-only):
  - video: Downloads/cricket_project/data/videos/f81d092b...mp4
  - ball candidates: analysis/event_timing_trial/raw_detections.json (the cached YOLO26
    detections, frames 50-115, reused as-is, not re-detected)

Method: for each frame in a window around release, run mediapipe legacy Pose solution
(static_image_mode=True, CPU, XNNPACK delegate - no EGL, no external model download needed,
bundled in mediapipe==0.10.14) on the full frame. Record both wrist landmarks (15=left,
16=right) in pixel coords. For each frame, find the ball candidate (from the cached list)
nearest to whichever wrist is closer overall across the window (bowling-arm side is not
known in advance, so both wrists are recorded and reported; the analysis picks whichever
wrist stays consistently close pre-release then diverges, and says so explicitly if neither
does).

This is a first look, not a finished detector. Output is saved for honest visual review.
"""
import json
import os

import cv2
import mediapipe as mp

ROOT = "/sessions/rcw-01sdoihp2zrszjau8ic1eu6t/mnt/g-p-6aad6939d0788191871c4d92556ac2d1"
VIDEO = "/sessions/rcw-01sdoihp2zrszjau8ic1eu6t/mnt/Downloads/cricket_project/data/videos/f81d092b6117be1126e0d6be97220b3f9a2870eb.mp4"
OUT_DIR = os.path.join(ROOT, "analysis", "release_pose_trial")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, "frames"), exist_ok=True)

REVIEWED_RELEASE = (90, 91)  # last-attached .. first-detached, from the project notes
WINDOW = range(80, 100)  # frames to inspect

# load the cached ball candidates for C1
with open(os.path.join(ROOT, "analysis", "event_timing_trial", "raw_detections.json")) as f:
    raw = json.load(f)
ball_by_frame = {}
for row in raw:
    if row["clip"] == "C1":
        ball_by_frame[row["frame"]] = row["candidates"]

pose = mp.solutions.pose.Pose(static_image_mode=True, model_complexity=1, min_detection_confidence=0.3)

cap = cv2.VideoCapture(VIDEO)
if not cap.isOpened():
    raise SystemExit(f"could not open {VIDEO}")

results = []
for frame_idx in WINDOW:
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ok, frame = cap.read()
    if not ok:
        results.append({"frame": frame_idx, "error": "frame_read_failed"})
        continue
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pose_result = pose.process(rgb)

    entry = {"frame": frame_idx, "ball_candidates": ball_by_frame.get(frame_idx, [])}

    if pose_result.pose_landmarks:
        lm = pose_result.pose_landmarks.landmark
        left_wrist = lm[15]
        right_wrist = lm[16]
        entry["left_wrist_px"] = [left_wrist.x * w, left_wrist.y * h, left_wrist.visibility]
        entry["right_wrist_px"] = [right_wrist.x * w, right_wrist.y * h, right_wrist.visibility]

        annotated = frame.copy()
        mp.solutions.drawing_utils.draw_landmarks(
            annotated, pose_result.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS
        )
        for cx, cy, cconf in entry["ball_candidates"]:
            cv2.circle(annotated, (int(cx), int(cy)), 6, (0, 0, 255), 2)
            cv2.putText(annotated, f"ball {cconf:.2f}", (int(cx) + 8, int(cy)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.imwrite(os.path.join(OUT_DIR, "frames", f"f{frame_idx:03d}.jpg"), annotated)
    else:
        entry["left_wrist_px"] = None
        entry["right_wrist_px"] = None
        cv2.imwrite(os.path.join(OUT_DIR, "frames", f"f{frame_idx:03d}_nopose.jpg"), frame)

    results.append(entry)

cap.release()

with open(os.path.join(OUT_DIR, "results.json"), "w") as f:
    json.dump({"clip": "C1", "reviewed_release": REVIEWED_RELEASE, "results": results}, f, indent=2)

# quick console summary: nearest ball candidate distance to each wrist per frame
import math

def nearest_dist(wrist, candidates):
    if wrist is None or not candidates:
        return None
    wx, wy, _ = wrist
    return min(math.hypot(wx - cx, wy - cy) for cx, cy, _ in candidates)

print(f"{'frame':>5} {'pose?':>6} {'L-wrist->ball px':>18} {'R-wrist->ball px':>18}")
for e in results:
    if "error" in e:
        print(f"{e['frame']:>5}  FRAME READ FAILED")
        continue
    has_pose = e["left_wrist_px"] is not None
    ld = nearest_dist(e["left_wrist_px"], e["ball_candidates"])
    rd = nearest_dist(e["right_wrist_px"], e["ball_candidates"])
    marker = " <= reviewed release" if e["frame"] in REVIEWED_RELEASE else ""
    print(f"{e['frame']:>5} {str(has_pose):>6} {str(round(ld,1)) if ld else '-':>18} {str(round(rd,1)) if rd else '-':>18}{marker}")
