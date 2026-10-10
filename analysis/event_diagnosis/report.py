from pathlib import Path
import json,cv2,numpy as np,pandas as pd,subprocess,shutil
R=Path(__file__).resolve().parent;results=pd.read_csv(R/'event_results.csv');trace=json.loads((R/'trace.json').read_text());timeline=json.loads((R/'timeline.json').read_text());prefix={'C1':'f81d','C2':'9ef5','C3':'98e5','C4':'6a79','C5':'bad1'};D=Path('pipeline/data/videos');out=cv2.VideoWriter(str(R/'events_raw.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),10,(960,620))
for clip in prefix:
 cap=cv2.VideoCapture(str(next(D.glob(prefix[clip]+'*'))))
 for r in [x for x in timeline if x['clip']==clip]:
  f=r['frame'];cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,im=cap.read();assert ok;c=r['selected'];e=r['event'];status=e['status'] if e else 'no bounce event'
  if c:cv2.circle(im,(round(c['x']),round(c['y'])),16,(0,190,0),3)
  canvas=np.full((620,960,3),245,np.uint8);canvas[60:600]=cv2.resize(im,(960,540));cv2.putText(canvas,f'{clip} F{f} | Bounce: {status}',(12,25),0,.7,(20,20,20),2)
  desc=f"Candidate frame {e['bounce_frame']}" if e else 'Five verified initial ball sightings; subsequent selections automatic'
  cv2.putText(canvas,desc,(12,50),0,.6,(20,20,20),1)
  for _ in range(2):out.write(canvas)
 cap.release()
out.release();subprocess.run([shutil.which('ffmpeg'),'-y','-loglevel','error','-i',str(R/'events_raw.mp4'),'-c:v','libx264','-pix_fmt','yuv420p','+faststart' if False else '-movflags','+faststart',str(R/'events.mp4')],check=True)
report='''# Bounce confirmation diagnosis

C4 was not a wrong bounce position: the seeded guide selected the ball through frame105, including its downward-to-upward turn at104. There are no detector boxes at106–108, so the previous rule cannot obtain a second upward observation. Visual review of original frames saved in C4_review.jpg supports this account. Later low-confidence boxes at109/110 are rejected by the guide. Do not assume they are the ball.

A new small state machine retains a tentative bounce after two downward segments and one upward segment. Another upward observation within three frames confirms it. A contradictory sighting rejects it; no confirming sighting leaves it explicitly unconfirmed. Only accepted detections enter this rule, never predicted points. Segment gaps must be at most two frames when opening a candidate. Threshold remains5px/frame.

'''+results.to_markdown(index=False)+'''

There are still **three confirmed bounces out of four scorable clips**, plus one correctly located but unconfirmed candidate. This is not a new 100% accuracy claim. C2 has no event/reference. All tracks start from five manually verified ball sightings. This modification was motivated by a known C4 failure; all results are development diagnostics.

The new state does not solve unseeded foot/body false tracks or release timing. Its value is preserving useful uncertainty instead of silently losing the event. No source/production pipeline changed.

Checks passed for confirmed, expired/unconfirmed, contradictory/rejected and jitter sequences. All five clip histories replayed using cached local detections; no model inference or cloud compute was needed. events.mp4 shows state transitions, not a ground-truth-labelled detection accuracy test after the original scoring windows.

Reproduce from project root:
```
python3 analysis/event_diagnosis/trace.py
python3 analysis/event_diagnosis/evaluate_state.py
python3 analysis/event_diagnosis/report.py
```

Next: inspect locally available hand/pose tools for acquisition and release, then test explicit hand-ball separation rather than equating track start with release. No pose/X3D model files were found in the two inspected project directories; this is not a search of every computer cache. Models must not be downloaded or trained silently.
'''
(R/'REPORT.md').write_text(report)
