"""Pick out the delivery-camera segment by content, not position.

The delivery view has a distinctive signature no other broadcast angle shares:
a long, roughly-vertical strip of pitch-brown running most of the frame's
height, narrower than it is tall (the camera looks straight down the pitch).
Wide fielding shots show the pitch as a small squat patch; close-ups show no
usable pitch at all. Score every cut segment on this and take the best.
"""
import sys
import cv2
import numpy as np

def cut_segments(path, thresh=0.35):
    cap = cv2.VideoCapture(path)
    prev, diffs, i = None, [], 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        small = cv2.resize(frame, (160, 90))
        hist = cv2.calcHist([small], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        if prev is not None:
            d = cv2.compareHist(prev, hist, cv2.HISTCMP_BHATTACHARYYA)
            if d > thresh:
                diffs.append(i)
        prev = hist
        i += 1
    cap.release()
    bounds = [0] + diffs + [i]
    return [(a, b) for a, b in zip(bounds[:-1], bounds[1:]) if b - a >= 5]

def pitch_score(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # cricket pitch: dry tan/brown -- low saturation, mid-high value, warm hue
    mask = cv2.inRange(hsv, (5, 20, 90), (35, 140, 220))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if n <= 1:
        return 0.0, None
    # largest blob = candidate pitch
    idx = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, w, h, area = stats[idx]
    H, W = frame.shape[:2]
    if area < 0.01 * W * H:
        return 0.0, None
    aspect = h / max(w, 1)                     # tall & narrow = looking down the pitch
    centered = 1.0 - abs((x + w / 2) - W / 2) / (W / 2)
    frac_h = h / H                              # spans a good chunk of frame height
    score = aspect * centered * frac_h
    return float(score), (x, y, w, h)

def main():
    path = sys.argv[1]
    segs = cut_segments(path)
    cap = cv2.VideoCapture(path)
    results = []
    for (a, b) in segs:
        mid = (a + b) // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, mid)
        ok, frame = cap.read()
        if not ok:
            continue
        score, box = pitch_score(frame)
        results.append((a, b, mid, score, box))
    cap.release()
    results.sort(key=lambda r: -r[3])
    print(path)
    for a, b, mid, score, box in results:
        tag = '  <-- picked' if (a, b) == (results[0][0], results[0][1]) else ''
        print(f'  seg {a:4d}-{b:4d} (mid {mid:4d})  pitch_score={score:.3f}  box={box}{tag}')

if __name__ == '__main__':
    main()
