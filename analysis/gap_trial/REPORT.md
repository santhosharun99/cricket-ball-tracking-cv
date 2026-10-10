# Hidden-frame trial: did the curved-path guide help?

**It helped predict short gaps before the bounce, but did not beat the detector on these clear clips. It should not control the tracker yet.**

We tested C4 first, then C1, C3 and C5. Two or three frames were withheld from each predictor. Only the earlier ball positions and the returning frame's raw detections were passed to it. No future bounce time, later speed graphic or official metric answer was used.

## Result

| Method | Correct first return | Cases | Rate | Median miss (pixels) |
| --- | --- | --- | --- | --- |
| blend | 26 | 46 | 56.5% | 45.4 |
| curved | 27 | 46 | 58.7% | 35.4 |
| detector_only | 46 | 46 | 100.0% | not applicable |
| straight | 21 | 46 | 45.7% | 66.3 |

The detector alone selected the correct ball in all **46 scored return-frame cases**. A straight-path search found it in **21/46**; adding a fixed half-and-half curved prediction found it in **26/46**. Curved prediction alone found it in **27/46**. These are overlapping artificial gaps from only four deliveries, not 46 independent deliveries and not an official challenge score.

For **19 gaps ending before the bounce**, straight prediction recovered **10/19**, the blend **18/19**, and curved prediction **19/19**. The median miss fell from **52 pixels** for straight continuation to **16 pixels** for curved continuation. That is a useful signal for guiding a search while the ball remains in the same flight phase.

Across a bounce, the trend reversed: of **17 cases starting before the bounce and returning at/after it**, straight continuation recovered **10**, the blend **8**, curved continuation **6**. The incoming curve continues downward while the ball has already bounced upward. Histories that mix pre- and post-bounce sightings also perform poorly; the current five-point fit does not reset when a bounce happens.

The C4 result alone was straight **8/11**, blend **9/11**, curved **9/11**, detector **11/11**. The other clips exposed the failure cases. Longer, five-frame gaps were worse: straight **3/15**, blend **5/15**, curved **3/15**; detector **15/15**. Settings were not adjusted after these results.

## What this does and does not establish

- This is a **local curved-motion test in image pixels**, not a test of the earlier metre-based gravity/drag simulator. It fits constant image acceleration from five previous sightings. Perspective and camera zoom affect that curve. A calibrated camera and independent initial physical state are still needed to project a true 3D simulator causally onto the video.
- The earlier timing simulator was intentionally not reused: it requires knowing when the bounce occurs. Feeding that time into an unseen-bounce experiment would give away future information.
- This is a correctly seeded gap-recovery component test. The five prior ball detections are manually verified; the experiment does not measure automatic release acquisition or recovery from an already-wrong track. It is not a rerun of the entire existing production tracker.
- Clear, visible return frames were selected for scoring. Labels are detector-assisted human ball-identity checks, with separate bright-pixel centroids measured from original frames. This is not an independent official frame-level ground-truth dataset. The detector's 46/46 result is conditional on this small, favourable selection, not a broad recall claim.
- Three frames could not be confidently labelled: C1 F97 (partly occluded ball and a false pitch-mark detection), C1 F103 (bat interaction), C5 F86 (ball/bat overlap). Four primary gap cases and one five-frame case returning exactly to these frames were excluded; they are listed in `excluded_cases.csv`. No missing ball was filled in with a predicted reference.
- C2 was not included: the previous inspection found no reliable early-flight references. This experiment provides no evidence of solving C2.
- We observed no wrong accepted ball in the scored return frames. Motion failures here were mostly rejection of the genuine ball because the predicted search region was misplaced.

## How the comparison worked

The existing local YOLO26 ball weights ran on 57 original frames at image size 1280 and confidence 0.05, without retraining. Every raw candidate was retained. Of these frames, 54 received visible-ball references after image review.

For each eligible last-seen frame, all candidate observations in the next 2, 3 or 5 frames were withheld from the prediction function. The return frame is last-seen + hidden-count + 1. Each fit receives only the last five verified detector observations at or before last-seen. Natural missing sightings may make those five observations non-consecutive.

Four methods:

1. Detector only: take the highest-confidence raw detection on the returning frame.
2. Straight: fit a constant-velocity path to the previous five sightings.
3. Curved: fit a constant-acceleration path to those same sightings.
4. Blend: average the straight and curved predicted positions, with a fixed 50/50 weight.

The three motion methods use the same **60-pixel search radius**. Within it, candidate scores combine detector confidence with distance to the predicted position (Gaussian width 30 pixels). A chosen candidate counts as correct if its centre is within **20 pixels** of the reviewed ball reference. These illustrative settings were written into `protocol.json` before scoring; they were not tuned on the cases. They are not calibrated statistical uncertainties.

The code also records attempts over up to three visible return frames after rejection. An accepted wrong detection is terminal, not silently corrected using labels. Since the detector-only baseline was already correct immediately on all scored first returns, no faster-than-detector reacquisition has been demonstrated. End-of-clip follow-up lengths differ, so first-return success is the primary result.

Phase labels such as “before bounce” are computed for reporting only and never passed to the predictor. `predictor.py` has no access to videos, answer sheets, reference files, bounce labels or future timestamps beyond the requested prediction frame.

## Recommendation

Keep the curved path as an **experimental search hint**, with clear visual detections allowed to override it. Do not use a hard physics gate that discards a clearly seen ball. Before using it across a bounce, add a causal bounce-change detector, reset the incoming fit after an observed bounce, and retain multiple possibilities when a bounce may be hidden. Then repeat this exact saved test and add genuinely ambiguous return frames or another delivery; do not optimise the weights just to improve these four clips.

No existing tracker files or source videos were changed. The result does not yet justify deploying a physics/vision blend, but it identifies exactly where the idea helps and where it currently fails.

## Reproduce and inspect

Run from the project directory:

```sh
OMP_NUM_THREADS=4 python3 analysis/gap_trial/detect.py
python3 analysis/gap_trial/label_references.py
python3 analysis/gap_trial/evaluate.py
python3 analysis/gap_trial/make_report.py
```

`detections.json` caches the expensive detector run, so rerunning only the last two commands reproduces scoring and this report. Reference identity choices in `label_references.py` reflect the manual review recorded here, and `*_reference_review.jpg` shows the labelled ball crops. `*_candidate_review.jpg` shows detector outputs for inspection.

`cases.csv` contains every scored prediction, pixel error, candidate selection, phase and history-frame list. `overall.csv`, `per_clip.csv`, `per_phase.csv`, `per_gap.csv` and `long_gaps.csv` provide summary tables. `checks.json` records equation and input-boundary checks. `examples.png` illustrates both an improvement and a bounce failure, selected for explanation rather than used as the accuracy denominator.

Source videos: `pipeline/data/videos/`.
Source model: `pipeline/models/yolo26_ball_detector.pt`.
The detector's training set may overlap the broadcast source; independence of its training data from these examples is not established. Installed environment/model identity is recorded in `environment.json`.
