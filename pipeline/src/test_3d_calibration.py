import numpy as np
from mcc_pitch_model import get_3d_points
from camera_calibrator import CameraCalibrator
from detect_pitch_keypoints import extract_keypoints

def test_calibration():
    print("--- 3D Camera Calibration Test ---")
    
    # 1. Run the ML model (placeholder) to get 2D pixel coordinates
    detected_pixels = extract_keypoints("dummy_frame.jpg")
    
    # 2. Extract the lists of matching points
    keypoint_names = list(detected_pixels.keys())
    
    # Get 3D points from MCC Pitch Model
    points_3d = get_3d_points(keypoint_names)
    
    # Get 2D points from the ML detector
    points_2d = np.array([detected_pixels[k] for k in keypoint_names], dtype=np.float32)
    
    print(f"\nExtracted {len(points_3d)} matched reference points.")
    
    # 3. Initialize Calibrator
    # Using 1920x1080 as standard broadcast size
    calibrator = CameraCalibrator(image_width=1920, image_height=1080)
    
    # 4. Calibrate!
    print("\nRunning solvePnP grid search to find exact tilt, pan, and zoom...")
    results = calibrator.calibrate(points_3d, points_2d)
    
    print("\n[ Calibration Results ]")
    print(f"Calculated Focal Length (Zoom): {results['focal_length_px']} pixels")
    print(f"Calculated Camera Tilt:         {results['tilt_deg']:.2f} degrees")
    print(f"Calculated Camera Pan:          {results['pan_deg']:.2f} degrees")
    print(f"Calculated Camera Roll:         {results['roll_deg']:.2f} degrees")
    print(f"Reprojection Error:             {results['reprojection_error_px']:.2f} pixels")
    
    print("\n[ Depth Tracking Test (impact_x) ]")
    # Simulate a ball pixel at impact: e.g. x=960, y=850 (further down the pitch)
    # And we know the ball hit the ground (z=0.0) or bat (z=0.187)
    test_px_x = 960.0
    test_px_y = 750.0
    test_z = 0.0 # On the ground
    
    predicted_impact_x = calibrator.get_ground_x_from_pixel(test_px_x, test_px_y, ground_z=test_z)
    
    print(f"A ball tracked at pixel ({test_px_x}, {test_px_y}) on the ground...")
    print(f"...is EXACTLY {predicted_impact_x:.3f} metres down the pitch!")

if __name__ == "__main__":
    test_calibration()
