# Predicted search-area experiment

**Result: no additional detection improvement in this trial.** Predicted-area search and last-position search both matched the previous guide at 39/40 visible frames. Both crops contained the ball in all 40 labelled frames. C2 frame 85 remained undetected despite being inside the crop. This suggests the remaining failure concerns recognising the ball, rather than locating the search area. The extra search is an experimental option, not yet justified as the default.

| method                       |   correct |   missed_visible |   safe_abstention |   unscorable |   wrong |   wrong_known_pitch_mark |
|:-----------------------------|----------:|-----------------:|------------------:|-------------:|--------:|-------------------------:|
| bounce_reset_visual_override |        39 |                1 |                 1 |            1 |       0 |                        0 |
| detector_only                |        37 |                1 |                 0 |            1 |       2 |                        1 |
| last_position_roi            |        39 |                1 |                 1 |            1 |       0 |                        0 |
| predicted_roi                |        39 |                1 |                 1 |            1 |       0 |                        0 |

## What was tested
The same local YOLO26 ball model ran on CPU, using 4 threads. Each method began with the same five verified observations. Later history contained only its own accepted detections. A 384-pixel square around the predicted position was resized for detection at 640 pixels. Candidates were checked against the causal motion prediction. When none passed, the previous full-frame candidate selector was used. The allowed distance grows after missed detections.

A second method cropped around the last sighting instead of the prediction. This controls for the benefit of enlarging the ball. Full-frame results were reused from the previous run; crop timing therefore measures additional cost, not end-to-end speed.

## Metrics and limitations
Correct means within 20 pixels of a reviewed visible-ball reference. There are 40 visible labelled frames, one known false pitch-mark frame and one unscorable frame. All are correlated development examples. This is not held-out or fully automatic accuracy: starting points were manually verified and model training overlap remains unknown. No thresholds were tuned after scoring.

This uses local image motion, not calibrated gravity/drag in world coordinates. No future bounce, speed graphic or true bounce location enters selection. A 2D overlay is valid; metre distances and 3D/post-bounce angles cannot be validated from this experiment. Existing metric simulator results remain separate.

## Additional measurements
- last_position_roi: crop includes labelled ball in 40/40 frames; mean accepted position error 1.90px; additional mean crop inference 0.096s/frame. Position error excludes missed detections; use counts above alongside it.
- predicted_roi: crop includes labelled ball in 40/40 frames; mean accepted position error 1.92px; additional mean crop inference 0.123s/frame. Position error excludes missed detections; use counts above alongside it.

## Reproduce
Run from project root:
```sh
python3 analysis/search_area_trial/run.py
python3 analysis/search_area_trial/render.py
```
Dependencies: Python, torch, ultralytics, numpy, pandas, opencv-python, tabulate, and ffmpeg. Input paths are at the top of run.py. Outputs include per-frame choices, all crop candidates, fixed protocol, model hash and a comparison video. All model inference explicitly uses device=cpu.
