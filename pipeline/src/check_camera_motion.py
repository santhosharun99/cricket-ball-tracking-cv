"""Is the delivery-segment camera locked off, or does it pan/zoom?
Compare ORB keypoints between the first and last frame of segment 1 (the
delivery view) -- a locked camera gives a near-identity homography; a
panning/zooming one gives real translation/scale.
"""
import sys
import cv2
import numpy as np

path, seg_end = sys.argv[1], int(sys.argv[2])
cap = cv2.VideoCapture(path)
frames = []
i = 0
while i < seg_end:
    ok, fr = cap.read()
    if not ok:
        break
    frames.append(fr)
    i += 1
cap.release()

f0 = cv2.cvtColor(frames[3], cv2.COLOR_BGR2GRAY)      # skip first couple (transition blur)
f1 = cv2.cvtColor(frames[-3], cv2.COLOR_BGR2GRAY)

orb = cv2.ORB_create(2000)
k0, d0 = orb.detectAndCompute(f0, None)
k1, d1 = orb.detectAndCompute(f1, None)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
matches = sorted(bf.match(d0, d1), key=lambda m: m.distance)[:200]

pts0 = np.float32([k0[m.queryIdx].pt for m in matches])
pts1 = np.float32([k1[m.trainIdx].pt for m in matches])
H, inliers = cv2.findHomography(pts0, pts1, cv2.RANSAC, 3.0)

# decompose the translation/scale part for a quick human-readable read
scale = np.sqrt(np.linalg.det(H[:2, :2]))
dx, dy = H[0, 2], H[1, 2]
print(f'{path}')
print(f'  frames compared: 3 -> {seg_end-3}  ({seg_end-6} frames apart)')
print(f'  matches used: {len(matches)}, inliers: {int(inliers.sum())}')
print(f'  estimated scale change: {scale:.4f}  (1.0 = no zoom)')
print(f'  estimated shift: dx={dx:.1f}px dy={dy:.1f}px')
