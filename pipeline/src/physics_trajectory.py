import numpy as np

g = 9.81

def solve_pre_bounce(release_z, kph, release_x, bounce_x, bounce_frame, fps):
    """Simple projectile (gravity only, constant horizontal speed) from release to bounce."""
    v = kph/3.6
    dist = release_x - bounce_x
    T = dist / v                      # seconds, release -> bounce
    frame_release = bounce_frame - T*fps
    vy0 = (0.5*g*T**2 - release_z) / T   # solves height(T) = 0
    def height_at_frame(f):
        t = (f - frame_release)/fps
        return release_z + vy0*t - 0.5*g*t**2
    return frame_release, T, vy0, height_at_frame

def implied_post_bounce_vy0(height_truth, t_since_bounce):
    """What vertical launch speed off the pitch would explain an observed height at time t?"""
    return (height_truth + 0.5*g*t_since_bounce**2) / t_since_bounce

print("================= C4 =================")
release_x_assumed = 16.6  # ~2.3m in front of bowling crease (18.9m) - typical fast-bowler release point
frame_release, T, vy0, hfun = solve_pre_bounce(release_z=2.161, kph=136.69,
                                                release_x=release_x_assumed, bounce_x=2.258,
                                                bounce_frame=104, fps=25)
print(f"assumed release point: {release_x_assumed}m from batter's stumps")
print(f"-> release works out to frame {frame_release:.1f} (we started tracking at frame 93)")
print(f"-> time in the air release->bounce: {T:.3f}s  ({T*25:.1f} frames)")
print("predicted height (pure physics, no pixels) at each tracked frame:")
for f in range(93,105):
    print(f"  frame{f}: predicted height = {hfun(f):.3f} m")

print()
t_bounce_to_105 = (105-104)/25
vy0_needed_for_pixel = implied_post_bounce_vy0(0.136, t_bounce_to_105)
vy0_needed_for_truth = implied_post_bounce_vy0(0.187, t_bounce_to_105)
print(f"post-bounce check at frame105 (0.04s after pitching):")
print(f"  our pixel answer 0.136m implies the ball popped up off the pitch at {vy0_needed_for_pixel:.2f} m/s")
print(f"  true answer      0.187m implies the ball popped up off the pitch at {vy0_needed_for_truth:.2f} m/s")
print("  (both are ordinary, believable numbers for a length ball - real bounces are usually 1.5-3.5 m/s upward)")

print()
print("================= C5 =================")
release_x_assumed = 16.6
frame_release5, T5, vy05, hfun5 = solve_pre_bounce(release_z=2.158, kph=138.82,
                                                    release_x=release_x_assumed, bounce_x=3.142,
                                                    bounce_frame=84, fps=25)
print(f"-> release works out to frame {frame_release5:.1f}")
print(f"-> time in the air release->bounce: {T5:.3f}s ({T5*25:.1f} frames)")

t_bounce_to_91 = (91-84)/25
vy0_needed_pixel5 = implied_post_bounce_vy0(0.358, t_bounce_to_91)
vy0_needed_truth5 = implied_post_bounce_vy0(0.292, t_bounce_to_91)
print(f"post-bounce check at frame91 ({t_bounce_to_91:.2f}s after pitching):")
print(f"  our pixel answer 0.358m implies pop-up speed {vy0_needed_pixel5:.2f} m/s")
print(f"  true answer      0.292m implies pop-up speed {vy0_needed_truth5:.2f} m/s")
