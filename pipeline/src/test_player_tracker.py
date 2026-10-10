import numpy as np
from mcc_pitch_model import get_3d_points
from camera_calibrator import CameraCalibrator
from detect_pitch_keypoints import extract_keypoints
from player_tracker import PlayerTracker

def test_player_tracking():
    print("--- Setting up 3D Pitch Calibration ---")
    
    # 1. Calibrate camera (re-using the logic from the previous test)
    detected_pixels = extract_keypoints("dummy_frame.jpg")
    keypoint_names = list(detected_pixels.keys())
    points_3d = get_3d_points(keypoint_names)
    points_2d = np.array([detected_pixels[k] for k in keypoint_names], dtype=np.float32)
    
    calibrator = CameraCalibrator(image_width=1920, image_height=1080)
    calibrator.calibrate(points_3d, points_2d)
    
    print("Camera Calibrated Successfully.")
    
    # 2. Run Player Tracker
    print("\n--- Initializing YOLO-Pose Player Tracker ---")
    tracker = PlayerTracker(calibrator)
    tracker.process_frame("dummy_frame_with_players.jpg")

if __name__ == "__main__":
    test_player_tracking()
