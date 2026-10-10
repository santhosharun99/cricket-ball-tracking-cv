"""
v4: trajectory-fit tracker.

Instead of predicting the next position from the last frame's velocity
(which has no idea a bounce is coming), fit a smooth curve (quadratic in x
and y vs frame number) through the last several CONFIRMED real points and
use that curve to predict ahead. A quadratic can represent the natural
easing/acceleration of the ball's pixel path (including approaching a
bounce), and we refit it every time a new point is confirmed, so it
"learns" the current leg of the trajectory (pre-bounce arc, then the
new post-bounce arc) instead of extrapolating blindly through the reversal.

Ball candidates must look like a ball: near-square bounding box (round),
not just bright.
"""
import cv2
import numpy as np
import json

FRAME_DIR = "frames/c5_seg"

# All manually verified anchors so far (eye-checked against the frame)
VERIFIED = {
    74: (881.0, 322.0), 75: (887.1, 333.8), 76: (893.3, 351.1), 77: (898.7, 372.7),
    78: (903.9, 397.3), 79: (909.4, 423.7), 80: (914.9, 452.4), 81: (920.7, 481.7),
    82: (926.6, 512.5), 83: (933.4, 546.0), 84: (939.7, 580.5), 85: (945.4, 543.2),
    87: (957.5, 475.5),
}
MIN_FRAME, MAX_FRAME = 42, 139


def load_gray(fn):
    img = cv2.imread(f"{FRAME_DIR}/f{fn:04d}.jpg")
    return None if img is None else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def round_blob_candidates(gray_cur, gray_prev, cx, cy, radius, w, h):
    x0, y0 = max(0, int(cx - radius)), max(0, int(cy - radius))
    x1, y1 = min(w, int(cx + radius)), min(h, int(cy + radius))
    if x1 <= x0 or y1 <= y0:
        return []
    patch_cur = gray_cur[y0:y1, x0:x1]
    patch_prev = gray_prev[y0:y1, x0:x1]
    diff = cv2.absdiff(patch_cur, patch_prev)
    _, motion_mask = cv2.threshold(diff, 12, 255, cv2.THRESH_BINARY)
    _, bright_mask = cv2.threshold(patch_cur, 175, 255, cv2.THRESH_BINARY)
    mask = cv2.bitwise_or(cv2.bitwise_and(motion_mask, bright_mask), bright_mask if radius <= 30 else np.zeros_like(bright_mask))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    out = []
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < 60 or area > 350:
            continue
        aspect = max(bw, bh) / max(1, min(bw, bh))
        if aspect > 1.6 or bw < 8 or bw > 22 or bh < 8 or bh > 22:
            continue
        cx_l, cy_l = centroids[i]
        out.append((x0 + cx_l, y0 + cy_l, area))
    return out


def fit_curve(points):
    """points: list of (frame, x, y). Returns (px, py) numpy poly1d, degree min(2, n-1)."""
    frames = np.array([p[0] for p in points])
    xs = np.array([p[1] for p in points])
    ys = np.array([p[2] for p in points])
    deg = 2 if len(points) >= 3 else 1
    px = np.poly1d(np.polyfit(frames, xs, deg))
    py = np.poly1d(np.polyfit(frames, ys, deg))
    return px, py


sample = load_gray(87)
h, w = sample.shape

results = {fn: {"x": round(x, 1), "y": round(y, 1), "note": "verified"} for fn, (x, y) in VERIFIED.items()}

# Forward-extend past frame 87 using a curve fit to the last 3-4 confirmed post-bounce points
confirmed = sorted(VERIFIED.items())
RADII = [20, 35, 55, 80]

fn = 87
coast = 0
while True:
    nxt = fn + 1
    if nxt > MAX_FRAME:
        break
    recent = [p for p in confirmed if p[0] > 84][-4:]  # only post-bounce leg
    if len(recent) < 2:
        break
    pts = [(f, x, y) for f, (x, y) in recent]
    px, py = fit_curve(pts)
    pred_x, pred_y = float(px(nxt)), float(py(nxt))

    g_cur, g_prev = load_gray(nxt), load_gray(nxt - 1)
    if g_cur is None or g_prev is None:
        break
    found = None
    used_r = None
    for r in RADII:
        cands = round_blob_candidates(g_cur, g_prev, pred_x, pred_y, r, w, h)
        if cands:
            found = min(cands, key=lambda c: (c[0] - pred_x) ** 2 + (c[1] - pred_y) ** 2)
            used_r = r
            break

    if found is None:
        coast += 1
        results[nxt] = {"x": round(pred_x, 1), "y": round(pred_y, 1),
                         "note": f"predicted from curve fit, no matching blob found (coast {coast})"}
        if coast >= 2:
            results[nxt]["note"] += " - stopping"
            fn = nxt
            break
        fn = nxt
        continue

    coast = 0
    nx, ny, area = found
    results[nxt] = {"x": round(nx, 1), "y": round(ny, 1),
                     "note": f"curve-predicted+matched round blob, r<={used_r}px, area={int(area)}"}
    confirmed.append((nxt, (nx, ny)))
    fn = nxt

with open("data/c5_ball_track_v4.json", "w") as f:
    json.dump({str(k): results[k] for k in sorted(results)}, f, indent=2)

for k in sorted(results):
    print(k, results[k])
