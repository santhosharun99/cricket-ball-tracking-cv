from pathlib import Path
import pandas as pd,json
R=Path(__file__).resolve().parent
d=pd.read_csv(R/'results.csv');a=d.query("mode=='video_speed_assumed_height' and model=='air_resistance'");plain=d.query("mode=='video_speed_assumed_height' and model=='no_air_resistance'")
lines=['| Clip | Calculated bounce | Correct bounce | Missed by |','|---|---:|---:|---:|']
for _,r in a.iterrows():lines.append(f"| {r['clip']} | {r.predicted_bounce_x_m:.2f} m | {r.true_bounce_x_m:.2f} m | {r.absolute_error_m*100:.0f} cm |")
report='''# First test on the example videos

**The idea is promising enough to keep testing.** Using the speed displayed in the videos, timing checked from the frames, and the same assumptions for every ball, the model landed within half a metre on all three usable clips.

'''+ '\n'.join(lines)+f'''

Average miss: **{a.absolute_error_m.mean()*100:.0f} cm**. Without air resistance, it was **{plain.absolute_error_m.mean()*100:.0f} cm**.

If “accurate” means within 50 cm, the result is **3/3 usable clips (100%)**, with coverage of **3/5 example clips (60%)**. All three were also within 1 m. This is a tiny, retrospective, manually reviewed pilot—not a claim that the automatic tracker is 100% accurate. Five examples are not enough to measure general performance or choose final blending weights. This is not the competition's official score.

## What happened with the other two?

- **C3:** missed by about **25 cm** when given the speed from the answer sheet and the same assumed height. I did not find a readable speed in the sampled scoreboards, so C3 is excluded from the video-input success rate. Its result tests the calculation only.
- **C2:** not scored. The hidden early flight and uncertain bounce do not give reliable timing. It would be misleading to manufacture a duration from its correct bounce distance.

## What went into the estimate?

For every scored clip: release 10 cm ahead of the bowler-end popping crease (18.8 m from the striker's wicket), release height 2 m, and one shared air-resistance setting. These assumptions were fixed before computing this trial's errors. The ball's release speed was read directly from the later broadcast graphic: C1 **138.5**, C4 **136.5**, C5 **139.2 km/h**. No bounce answer, true height or true speed entered these three video-input predictions.

The release happens between frames. I used the middle of the last attached-ball frame and the first clearly detached-ball frame, consistently:

| Clip | Release interval, frames | Bounce frame | Flight time used |
|---|---|---|---|
| C1 | 90–91 | 98 | 0.300 s |
| C3 | 83–84 | 95 | 0.460 s |
| C4 | 92–93 | 104 | 0.460 s |
| C5 | 73–74 | 84 | 0.420 s |

Frames are zero-based; these four clips are 25 fps. Bounce frames came from the prior tracking work and were visually checked against the original footage. A nominal ±half-frame uncertainty is retained for each event; it is an assumption, not independently labelled event truth. Release and speed reading in this pilot are manual; the full automatic pipeline has not been rerun. The answer file was inspected before annotating events, so the trial is not blinded. No frame was changed to improve the metric answer.

## The main weakness is timing

Moving the duration by one frame changes the result by roughly **1.3–1.5 metres**. The central estimates look good, but their precision depends on where the event lies between frames. The full timing brackets alone give roughly C1 **6.45–9.33 m**, C4 **1.17–3.86 m**, and C5 **2.20–4.97 m**. These are possible ranges under the chosen event brackets, not statistical confidence intervals, and do not include all model errors.

Changing the assumed release position by 10 cm moves the answer by 10 cm. Changing assumed height by 20 cm has a much smaller effect on bounce distance in these clips. Different air-resistance assumptions can also shift the answer materially. All one-at-a-time checks are saved in `sensitivity.csv`; none were used to retune each clip.

## Can it help the visual tracker?

**Yes, as a candidate supporting estimate.** The prototype includes a combination function: a clearer visual estimate gets more weight; a more certain physics estimate gets more weight. If they strongly disagree, it returns a conflict instead of averaging them into a misleading answer. Its checks pass, but its weights have not been calibrated on real tracking errors, and it has not been installed in the existing tracker.

There are three practical limits:

1. This calculation uses the time of the bounce. It can fill gaps *between known events*, but cannot independently recover a completely hidden bounce from timing that we do not know. For that, the tracker needs an independently estimated early-flight direction or several possible trajectories.
2. The speed graphics appear after the delivery. They work when processing a complete clip, but are unavailable for a live prediction before the bounce. A live system needs its own independent speed estimate.
3. The simulator produces positions in metres. Drawing a search region onto video pixels still needs camera calibration. The simulator and visual tracker may share timing/camera errors; do not treat their uncertainties as independent without checking.

The example answer sheets do **not** include post-bounce angle, so no angle accuracy is claimed. The illustration shows the calculated pre-bounce paths, not measured 3D trajectories. A clean visual-only metric baseline was not available: earlier calibration work used selected example information, so no claim that fusion outperforms visual-only tracking has been made.

## Files and reproducibility

- `observations.json`: fixed assumptions, event brackets and independently read speeds.
- `simulator.py`: flight simulator and experimental weighting helper; no access to the answer sheet.
- `run_trial.py`: runs the comparison and equation/weighting checks; answer fields are used only for scoring and clearly labelled diagnostic runs.
- `results.csv`, `summary.csv`, `sensitivity.csv`: complete numerical results, including failed/ineligible cases described above.
- `inventory.json`: original video paths, frame rates and hashes.
- `comparison.png`: calculated paths and actual bounce locations.
- `C1_speed_evidence.jpg`, `C4_speed_evidence.jpg`, `C5_speed_evidence.jpg`: readable speed graphics.
- `*_release_detail.jpg`, `*_bounce_detail.jpg`: frame-review evidence. C1's tight bounce crop clips the lowest point; the wider events sheet and the prior tracker event provide context, rather than pretending the crop alone proves ground contact.

Run from the project directory:

```sh
python3 analysis/video_trial/run_trial.py
python3 analysis/video_trial/write_report.py
```

The frame-review helpers reproduce crops from original videos. Dependencies: the earlier analysis requirements plus OpenCV and Pillow; installed versions are saved in `environment.json`. Source videos and the original tracking project were left unchanged.

Answer source: `pipeline/data/examples.json`. Video source: the same project's `data/videos/` folder. Clip names C1–C5 follow the file ordering in that answer file.

Technical assumptions for reproduction: quadratic drag, air density 1.225 kg/m³, drag coefficient 0.5, mass 0.156 kg, radius 0.036 m, gravity 9.81 m/s², no wind/spin/lateral heading, point-contact height zero. These are illustrative shared assumptions, not measured pitch/ball conditions. The initial vertical velocity is solved so the trajectory reaches ground at the observed bounce time while preserving the supplied initial speed. The earlier 200k-row learned model is not used here; this directly tests your timing idea.
'''
(R/'REPORT.md').write_text(report)
import cv2,PIL,numpy,scipy,platform,hashlib
(R/'environment.json').write_text(json.dumps({'python':platform.python_version(),'opencv':cv2.__version__,'pillow':PIL.__version__,'numpy':numpy.__version__,'scipy':scipy.__version__,'answer_file_sha256':hashlib.sha256(Path('pipeline/data/examples.json').read_bytes()).hexdigest()},indent=2))
print(R/'REPORT.md')
