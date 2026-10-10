"""
camera_calibrator.py
--------------------
Uses OpenCV and classical geometric computer vision to calculate camera zoom (focal length),
and camera tilt/pan angles based on the 2D pixel coordinates of known MCC pitch dimensions.
"""
import cv2
import numpy as np
from scipy.spatial.transform import Rotation as R

class CameraCalibrator:
    def __init__(self, image_width=1920, image_height=1080):
        self.width = image_width
        self.height = image_height
        self.cx = image_width / 2.0
        self.cy = image_height / 2.0
        
        self.focal_length = None
        self.camera_matrix = None
        self.dist_coeffs = np.zeros((4,1)) # Assume zero lens distortion for broadcast cameras
        self.rvec = None
        self.tvec = None

    def calibrate(self, object_points_3d, image_points_2d):
        """
        Solves for the camera zoom (focal length) and rotation/translation (tilt, pan).
        Because we only have a single view, we run a sweep over realistic focal lengths
        and use solvePnP to find the one with the lowest reprojection error.
        
        Returns:
            focal_length: Estimated zoom
            tilt: Pitch angle in degrees
            pan: Yaw angle in degrees
            roll: Roll angle in degrees
        """
        best_error = float('inf')
        best_f = None
        best_rvec = None
        best_tvec = None
        
        # Broadcast cameras are heavily zoomed. Sweep from 1000 to 10000 pixels focal length.
        for f in range(1000, 10001, 100):
            cam_matrix = np.array([
                [f, 0, self.cx],
                [0, f, self.cy],
                [0, 0, 1]
            ], dtype=np.float32)
            
            # Use solvePnP to find the rotation and translation
            success, rvec, tvec = cv2.solvePnP(
                object_points_3d, 
                image_points_2d, 
                cam_matrix, 
                self.dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE
            )
            
            if success:
                # Calculate reprojection error
                projected_points, _ = cv2.projectPoints(object_points_3d, rvec, tvec, cam_matrix, self.dist_coeffs)
                projected_points = projected_points.reshape(-1, 2)
                error = np.mean(np.linalg.norm(image_points_2d - projected_points, axis=1))
                
                if error < best_error:
                    best_error = error
                    best_f = f
                    best_rvec = rvec
                    best_tvec = tvec
                    
        self.focal_length = best_f
        self.camera_matrix = np.array([
            [best_f, 0, self.cx],
            [0, best_f, self.cy],
            [0, 0, 1]
        ], dtype=np.float32)
        self.rvec = best_rvec
        self.tvec = best_tvec
        
        # Convert rotation vector to Euler angles (tilt, pan, roll)
        rmat, _ = cv2.Rodrigues(self.rvec)
        r = R.from_matrix(rmat)
        angles = r.as_euler('xyz', degrees=True) # x=tilt, y=pan, z=roll
        
        return {
            "focal_length_px": self.focal_length,
            "tilt_deg": angles[0],
            "pan_deg": angles[1],
            "roll_deg": angles[2],
            "reprojection_error_px": best_error
        }
        
    def get_ground_x_from_pixel(self, pixel_x, pixel_y, ground_z=0.0):
        """
        Fires a ray from the camera through the pixel to find exactly where it intersects
        the ground plane (z=0) in real-world coordinates.
        This completely solves the depth estimation problem (impact_x).
        """
        if self.camera_matrix is None:
            raise ValueError("Camera not calibrated yet.")
            
        # Ray in camera coordinates
        ray_cam = np.linalg.inv(self.camera_matrix).dot(np.array([pixel_x, pixel_y, 1.0]))
        
        # Convert to world coordinates
        rmat, _ = cv2.Rodrigues(self.rvec)
        R_inv = np.linalg.inv(rmat)
        
        camera_position_world = -R_inv.dot(self.tvec).flatten()
        ray_world = R_inv.dot(ray_cam)
        
        # Find intersection with z = ground_z
        # camera_z + t * ray_z = ground_z  =>  t = (ground_z - camera_z) / ray_z
        if abs(ray_world[2]) < 1e-6:
            return None # Ray is parallel to ground
            
        t = (ground_z - camera_position_world[2]) / ray_world[2]
        
        # Calculate intersection point
        intersection = camera_position_world + t * ray_world
        return intersection[0] # Return the X coordinate (down the pitch)
