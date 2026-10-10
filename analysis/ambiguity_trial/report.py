from pathlib import Path
import json,cv2,numpy as np,pandas as pd,hashlib,subprocess,shutil
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;df=pd.read_csv(R/'sequential_cases.csv');raw=json.loads((R/'c2_detections.json').read_text());det={r['frame']:r['candidates'] for r in raw};refs={r['frame']:r for r in json.loads((R/'c2_references.json').read_text()) if r['status']=='visible'};video=next(Path('pipeline/data/videos').glob('9ef5*'));cap=cv2.VideoCapture(str(video));out=cv2.VideoWriter(str(R/'comparison_raw.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),12,(1280,470));stills=[]
for f in range(76,87):
 cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,original=cap.read();canvas=np.full((470,1280,3),245,np.uint8)
 for k,method in enumerate(['detector_only','bounce_reset_visual_override']):
  im=original.copy();title='Detector only' if k==0 else 'Detector + motion guide'
  if f<=80:
   status='Initial known ball sightings';r=refs[f];cv2.circle(im,(round(r['x']),round(r['y'])),16,(255,170,0),3)
  else:
   row=df[(df['clip']=='C2')&(df.frame==f)&(df.method==method)].iloc[0];status=row.status.replace('_',' ')
   if not pd.isna(row.selected_id):
    c=next(c for c in det[f] if c['id']==int(row.selected_id));color=(0,180,0) if row.status=='correct' else (0,0,255);cv2.circle(im,(round(c['x']),round(c['y'])),18,color,4)
   elif k==1 and not pd.isna(row.prediction_x):
    cv2.drawMarker(im,(round(row.prediction_x),round(row.prediction_y)),(0,190,255),cv2.MARKER_CROSS,25,3);status='Prediction only: NOT a detection'
  canvas[60:420,k*640:(k+1)*640]=cv2.resize(im,(640,360));cv2.putText(canvas,title,(k*640+15,25),cv2.FONT_HERSHEY_SIMPLEX,.7,(30,30,30),2);cv2.putText(canvas,f'C2 frame {f} | {status}',(k*640+15,49),cv2.FONT_HERSHEY_SIMPLEX,.48,(30,30,30),1)
 cv2.putText(canvas,'Slowed for inspection. Five manually verified starting sightings; no later corrections supplied.',(15,449),cv2.FONT_HERSHEY_SIMPLEX,.55,(30,30,30),1)
 for _ in range(8):out.write(canvas)
 if f in [82,84,85]:stills.append(canvas)
out.release();cap.release();cv2.imwrite(str(R/'comparison.jpg'),np.vstack(stills))
ffmpeg=shutil.which('ffmpeg')
if ffmpeg:
 subprocess.run([ffmpeg,'-y','-loglevel','error','-i',str(R/'comparison_raw.mp4'),'-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(R/'comparison.mp4')],check=True)
else:shutil.copyfile(R/'comparison_raw.mp4',R/'comparison.mp4')
r=df[(df['clip']=='C2')&(df.frame==85)&(df.method=='bounce_reset_visual_override')].iloc[0];error=float(np.hypot(r.prediction_x-refs[85]['x'],r.prediction_y-refs[85]['y']))
report=f'''# Sequential tracking: does the motion guide help with real distractors?

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
- **Frame 85:** the detector returned no candidates. Both tracking methods recorded a missing detection. The guide's unconfirmed predicted position was **{error:.1f} pixels** from the manually reviewed ball centre, and it found the ball again at frame 86. This single interpolation result is encouraging but is **not counted as a successful detection** and was not inserted into the state as if observed.

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
'''
(R/'REPORT.md').write_text(report)
(R/'audit.json').write_text(json.dumps({'source_video':str(video),'source_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'predictor_sha256':hashlib.sha256((R.parent/'gap_trial_v2/predictor_v2.py').read_bytes()).hexdigest(),'protocol_sha256':hashlib.sha256((R/'protocol.json').read_bytes()).hexdigest(),'evaluated_visible_frames':40,'unconfirmed_frame85_prediction_error_px':error,'causal_history_check':bool((df.history_last_frame_before_choice<df.frame).all())},indent=2))
print(R/'REPORT.md')
