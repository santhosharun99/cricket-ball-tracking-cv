# Cricket Ball Tracking from Broadcast Video

Computer vision pipeline that finds and follows a cricket ball in TV broadcast footage, detects the release and bounce, and estimates delivery metrics: speed, bounce position, swing, deviation and line/height at the stumps.

Built for the Score Vision `DetectCricketDelivery` challenge and tested on its 5 example deliveries, each with a ground-truth answer sheet.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![YOLO](https://img.shields.io/badge/Ultralytics-YOLO26-111F68?style=flat)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat&logo=opencv&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat&logo=pytorch&logoColor=white)

## How it works

1. **Ball detection.** A YOLO model trained on ~7,000 labelled cricket images spots the ball in each frame. First a YOLOv8s model, then a YOLO26s model trained on a larger mixed dataset (Google Colab, T4 GPU, 60 epochs).
2. **Tracking.** Detections are linked frame to frame using motion continuity, so one bright false positive doesn't derail the track. Gaps are filled with a physics-guided search window.
3. **Camera calibration.** For the behind-the-bowler camera, three known pitch points (stump base, release, bounce) map screen pixels to real pitch metres.
4. **Events.** Release and bounce frames are found from the track (direction change at the bounce) and from bowler pose (wrist leaves the ball).
5. **Metrics.**
   - *Bounce position:* the bowling crease is fixed at 18.9 m from the stumps, so speed × time in the air gives the distance from release to bounce.
   - *Swing:* the ball's direction just after release vs. just before the bounce (tangent difference), not one straight line.
   - *Stump line/height:* projected from the post-bounce track.
   - *Scorecard:* OCR of the on-screen score graphic.

## Results

| Metric | Result (tight behind-the-bowler camera, clips C4/C5) |
|---|---|
| Stump line (sideways position at stumps) | within 1–4 cm |
| Bounce position | within 4 cm (C4) and 33 cm (C5) |
| Bounce position, physics model on 3 clips | mean error ~0.33 m (manually reviewed event timing) |
| Tracking with motion continuity | 39/40 correct ball picks vs 37/40 detector-only |
| YOLO26s ball detector (validation) | 90.6% precision, 84.8% recall, 87.5% mAP50 |

**Known limits.**
- Wide, full-ground side-on shots aren't solved: the ball is only a few pixels wide, and the detector still flags false positives there.
- Edited highlight packages need the correct delivery found among the cuts first.
- Release height, 3D trajectory and post-bounce angle aren't measured automatically yet.

## Repo layout

| Folder | Contents |
|---|---|
| `training/` | Detector training scripts (Apple Silicon MPS and Colab), dataset configs, YOLOv8s training plots and metrics in `results/` |
| `models/` | Trained weights: `ball_detector.pt` (YOLOv8s) and `yolo26_ball_detector.pt` (YOLO26s) |
| `pipeline/` | Ball candidates, tracker, camera calibration, pitch keypoints, cut detection, physics trajectory, bounce/speed/swing methods, per-clip ball tracks, pitch map and results workbook |
| `analysis/` | Follow-up experiments: physics-guided search areas, gap filling, event timing, release pose (YOLO26-pose), bowling-arm classifier. Each folder has its own report. |

## Datasets (not included)

No datasets are stored in this repo. To reproduce, download them from the original sources:

| Used for | Dataset | Source |
|---|---|---|
| Ball detector (original set, ~1,900 images) | Cricket Ball Dataset for YOLO | [Kaggle: kushagra3204/cricket-ball-dataset-for-yolo](https://www.kaggle.com/datasets/kushagra3204/cricket-ball-dataset-for-yolo) |
| Ball detector (added set, ~15,400 images, CC BY 4.0) | NEW BALL TRACKING | [Roboflow Universe: cricket-ball-tracking-dataset/new-ball-tracking](https://universe.roboflow.com/cricket-ball-tracking-dataset/new-ball-tracking) |
| Bowling-arm classifier | Cricket Bowling Action Recognition | [Kaggle: bigyansubedi/cricket-bowling-action-recognition](https://www.kaggle.com/datasets/bigyansubedi/cricket-bowling-action-recognition) |
| Test deliveries and answer sheet (5 clips) | Score Vision `DetectCricketDelivery` examples | Score Vision subnet (Bittensor) |

The detector's final training set used the full Kaggle set plus every 3rd frame of the Roboflow set (6,263 train / 468 valid / 327 test images, one class `ball`). See `training/data_combined_fast.yaml`.

## Run

The scripts in `pipeline/src/` and `analysis/` are separate experiment steps rather than one entry point. Run them from the `pipeline/` folder, with the example clips placed in `pipeline/data/videos/` (not included).

```bash
pip install ultralytics opencv-python numpy openpyxl
```
