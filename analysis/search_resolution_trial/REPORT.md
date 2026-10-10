# Higher-resolution local search

**Result: enlarging the detector input did not help.** The 1280 setting matched the existing guide at 39/40; the 960 setting fell to 35/40 with three wrong-object picks. Both still missed C2 frame 85. Keep the existing guide; larger input is not justified by these results. The cause of the missed recognition remains unresolved. Further evaluation should use newly labelled footage rather than repeatedly tuning these five clips.

Exploratory follow-up on the same five development clips. Two resolutions (960 and 1280) were fixed before this run. Same 384-pixel crop, motion gate, confidence threshold, five verified starting observations and full-frame fallback as the previous experiment. Each method follows its own accepted detections, without later ground-truth corrections. Model inference is CPU-only, four threads.

| method                       |   correct |   missed_visible |   safe_abstention |   unscorable |   wrong |   wrong_known_pitch_mark |
|:-----------------------------|----------:|-----------------:|------------------:|-------------:|--------:|-------------------------:|
| bounce_reset_visual_override |        39 |                1 |                 1 |            1 |       0 |                        0 |
| detector_only                |        37 |                1 |                 0 |            1 |       2 |                        1 |
| predicted_roi                |        39 |                1 |                 1 |            1 |       0 |                        0 |
| predicted_roi_1280           |        39 |                1 |                 1 |            1 |       0 |                        0 |
| predicted_roi_960            |        35 |                2 |                 1 |            1 |       3 |                        0 |

## Cost and position error
- predicted_roi_1280: additional crop inference 0.309 seconds/frame; average accepted visible-ball error 1.47 pixels. Misses excluded from position error but included in counts.
- predicted_roi_960: additional crop inference 0.201 seconds/frame; average accepted visible-ball error 8.34 pixels. Misses excluded from position error but included in counts.

## Interpretation
Correct means within 20 pixels of the reviewed reference. Compare false picks as well as correct counts: extra detections are not necessarily real balls. This is repeated exploration of known clips, not independent validation or a general accuracy claim. Verified initial seeds and possible detector-training overlap limit conclusions. No settings have been promoted to the production tracker. This remains image-motion guidance, not calibrated 3D physics.

## Reproduce
```sh
python3 analysis/search_resolution_trial/run.py
python3 analysis/search_resolution_trial/report.py
```
Dependencies and input files match the preceding search_area_trial. cases.csv and detections.json contain every scored choice and raw crop candidate; protocol.json records fixed parameters; audit.json records CPU use and model hash.
