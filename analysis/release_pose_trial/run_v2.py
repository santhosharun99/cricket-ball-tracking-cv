"""
release_pose_trial v2: extend the C1 proof-of-concept to all 5 clips, and try to close
the coverage gap found in v1 (frames right at the reviewed release window sometimes gave
no pose reading at all).

Changes from v1, and why:
  - static_image_mode=False (sequential/video mode) instead of True: mediapipe's video mode
    uses the previous frame's landmarks to help find the pose in the next one, which should
    be more robust through brief occlusion/motion-blur than treating every frame as an
    independent fresh image. Frames are still fed to it in increasing order within each clip.
  - model_complexity=2 (heaviest/most accurate) and lower min_detection_confidence=0.1 /
    min_tracking_confidence=0.1: v1 used complexity=1 and default 0.5 confidence, which is
    likely why frames 90-93 came up empty on C1. Compute is not the bottleneck here (a few
    hundred frames total on CPU), so trading speed for a better chance of a reading is fine.
  - Loops over C1, C3, C4, C5 (C2 has no reviewed release reference per the project notes
    section 3 - "C2 early flight/bounce cannot be reliably labelled" - so it is excluded from
    this scored comparison, same as the earlier experiments excluded it. Not silently dropped: this
    script prints why.

Ball positions: still the cached analysis/event_timing_trial/raw_detections.json,
reused as-is. No new YOLO inference, no network calls, no re-detection.
"""
import json
import math
import os

import cv2
import mediapipe as mp

ROOT = "/sessions/rcw-01sdoihp2zrszjau8ic1eu6t/mnt/g-p-6aad6939d0788191871c4d92556ac2d1"
VIDEO_DIR = "/sessions/rcw-01sdoihp2zrszjau8ic1eu6t/mnt/Downloads/cricket_project/data/videos"
OUT_DIR = os.path.join(ROOT, "analysis", "release_pose_trial")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, "frames_v2"), exist_ok=True)

CLIPS = {
    "C1": {"file": "f81d092b6117be1126e0d6be97220b3f9a2870eb.mp4", "release": (90, 91)},
    "C3": {"file": "98e537a2a3555da28ca7eea3227babb61df228d1.mp4", "release": (83, 84)},
    "C4": {"file": "6a79fbe0fd6792126c69087568f7f08318dcf449.mp4", "release": (92, 93)},
    "C5": {"file": "bad1530d039b7146a8ce4a1b1a6b29502c3c9491.mp4", "release": (73, 74)},
}
SKIPPED = {"C2": "no reviewed release reference exists (project notes section 3: early flight/bounce not reliably labelled)"}

with open(os.path.join(ROOT, "analysis", "event_timing_trial", "raw_detections.json")) as f:
    raw = json.load(f)
ball_by_clip_frame = {}
for row in raw:
    ball_by_clip_frame.setdefault(row["clip"], {})[row["frame"]] = row["candidates"]


def nearest_dist(wrist, candidates):
    if wrist is None or not candidates:
        return None
    wx, wy, _ = wrist
    return min(math.hypot(wx - cx, wy - cy) for cx, cy, _ in candidates)


all_results = {}

for clip_id, info in CLIPS.items():
    video_path = os.path.join(VIDEO_DIR, info["file"])
    rel_lo, rel_hi = info["release"]
    window = range(rel_lo - 10, rel_hi + 10)
    ball_by_frame = ball_by_clip_frame.get(clip_id, {})

    # fresh sequential pose tracker per clip (video mode relies on frame order within one clip)
    pose = mp.solutions.pose.Pose(
        static_image_mode=False,
        model_complexity=1,  # complexity=2 ("heavy") needs an on-demand download that is
        # blocked from this sandbox (same allowlist wall as the Tasks-API .task file) -
        # complexity=1 ("full") is bundled in the pip package already, per v1's working run.
        min_detection_confidence=0.1,
        min_tracking_confidence=0.1,
    )

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        all_results[clip_id] = {"error": f"could not open {video_path}"}
        continue

    clip_results = []
    for frame_idx in window:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ok, frame = cap.read()
        if not ok:
            clip_results.append({"frame": frame_idx, "error": "frame_read_failed"})
            continue
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pose_result = pose.process(rgb)

        entry = {"frame": frame_idx, "ball_candidates": ball_by_frame.get(frame_idx, [])}
        if pose_result.pose_landmarks:
            lm = pose_result.pose_landmarks.landmark
            lw, rw = lm[15], lm[16]
            entry["left_wrist_px"] = [lw.x * w, lw.y * h, lw.visibility]
            entry["right_wrist_px"] = [rw.x * w, rw.y * h, rw.visibility]

            annotated = frame.copy()
            mp.solutions.drawing_utils.draw_landmarks(
                annotated, pose_result.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS
            )
            for cx, cy, cconf in entry["ball_candidates"]:
                cv2.circle(annotated, (int(cx), int(cy)), 6, (0, 0, 255), 2)
            cv2.imwrite(os.path.join(OUT_DIR, "frames_v2", f"{clip_id}_f{frame_idx:03d}.jpg"), annotated)
        else:
            entry["left_wrist_px"] = None
            entry["right_wrist_px"] = None

        clip_results.append(entry)

    cap.release()
    pose.close()
    all_results[clip_id] = {"release": [rel_lo, rel_hi], "frames": clip_results}

with open(os.path.join(OUT_DIR, "results_v2.json"), "w") as f:
    json.dump({"skipped": SKIPPED, "clips": all_results}, f, indent=2)

# console summary
for clip_id, data in all_results.items():
    if "error" in data:
        print(f"{clip_id}: ERROR {data['error']}")
        continue
    rel_lo, rel_hi = data["release"]
    print(f"\n=== {clip_id} (reviewed release {rel_lo}-{rel_hi}) ===")
    print(f"{'frame':>5} {'pose?':>6} {'R-wrist->ball px':>18}")
    for e in data["frames"]:
        if "error" in e:
            print(f"{e['frame']:>5}  FRAME READ FAILED")
            continue
        has_pose = e["left_wrist_px"] is not None
        rd = nearest_dist(e.get("right_wrist_px"), e["ball_candidates"])
        marker = " <= reviewed release" if rel_lo <= e["frame"] <= rel_hi else ""
        print(f"{e['frame']:>5} {str(has_pose):>6} {str(round(rd,1)) if rd else '-':>18}{marker}")

print("\nSkipped:", SKIPPED)
