"""
release_pose_trial v3: v2's fix backfired (see REPORT.md "v2" section) - switching to
mediapipe's sequential/video tracking mode to close the coverage gap instead made it lock
onto the UMPIRE instead of the bowler (confirmed visually: frame C1_f089.jpg's skeleton is
drawn on the pink-shirted umpire, standing still and central in frame, not the bowler at the
edge). Reverting to static_image_mode=True (v1's setting, confirmed correct on the bowler)
and only lowering min_detection_confidence, rather than changing tracking mode.

Also correcting scope: v1's real per-frame pose gap on C1 was only 5 frames (80, 81, 91, 92,
93 out of 20) - most of the "gap" that mattered was actually the cached ball-detector
having NO candidates pre-release, which is a separate, harder problem this script cannot fix
(would need re-running YOLO, deliberately deferred - see the project notes This run
only tries to close the smaller, real pose-side gap.
"""
import json
import math
import os

import cv2
import mediapipe as mp

ROOT = "/sessions/rcw-01sdoihp2zrszjau8ic1eu6t/mnt/g-p-6aad6939d0788191871c4d92556ac2d1"
VIDEO_DIR = "/sessions/rcw-01sdoihp2zrszjau8ic1eu6t/mnt/Downloads/cricket_project/data/videos"
OUT_DIR = os.path.join(ROOT, "analysis", "release_pose_trial")
os.makedirs(os.path.join(OUT_DIR, "frames_v3"), exist_ok=True)

CLIPS = {
    "C1": {"file": "f81d092b6117be1126e0d6be97220b3f9a2870eb.mp4", "release": (90, 91)},
    "C3": {"file": "98e537a2a3555da28ca7eea3227babb61df228d1.mp4", "release": (83, 84)},
    "C4": {"file": "6a79fbe0fd6792126c69087568f7f08318dcf449.mp4", "release": (92, 93)},
    "C5": {"file": "bad1530d039b7146a8ce4a1b1a6b29502c3c9491.mp4", "release": (73, 74)},
}
SKIPPED = {"C2": "no reviewed release reference exists"}

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

    # static_image_mode=True: each frame independent, correctly found the bowler in v1.
    # Only change from v1: lower min_detection_confidence (0.5 -> 0.2) to try to recover
    # the handful of frames v1 missed, without changing tracking mode.
    pose = mp.solutions.pose.Pose(
        static_image_mode=True,
        model_complexity=1,
        min_detection_confidence=0.2,
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
            # sanity flag: is this landmark set plausibly the bowler (near the popping
            # crease / run-up side, roughly x < 0.65*w in these wide shots) rather than the
            # umpire (who sits near the centre of the pitch, roughly 0.45w-0.55w) or a
            # fielder? Not a real fix, just a visible flag for honest review.
            nose_x = lm[0].x * w
            entry["nose_x_frac"] = round(nose_x / w, 3)
            entry["left_wrist_px"] = [lw.x * w, lw.y * h, lw.visibility]
            entry["right_wrist_px"] = [rw.x * w, rw.y * h, rw.visibility]

            annotated = frame.copy()
            mp.solutions.drawing_utils.draw_landmarks(
                annotated, pose_result.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS
            )
            for cx, cy, cconf in entry["ball_candidates"]:
                cv2.circle(annotated, (int(cx), int(cy)), 6, (0, 0, 255), 2)
            cv2.imwrite(os.path.join(OUT_DIR, "frames_v3", f"{clip_id}_f{frame_idx:03d}.jpg"), annotated)
        else:
            entry["left_wrist_px"] = None
            entry["right_wrist_px"] = None
            entry["nose_x_frac"] = None

        clip_results.append(entry)

    cap.release()
    pose.close()
    all_results[clip_id] = {"release": [rel_lo, rel_hi], "frames": clip_results}

with open(os.path.join(OUT_DIR, "results_v3.json"), "w") as f:
    json.dump({"skipped": SKIPPED, "clips": all_results}, f, indent=2)

for clip_id, data in all_results.items():
    if "error" in data:
        print(f"{clip_id}: ERROR {data['error']}")
        continue
    rel_lo, rel_hi = data["release"]
    print(f"\n=== {clip_id} (reviewed release {rel_lo}-{rel_hi}) ===")
    print(f"{'frame':>5} {'pose?':>6} {'nose_x_frac':>12} {'R-wrist->ball px':>18}")
    for e in data["frames"]:
        if "error" in e:
            print(f"{e['frame']:>5}  FRAME READ FAILED")
            continue
        has_pose = e["left_wrist_px"] is not None
        rd = nearest_dist(e.get("right_wrist_px"), e["ball_candidates"])
        marker = " <= reviewed release" if rel_lo <= e["frame"] <= rel_hi else ""
        nx = e.get("nose_x_frac")
        print(f"{e['frame']:>5} {str(has_pose):>6} {str(nx) if nx is not None else '-':>12} {str(round(rd,1)) if rd else '-':>18}{marker}")
