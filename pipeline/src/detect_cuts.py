"""Find camera cuts in a broadcast clip via frame-to-frame histogram change.
Real broadcast footage cuts between the bowler-end camera, wide replay angles,
crowd shots etc within one 20-30s clip -- we need to know which segment is
actually the delivery view before any ball detector can run on it.
"""
import sys
import cv2
import numpy as np

path = sys.argv[1]
cap = cv2.VideoCapture(path)
fps = cap.get(cv2.CAP_PROP_FPS)
prev = None
diffs = []
i = 0
while True:
    ok, frame = cap.read()
    if not ok:
        break
    small = cv2.resize(frame, (160, 90))
    hist = cv2.calcHist([small], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    hist = cv2.normalize(hist, hist).flatten()
    if prev is not None:
        d = cv2.compareHist(prev, hist, cv2.HISTCMP_BHATTACHARYYA)
        diffs.append((i, d))
    prev = hist
    i += 1
cap.release()

diffs = np.array(diffs)
thresh = 0.35
cuts = [0] + [int(f) for f, d in diffs if d > thresh] + [i]
print(f'{path}: {i} frames @ {fps:.0f}fps, {len(cuts)-2} cuts detected')
segs = list(zip(cuts[:-1], cuts[1:]))
for a, b in segs:
    print(f'  segment frames {a:4d}-{b:4d}  ({(b-a)/fps:5.1f}s)')
