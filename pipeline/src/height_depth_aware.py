import numpy as np
import json

def depth_aware_height(base_y_at_frame, scale_at_frame, bounce_ball_y_raw,
                        base_y_at_bounce_frame, scale_at_bounce_frame,
                        bounce_x, X_t, ball_y_t, frame_scale_t):
    """
    base_y_at_frame / scale_at_frame: stump-base pixel-y and scale, evaluated AT frame t (zoom-corrected)
    bounce_ball_y_raw: the ball's raw measured pixel-y at the bounce frame
    base_y_at_bounce_frame / scale_at_bounce_frame: stump-base pixel-y & scale evaluated at the BOUNCE frame's own zoom
    bounce_x: real distance (m) of the bounce point in front of the stumps
    X_t: estimated real depth (m) of the ball at frame t, between 0 (stumps) and bounce_x
    ball_y_t: ball's measured pixel-y at frame t
    frame_scale_t: same as scale_at_frame (kept separate name for clarity)
    """
    # express "ground level at the bounce's depth" in frame t's own zoom/coords
    ground_y_bounce_depth_at_t = base_y_at_frame + (bounce_ball_y_raw - base_y_at_bounce_frame) * (scale_at_frame/scale_at_bounce_frame)
    # interpolate ground level linearly between X=0 (stumps) and X=bounce_x, at frame t's zoom
    ground_y_Xt = base_y_at_frame + (ground_y_bounce_depth_at_t - base_y_at_frame) * (X_t/bounce_x)
    real_z = (ground_y_Xt - ball_y_t) / frame_scale_t
    return real_z, ground_y_Xt

print("=== C4: depth-aware height at frame105 ===")
# fitted models (linear, from real stump measurements frames 93-103)
height_fit_c4 = np.poly1d(np.polyfit([93,94,95,96,97,98,99,100,101,102,103],
                                      [107,112,118,142,115,137,150,148,148,165,160], 1))
base_fit_c4   = np.poly1d(np.polyfit([93,94,95,96,97,98,99,100,101,102,103],
                                      [462,470,478,500,517,535,565,600,618,648,657], 1))
def scale_c4(f): return height_fit_c4(f)/0.7112

bounce_frame_c4, bounce_x_c4 = 104, 2.258
by_bounce = base_fit_c4(bounce_frame_c4); sc_bounce = scale_c4(bounce_frame_c4)
bounce_ball_y_raw_c4 = 730

f = 105
by_t = base_fit_c4(f); sc_t = scale_c4(f)
ball_y_t = 693
# assume ball reaches X=0 (bat/stumps depth) ~1 frame after 105 (frame106, where it's occluded by bat)
assumed_contact_frame = 106
X_t = bounce_x_c4 * (assumed_contact_frame - f)/(assumed_contact_frame - bounce_frame_c4)
z, gy = depth_aware_height(by_t, sc_t, bounce_ball_y_raw_c4, by_bounce, sc_bounce, bounce_x_c4, X_t, ball_y_t, sc_t)
print(f"frame{f}: assumed depth X={X_t:.3f}m, ground_y={gy:.1f}, real_z={z:.3f}  (ground truth impact_z=0.187)")

print()
print("=== C5: depth-aware height at frame91 ===")
h0,f0c5,rate_c5 = 95,42,0.9444444444444444
base0_c5 = 366
def height_c5(f): return h0+rate_c5*(f-f0c5)
def base_c5(f): return base0_c5+rate_c5*(f-f0c5)
def scale_c5(f): return height_c5(f)/0.7112

bounce_frame_c5, bounce_x_c5 = 84, 3.142
by_bounce5 = base_c5(bounce_frame_c5); sc_bounce5 = scale_c5(bounce_frame_c5)
bounce_ball_y_raw_c5 = 580.5

f = 91
by_t5 = base_c5(f); sc_t5 = scale_c5(f)
ball_y_t5 = 382
assumed_contact_frame5 = 93
X_t5 = bounce_x_c5 * (assumed_contact_frame5 - f)/(assumed_contact_frame5 - bounce_frame_c5)
z5, gy5 = depth_aware_height(by_t5, sc_t5, bounce_ball_y_raw_c5, by_bounce5, sc_bounce5, bounce_x_c5, X_t5, ball_y_t5, sc_t5)
print(f"frame{f}: assumed depth X={X_t5:.3f}m, ground_y={gy5:.1f}, real_z={z5:.3f}  (ground truth stump_z=0.292)")

print()
print("=== Pitch length classification (official bounce_x) ===")
ex = json.load(open('data/examples.json'))
names = ['C1','C2','C3','C4','C5']
def classify(bx):
    if bx <= 2.0: return "Yorker / very full"
    elif bx <= 4.0: return "Full length"
    elif bx <= 8.0: return "Good length"
    else: return "Short of a length"
for name, e in zip(names, ex):
    p = e['prediction']
    print(name, 'bounce_x=', p['bounce_x'], '->', classify(p['bounce_x']))
