"""
Track the ball frame-by-frame in clip C5 (bad1530d...), segment 42-139,
starting from the confirmed seed position at frame 74: (881, 322).

Approach: small local search window around a position predicted from the
last known velocity (simple constant-velocity prediction), look for a
small bright round blob in that window (motion diff + brightness threshold
combined), pick the best match, update velocity. Track forward and
backward from the seed frame.
"""
import cv2
import numpy as np
import json

FRAME_DIR = "frames/c5_seg"
SEED_FRAME = 74
SEED_XY = (881, 322)

def load(fn):
    return cv2.imread(f"{FRAME_DIR}/f{fn:04d}.jpg")

def find_ball_near(gray_cur, gray_prev, cx, cy, win=45, min_area=3, max_area=250):
    x0, y0 = max(0, cx - win), max(0, cy - win)
    x1, y1 = min(gray_cur.shape[1], cx + win), min(gray_cur.shape[0], cy + win)
    patch_cur = gray_cur[y0:y1, x0:x1]
    patch_prev = gray_prev[y0:y1, x0:x1]
    diff = cv2.absdiff(patch_cur, patch_prev)
    _, motion_mask = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)
    _, bright_mask = cv2.threshold(patch_cur, 170, 255, cv2.THRESH_BINARY)
    mask = cv2.bitwise_and(motion_mask, bright_mask)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    best = None
    best_score = -1
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if not (min_area <= area <= max_area):
            continue
        aspect = max(w, h) / max(1, min(w, h))
        if aspect > 2.2:  # ball should be roughly round, reject thin stump-like blobs
            continue
        fill = area / (w * h)
        cx_l, cy_l = centroids[i]
        score = fill
        if score > best_score:
            best_score = score
            best = (x0 + cx_l, y0 + cy_l, area, w, h)
    return best

results = {}
frames = list(range(42, 140))

# ---- track forward from seed ----
cx, cy = SEED_XY
vx, vy = 0.0, 6.0  # rough initial guess: ball moving down-frame toward batsman
gray_cache = {}
def gray(fn):
    if fn not in gray_cache:
        img = load(fn)
        gray_cache[fn] = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img is not None else None
    return gray_cache[fn]

results[SEED_FRAME] = {"x": cx, "y": cy, "area": None, "note": "manually verified seed"}

last_xy = (cx, cy)
for fn in range(SEED_FRAME + 1, 140):
    g_cur, g_prev = gray(fn), gray(fn - 1)
    if g_cur is None or g_prev is None:
        break
    pred_x = last_xy[0] + vx
    pred_y = last_xy[1] + vy
    found = find_ball_near(g_cur, g_prev, int(pred_x), int(pred_y), win=40)
    if found is None:
        found = find_ball_near(g_cur, g_prev, int(pred_x), int(pred_y), win=70)
    if found is None:
        results[fn] = {"x": None, "y": None, "area": None, "note": "not found"}
        continue
    nx, ny, area, w, h = found
    vx, vy = nx - last_xy[0], ny - last_xy[1]
    last_xy = (nx, ny)
    results[fn] = {"x": round(nx, 1), "y": round(ny, 1), "area": int(area), "note": ""}

# ---- track backward from seed ----
cx, cy = SEED_XY
vx, vy = 0.0, -6.0
last_xy = (cx, cy)
for fn in range(SEED_FRAME - 1, 41, -1):
    g_cur, g_prev = gray(fn), gray(fn + 1)
    if g_cur is None or g_prev is None:
        break
    pred_x = last_xy[0] + vx
    pred_y = last_xy[1] + vy
    found = find_ball_near(g_cur, g_prev, int(pred_x), int(pred_y), win=40)
    if found is None:
        found = find_ball_near(g_cur, g_prev, int(pred_x), int(pred_y), win=70)
    if found is None:
        results[fn] = {"x": None, "y": None, "area": None, "note": "not found"}
        continue
    nx, ny, area, w, h = found
    vx, vy = nx - last_xy[0], ny - last_xy[1]
    last_xy = (nx, ny)
    results[fn] = {"x": round(nx, 1), "y": round(ny, 1), "area": int(area), "note": ""}

with open("data/c5_ball_track_raw.json", "w") as f:
    json.dump({k: results[k] for k in sorted(results)}, f, indent=2)

found_count = sum(1 for v in results.values() if v["x"] is not None)
print(f"tracked {found_count}/{len(results)} frames")
for fn in sorted(results):
    print(fn, results[fn])
