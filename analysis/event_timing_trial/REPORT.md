# Automatic event timing: five existing clips

This is a deliberately simple **unseeded image-turn baseline**, not the previously manually initialised tracker. All detection ran on the local CPU. It starts candidate tracks automatically in a common frame 50–115 excerpt and looks for two downward movements followed by two upward movements. The first qualifying turn is its bounce proposal. No reference timing or manual ball seed enters prediction. Labels are read after predictions.

| clip   |   turn_candidates |   predicted_bounce_frame |   confirmation_frame |   reference_bounce_frame |   abs_error_frames |   error_ms |   track_start_proxy_not_release | release_reference   | release_status                                 |
|:-------|------------------:|-------------------------:|---------------------:|-------------------------:|-------------------:|-----------:|--------------------------------:|:--------------------|:-----------------------------------------------|
| C1     |                 3 |                       58 |                   60 |                       98 |                 40 |       1600 |                              51 | [90, 91]            | not measured: hand-ball separation unavailable |
| C2     |                 0 |                      nan |                  nan |                      nan |                nan |        nan |                             nan | nan                 | not measured: hand-ball separation unavailable |
| C3     |                 1 |                       95 |                   97 |                       95 |                  0 |          0 |                              87 | [83, 84]            | not measured: hand-ball separation unavailable |
| C4     |                 0 |                      nan |                  nan |                      104 |                nan |        nan |                             nan | [92, 93]            | not measured: hand-ball separation unavailable |
| C5     |                 2 |                       59 |                   61 |                       84 |                 25 |       1000 |                              57 | [73, 74]            | not measured: hand-ball separation unavailable |

## Result

Of four clips with reviewed bounce timing, 3 received a proposal and **1/4 were within one frame**. C2 has no reliable reviewed bounce and cannot be scored. Timing agreement alone does not prove the tracked object is the ball; inspect event_review.jpg. These are known development examples, not held-out validation. The frame window is preselected, so this is not whole-video automatic event acquisition.

Reference bounce times come from an earlier tracker event subsequently visually reviewed, with nominal half-frame uncertainty. They are not independently blinded labels. The tolerance is one frame (40 ms at 25 fps). The algorithm confirms turns after subsequent observations; confirmation_frame records that delay rather than pretending to know the bounce immediately.

## Release timing

**Not automatically measured.** A track's first detection is not evidence that the ball just left the hand. It can start early on a distractor or late after occlusion. Track-start values are saved for diagnosis only, not reported as release estimates. Reliable release timing requires identifying the bowling hand and the ball separating from it; this experiment has no such signal. Existing manually reviewed release intervals remain the only release timings.

## Reproduce

Run `python3 analysis/event_timing_trial/run.py`, then `python3 analysis/event_timing_trial/report.py` from the workspace root. Same Python/YOLO dependencies as earlier trials. protocol.json contains fixed rules; raw_detections.json and events.json preserve intermediate results; results.csv contains scoring. No source files or production tracker were changed.


## Separate seeded diagnostic (added after the unseeded baseline)

| clip   |   bounce_proposal |   confirmation_frame |   reference |   error_frames |
|:-------|------------------:|---------------------:|------------:|---------------:|
| C4     |               nan |                  nan |         104 |            nan |
| C1     |                98 |                  100 |          98 |              0 |
| C3     |                95 |                   97 |          95 |              0 |
| C5     |                84 |                   87 |          84 |              0 |
| C2     |               nan |                  nan |         nan |            nan |

With the existing five verified starting observations and unchanged guide, 3/4 scorable clips have exact bounce proposals. C4 returns none. C2 has no proposal and no reference. Confirmation delays are two frames for C1/C3 and three frames for C5. This is conditional on manual initialisation, not end-to-end automatic performance. See seeded.py and seeded_results.csv.

Visual review of unseeded proposals: C1 frame58 follows the bowler foot; C5 frame59 follows a bowler/body region. A change in vertical direction alone cannot identify a ball bounce.
