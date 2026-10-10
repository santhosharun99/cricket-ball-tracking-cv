"""Cricket ball candidate detector, adapted from the tennis motion detector.

Differences from the tennis version:
- ball is white/off-white here (limited-overs match), not yellow -- so we also
  score candidates by brightness relative to the pitch/outfield, not just motion.
- ball crosses the whole visible pitch in well under half a second at 25fps, so
  expect heavy motion blur (streaks, not clean circles) -- elongation tolerance
  raised accordingly.
"""
import sys
import glob
import cv2
import numpy as np

MIN_AREA, MAX_AREA = 4, 900
MAX_ELONGATION = 12.0
DIFF_THRESH = 10

def candidates(prev2, prev1, cur):
    d1 = cv2.absdiff(cur, prev1)
    d2 = cv2.absdiff(cur, prev2)
    motion = cv2.bitwise_and(
        cv2.threshold(d1, DIFF_THRESH, 255, cv2.THRESH_BINARY)[1],
        cv2.threshold(d2, DIFF_THRESH, 255, cv2.THRESH_BINARY)[1],
    )
    motion = cv2.morphologyEx(motion, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, labels, stats, cent = cv2.connectedComponentsWithStats(motion, connectivity=8)
    out = []
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if not (MIN_AREA <= area <= MAX_AREA):
            continue
        w, h = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
        elong = max(w, h) / max(1, min(w, h))
        if elong > MAX_ELONGATION:
            continue
        cx, cy = cent[i]
        fill = area / max(1, w * h)
        brightness = float(cur[int(cy), int(cx)]) / 255.0
        score = fill * (0.3 + 0.7 * brightness)     # weight brightness harder (white ball)
        out.append((float(cx), float(cy), float(score), w, h))
    return out

def main():
    files = sorted(glob.glob(sys.argv[1] + '/*.jpg'))
    greys = [cv2.GaussianBlur(cv2.cvtColor(cv2.imread(f), cv2.COLOR_BGR2GRAY), (3, 3), 0) for f in files]
    print(f'{len(files)} frames')
    for i in range(2, len(greys)):
        cands = candidates(greys[i - 2], greys[i - 1], greys[i])
        cands.sort(key=lambda c: -c[2])
        top = cands[:3]
        print(f'frame {i:3d} ({files[i].split("/")[-1]}): {len(cands):3d} candidates  '
              f'top: ' + ', '.join(f'({c[0]:.0f},{c[1]:.0f}) s={c[2]:.2f}' for c in top))

if __name__ == '__main__':
    main()
