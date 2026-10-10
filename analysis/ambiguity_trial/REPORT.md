# Sequential tracking: does the motion guide help with real distractors?

**Yes, in this small trial it made two better choices in C2 and avoided a false detection in C1.** This is the first experiment here that shows an advantage over simply taking the detector's highest-scoring box. It still does not solve C2's hidden release or bounce.

| Method | Correct visible frames | Missed visible frames | Wrong choices on visible frames | Additional known false pick on occluded C1 frame |
|---|---:|---:|---:|---:|
| Highest detector score | 37/40 (92.5%) | 1 | 2 | 1 |
| Conservative detector confidence rule | 29/40 (72.5%) | 11 | 0 | 0 |
| Detector + unchanged bounce-aware motion guide | 39/40 (97.5%) | 1 | 0 | 0 |

These are **40 frame decisions across five example deliveries**, not 40 independent videos or a general accuracy estimate. Each clip starts with five manually verified detector sightings. All later decisions use the method's own history, including any mistakes. No ground-truth correction is supplied later, and no parameters were changed from the preceding prototype.

## What changed from the earlier tests

Earlier gap tests repeatedly started from a known-correct history. Here the methods continue sequentially through the original detections, including actual missing or false detections. This is harder and closer to normal tracking. The raw detector sees the same frames and candidates as the guided method.

C2 was inspected from frames 58–86. Its early candidates include shoes, hands and background objects; release and bounce remain unlabelled. The ball is clearly visible from frame 76 onward. Frames 76–80 initialise the C2 test, and frames 81–86 are scored. This is **reacquired late-flight tracking**, not automatic acquisition of the whole delivery.

The guide uses five past detections, a local straight/curved image-motion prediction, the previous causal bounce-turn reset, and the fixed visual override. It is not the earlier metre-based gravity/drag simulator. No speed graphic, future bounce time or metric answer is used. The C2 gains come from motion continuity after the ball is visible; they do not demonstrate that the reset recovered its hidden bounce.

## What happened in C2

- **Frame 82:** a background detection scored 0.064, slightly above the genuine ball at 0.059. The detector-only method selected the background. The guide selected the ball near the expected path.
- **Frame 84:** a player-region detection scored 0.059, above the ball at 0.051. The guide again selected the genuine ball.
- **Frame 85:** the detector returned no candidates. Both tracking methods recorded a missing detection. The guide's unconfirmed predicted position was **3.5 pixels** from the manually reviewed ball centre, and it found the ball again at frame 86. This single interpolation result is encouraging but is **not counted as a successful detection** and was not inserted into the state as if observed.

In C1 frame 97, the real ball is partly obscured and has no reliable point label, but the detector's pitch-mark candidate is visibly false. The guided method rejected it. This is reported separately from the 40 visible-frame denominator. C5 frame 86 remains unscorable and is excluded from accuracy for every method; no candidate was selected there.

## Why this is still an experiment

There are only five previously inspected example clips, with 5 confirmed seed points per clip and 40 later visible-frame decisions. The C2 evaluation contains six frames; one has no detector box. Reference identities were manually reviewed with detector assistance, and centres were extracted from original-image bright components. C2 frame 85 was manually located from the source image because there was no box. This is not an independent official frame-label dataset, and the source-model training data may overlap these broadcasts.

The 60-pixel search radius and 20-pixel correctness tolerance are unchanged, including on C2's lower-resolution footage. Settings are illustrative rather than scale-calibrated. The correct-prefix and chosen-delivery-window assumptions remain. Most evaluated frames are straightforward and the sample contains few true competing objects. The confidence-only baseline shows that simply rejecting weak detections reduces errors but misses more genuine balls; the motion guide recovered several of those weak detections on this sample.

Do not present 97.5% as general tracking accuracy. The supported conclusion is narrower: **the unchanged motion guide resolved two observed distractor cases, rejected one known false detection, and bridged one detector miss with a close unconfirmed prediction on these examples.**

## Outputs and reproduction

- `comparison.mp4`: slowed C2 side-by-side review. Initial five sightings are marked separately; missing-frame prediction is explicitly labelled unconfirmed.
- `comparison.jpg`: the two corrected choices and the missed-frame prediction.
- `sequential_cases.csv`, `summary.csv`, `per_clip.csv`: every decision and aggregate counts.
- `seeds.json`: initial frame numbers and evaluation ranges.
- `c2_detections.json`, `c2_references.json`, `C2_reference_review.jpg`: new C2 observations and reference audit.
- `protocol.json`: pre-scoring rules and limitations.

```sh
python3 analysis/ambiguity_trial/detect_c2.py
python3 analysis/ambiguity_trial/label_c2.py
python3 analysis/ambiguity_trial/sequential.py
python3 analysis/ambiguity_trial/report.py
```

The final two commands reuse cached detections/references. `sequential.py` imports the **unchanged** `analysis/gap_trial_v2/predictor_v2.py`; source videos and the existing tracking project remain untouched. All history-frame timestamps precede each evaluated frame. References only score the selected result and define the initial five sightings; they never decide whether a later accepted candidate is fed back into history.

Next useful step: package this as an optional guide with explicit “observed”, “predicted” and “unknown” states, and test fixed settings on new videos. Keep it experimental until those unseen tests show the gains persist. Automatic delivery/release acquisition and metric camera calibration remain separate open work.
