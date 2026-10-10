"""
Motion tracker v3 for the ball in clip C5, segment 42-139.

Fixes vs v2:
  - Blob filters loosened back to what actually matched the ball visually
    (area 3-300, aspect <= 2.2, no hard fill-ratio cutoff).
  - Prediction uses a SMOOTHED velocity (average of last 2 steps), not raw
    2nd-order acceleration - acceleration from noisy 1-frame differences
    was blowing up and running the predicted position off the edge of the
    frame once a detection was missed.
  - Predicted step is capped to a sane max pixel displacement (60px) so a
    single bad step can't compound into nonsense.
  - Coasting (no detection found) is capped at 2 frames, and coasted
    positions are NOT fed back into the velocity estimate - if the ball
    still isn't found after that, tracking stops for that run rather than
    inventing positions.
  - Still: small box first (25px), only grows (40/60/90/130) if nothing
    found - never a whole-frame search.
"""
import cv2
import numpy as np
import json

FRAME_DIR = "frames/c5_seg"
SEED_FRAME = 74
SEED_XY = (881.0, 322.0)
MAX_FRAME = 139
MIN_FRAME = 42

RADII = [25, 40, 60, 90, 130]
MAX_COAST = 2
MAX_STEP = 60  # cap on predicted displacement per frame


def load_gray(fn):
    img = cv2.imread(f"{FRAME_DIR}/f{fn:04d}.jpg")
    if img is None:
        return None
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def candidates_in_box(gray_cur, gray_prev, cx, cy, radius, w, h):
    x0, y0 = max(0, int(cx - radius)), max(0, int(cy - radius))
    x1, y1 = min(w, int(cx + radius)), min(h, int(cy + radius))
    if x1 <= x0 or y1 <= y0:
        return []
    patch_cur = gray_cur[y0:y1, x0:x1]
    patch_prev = gray_prev[y0:y1, x0:x1]
    diff = cv2.absdiff(patch_cur, patch_prev)
    _, motion_mask = cv2.threshold(diff, 14, 255, cv2.THRESH_BINARY)
    _, bright_mask = cv2.threshold(patch_cur, 160, 255, cv2.THRESH_BINARY)
    mask = cv2.bitwise_and(motion_mask, bright_mask)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    out = []
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < 3 or area > 300:
            continue
        aspect = max(bw, bh) / max(1, min(bw, bh))
        if aspect > 2.2:
            continue
        cx_l, cy_l = centroids[i]
        out.append((x0 + cx_l, y0 + cy_l, area))
    return out


def pick_best(cands, pred_x, pred_y):
    if not cands:
        return None
    best, best_d = None, 1e9
    for (cx, cy, area) in cands:
        d = (cx - pred_x) ** 2 + (cy - pred_y) ** 2
        if d < best_d:
            best_d, best = d, (cx, cy, area)
    return best


def clamp_step(dx, dy, max_step=MAX_STEP):
    dist = (dx ** 2 + dy ** 2) ** 0.5
    if dist > max_step and dist > 0:
        scale = max_step / dist
        return dx * scale, dy * scale
    return dx, dy


def track(direction, frame_shape):
    h, w = frame_shape
    results = {}
    real_positions = [SEED_XY]  # only real (detected) positions feed the velocity model
    coast = 0
    fn = SEED_FRAME
    while True:
        nxt = fn + direction
        if nxt > MAX_FRAME or nxt < MIN_FRAME:
            break
        g_cur, g_prev = load_gray(nxt), load_gray(fn)
        if g_cur is None or g_prev is None:
            break

        last_x, last_y = real_positions[-1]
        if len(real_positions) >= 3:
            (x3, y3), (x2, y2), (x1, y1) = real_positions[-1], real_positions[-2], real_positions[-3]
            v_a = (x2 - x1, y2 - y1)
            v_b = (x3 - x2, y3 - y2)
            vx, vy = (v_a[0] + v_b[0]) / 2, (v_a[1] + v_b[1]) / 2
        elif len(real_positions) == 2:
            (x2, y2), (x1, y1) = real_positions[-1], real_positions[-2]
            vx, vy = x2 - x1, y2 - y1
        else:
            vx, vy = 0.0, 6.0 * direction

        vx, vy = clamp_step(vx, vy)
        pred_x = max(0, min(w - 1, last_x + vx))
        pred_y = max(0, min(h - 1, last_y + vy))

        found = None
        used_radius = None
        for r in RADII:
            cands = candidates_in_box(g_cur, g_prev, pred_x, pred_y, r, w, h)
            found = pick_best(cands, pred_x, pred_y)
            if found:
                used_radius = r
                break

        if found is None:
            coast += 1
            if coast > MAX_COAST:
                results[nxt] = {"x": None, "y": None, "area": None, "note": "lost - stopped"}
                break
            results[nxt] = {"x": round(pred_x, 1), "y": round(pred_y, 1), "area": None,
                             "note": "coasted (no detection) - not fed back into velocity"}
            fn = nxt
            continue

        coast = 0
        nx, ny, area = found
        note = f"search radius {used_radius}px"
        results[nxt] = {"x": round(nx, 1), "y": round(ny, 1), "area": int(area), "note": note}
        real_positions.append((nx, ny))
        fn = nxt

    return results


sample = load_gray(SEED_FRAME)
h, w = sample.shape

fwd = track(+1, (h, w))
bwd = track(-1, (h, w))

all_results = {SEED_FRAME: {"x": SEED_XY[0], "y": SEED_XY[1], "area": None,
                             "note": "manually verified seed"}}
all_results.update(bwd)
all_results.update(fwd)

with open("data/c5_ball_track_v3.json", "w") as f:
    json.dump({str(k): all_results[k] for k in sorted(all_results)}, f, indent=2)

print(f"total frames with a result: {len(all_results)} (range {min(all_results)}-{max(all_results)})")
for fn in sorted(all_results):
    print(fn, all_results[fn])
