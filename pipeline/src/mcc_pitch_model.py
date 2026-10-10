"""
mcc_pitch_model.py
------------------
Defines the exact 3D real-world coordinates of the cricket pitch according to the Laws of Cricket (MCC).
These coordinates are used to calibrate the camera and find exact zoom/tilt.

Coordinate System:
Origin (0,0,0) is at the base of the batter's middle stump.
+X axis points straight down the pitch towards the bowler.
+Y axis points horizontally across the pitch (from off-side to leg-side for a right-hander).
+Z axis points straight up into the sky.

Units are in metres.
"""
import numpy as np

# Measurements according to MCC
PITCH_LENGTH = 20.12          # 22 yards between bowling creases (stump to stump)
POPPING_CREASE_DIST = 1.22    # 4 feet in front of the bowling crease
CREASE_HALF_WIDTH = 1.32      # Minimum popping crease width is 8ft 8in (2.64m), so half is 1.32m
STUMP_HEIGHT = 0.7112         # 28 inches
STUMP_TOTAL_WIDTH = 0.2286    # 9 inches (from off-stump outer edge to leg-stump outer edge)
STUMP_HALF_WIDTH = STUMP_TOTAL_WIDTH / 2.0

# Define exactly known 3D points
MCC_3D_POINTS = {
    # --- BATTER'S END (x = 0 to 1.22) ---
    "batter_middle_stump_base": [0.0, 0.0, 0.0],
    "batter_middle_stump_top":  [0.0, 0.0, STUMP_HEIGHT],
    "batter_off_stump_base":    [0.0, -STUMP_HALF_WIDTH, 0.0],
    "batter_leg_stump_base":    [0.0, STUMP_HALF_WIDTH, 0.0],
    "batter_off_stump_top":     [0.0, -STUMP_HALF_WIDTH, STUMP_HEIGHT],
    "batter_leg_stump_top":     [0.0, STUMP_HALF_WIDTH, STUMP_HEIGHT],
    
    "batter_popping_crease_middle": [POPPING_CREASE_DIST, 0.0, 0.0],
    "batter_popping_crease_off":    [POPPING_CREASE_DIST, -CREASE_HALF_WIDTH, 0.0],
    "batter_popping_crease_leg":    [POPPING_CREASE_DIST, CREASE_HALF_WIDTH, 0.0],

    # --- BOWLER'S END (x = 18.9 to 20.12) ---
    "bowler_middle_stump_base": [PITCH_LENGTH, 0.0, 0.0],
    "bowler_middle_stump_top":  [PITCH_LENGTH, 0.0, STUMP_HEIGHT],
    "bowler_off_stump_base":    [PITCH_LENGTH, -STUMP_HALF_WIDTH, 0.0],
    "bowler_leg_stump_base":    [PITCH_LENGTH, STUMP_HALF_WIDTH, 0.0],
    
    "bowler_popping_crease_middle": [PITCH_LENGTH - POPPING_CREASE_DIST, 0.0, 0.0],
    "bowler_popping_crease_off":    [PITCH_LENGTH - POPPING_CREASE_DIST, -CREASE_HALF_WIDTH, 0.0],
    "bowler_popping_crease_leg":    [PITCH_LENGTH - POPPING_CREASE_DIST, CREASE_HALF_WIDTH, 0.0],
}

def get_3d_points(keypoint_names):
    """
    Given a list of keypoint names, returns their exact 3D coordinates as a numpy array.
    """
    pts = []
    for name in keypoint_names:
        if name not in MCC_3D_POINTS:
            raise ValueError(f"Unknown keypoint: {name}")
        pts.append(MCC_3D_POINTS[name])
    return np.array(pts, dtype=np.float32)
