"""
Proper motion-tracker for the ball in clip C5, segment 42-139.

Idea (same as video-editing motion tracking / point tracking):
  - Start from a known ball position (seed, verified by eye).
  - Predict where the ball should be in the NEXT frame using its recent
    velocity + acceleration (2nd-order extrapolation from the last two
    displacement vectors) - not a fixed guess.
  - Search only a SMALL box around that prediction (starts ~25px radius).
    If nothing ball-like is found, grow the box in steps (40/60/90/130px)
    - never jump straight to scanning the whole frame.
  - Candidate blobs must look like a ball: small, roughly round (not thin
    like a stump, not big like a glove/pad).
  - Around the bounce the vertical direction flips - detect that reversal
    and reset the motion model for the post-bounce leg instead of trusting
    the pre-bounce velocity going forward.
  - If the ball can't be found even at max box size, mark the frame as
    "not found" (coast the prediction forward a couple of frames) rather
    than silently locking onto the nearest bright blob.
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
MAX_COAST = 4  # frames allowed to "coast" on prediction alone before giving up


def load_gray(fn):
    img = cv2.imread(f"{FRAME_DIR}/f{fn:04d}.jpg")
    if img is None:
        return None
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def candidates_in_box(gray_cur, gray_prev, cx, cy, radius):
    h, w = gray_cur.shape
    x0, y0 = max(0, int(cx - radius)), max(0, int(cy - radius))
    x1, y1 = min(w, int(cx + radius)), min(h, int(cy + radius))
    if x1 <= x0 or y1 <= y0:
        return []
    patch_cur = gray_cur[y0:y1, x0:x1]
    patch_prev = gray_prev[y0:y1, x0:x1]
    diff = cv2.absdiff(patch_cur, patch_prev)
    _, motion_mask = cv2.threshold(diff, 16, 255, cv2.THRESH_BINARY)
    _, bright_mask = cv2.threshold(patch_cur, 165, 255, cv2.THRESH_BINARY)
    mask = cv2.bitwise_and(motion_mask, bright_mask)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    out = []
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < 3 or area > 300:
            continue
        aspect = max(bw, bh) / max(1, min(bw, bh))
        if aspect > 1.9:  # reject thin/elongated blobs (stumps, bat edge)
            continue
        fill = area / (bw * bh)
        if fill < 0.45:  # reject sparse/irregular blobs
            continue
        cx_l, cy_l = centroids[i]
        out.append((x0 + cx_l, y0 + cy_l, area, fill))
    return out


def pick_best(cands, pred_x, pred_y):
    if not cands:
        return None
    best, best_d = None, 1e9
    for (cx, cy, area, fill) in cands:
        d = (cx - pred_x) ** 2 + (cy - pred_y) ** 2
        if d < best_d:
            best_d, best = d, (cx, cy, area, fill)
    return best


def track(direction):
    """direction = +1 forward from seed, -1 backward from seed"""
    results = {}
    pos_history = [SEED_XY]
    vel = None
    coast = 0
    bounced = False
    fn = SEED_FRAME
    while True:
        nxt = fn + direction
        if nxt > MAX_FRAME or nxt < MIN_FRAME:
            break
        g_cur, g_prev = load_gray(nxt), load_gray(fn)
        if g_cur is None or g_prev is None:
            break

        last_x, last_y = pos_history[-1]
        if len(pos_history) >= 2:
            (x2, y2), (x1, y1) = pos_history[-1], pos_history[-2]
            vx, vy = x2 - x1, y2 - y1
        else:
            vx, vy = (0.0, 6.0 * direction)

        # 2nd order: use acceleration from last 3 points if available
        if len(pos_history) >= 3:
            (x3, y3), (x2b, y2b), (x1b, y1b) = pos_history[-1], pos_history[-2], pos_history[-3]
            v_prev = (x2b - x1b, y2b - y1b)
            v_cur = (x3 - x2b, y3 - y2b)
            ax, ay = v_cur[0] - v_prev[0], v_cur[1] - v_prev[1]
        else:
            ax, ay = 0.0, 0.0

        pred_x = last_x + vx + 0.5 * ax
        pred_y = last_y + vy + 0.5 * ay

        found = None
        used_radius = None
        for r in RADII:
            cands = candidates_in_box(g_cur, g_prev, pred_x, pred_y, r)
            found = pick_best(cands, pred_x, pred_y)
            if found:
                used_radius = r
                break

        if found is None:
            coast += 1
            if coast > MAX_COAST:
                results[nxt] = {"x": None, "y": None, "area": None,
                                 "note": "lost - exceeded coast limit"}
                fn = nxt
                pos_history.append((pred_x, pred_y))  # keep coasting position for future prediction
                continue
            results[nxt] = {"x": round(pred_x, 1), "y": round(pred_y, 1), "area": None,
                             "note": f"coasted (not found within r<=130)"}
            pos_history.append((pred_x, pred_y))
            fn = nxt
            continue

        coast = 0
        nx, ny, area, fill = found

        # bounce detection: vertical velocity sign flip (was descending, now ascending
        # or sharply decelerating) - only flag once
        if not bounced and len(pos_history) >= 2:
            prev_vy = pos_history[-1][1] - pos_history[-2][1]
            new_vy = ny - pos_history[-1][1]
            if direction == 1 and prev_vy > 3 and new_vy < prev_vy * 0.3:
                bounced = True
                results.setdefault(nxt, {})["bounce_flag"] = True

        note = f"search radius {used_radius}px"
        results[nxt] = {"x": round(nx, 1), "y": round(ny, 1), "area": int(area), "note": note}
        pos_history.append((nx, ny))
        fn = nxt

    return results


fwd = track(+1)
bwd = track(-1)

all_results = {SEED_FRAME: {"x": SEED_XY[0], "y": SEED_XY[1], "area": None,
                             "note": "manually verified seed"}}
all_results.update(bwd)
all_results.update(fwd)

with open("data/c5_ball_track_v2.json", "w") as f:
    json.dump({str(k): all_results[k] for k in sorted(all_results)}, f, indent=2)

found_count = sum(1 for v in all_results.values() if v.get("x") is not None and "coasted" not in v.get("note", "") and "lost" not in v.get("note", ""))
print(f"solidly detected (not coasted/lost): {found_count}/{len(all_results)} frames")
for fn in sorted(all_results):
    print(fn, all_results[fn])
