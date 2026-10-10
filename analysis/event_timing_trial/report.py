from pathlib import Path
import json,cv2,numpy as np,pandas as pd
R=Path(__file__).resolve().parent;df=pd.read_csv(R/'results.csv');events=json.loads((R/'events.json').read_text());known=df[df.reference_bounce_frame.notna()];scored=known[known.predicted_bounce_frame.notna()];hits=int((scored.abs_error_frames<=1).sum());prefix={'C1':'f81d','C2':'9ef5','C3':'98e5','C4':'6a79','C5':'bad1'};D=Path('pipeline/data/videos');tiles=[]
for _,r in df.iterrows():
 tile=np.full((420,640,3),245,np.uint8)
 if pd.notna(r.predicted_bounce_frame):
  cap=cv2.VideoCapture(str(next(D.glob(prefix[r['clip']]+'*'))));cap.set(cv2.CAP_PROP_POS_FRAMES,int(r.predicted_bounce_frame));ok,im=cap.read();cap.release();assert ok;e=next(e for e in events if e['clip']==r['clip']);point=e['points'][2];cv2.circle(im,(round(point[1]),round(point[2])),20,(0,0,255),3);tile[60:]=cv2.resize(im,(640,360))
 cv2.putText(tile,f"{r['clip']} predicted turn: {r.predicted_bounce_frame}",(10,24),cv2.FONT_HERSHEY_SIMPLEX,.6,(20,20,20),1);cv2.putText(tile,f'Reviewed bounce: {r.reference_bounce_frame}',(10,49),cv2.FONT_HERSHEY_SIMPLEX,.6,(20,20,20),1);tiles.append(tile)
cv2.imwrite(str(R/'event_review.jpg'),np.vstack(tiles))
text=f'''# Automatic event timing: five existing clips

This is a deliberately simple **unseeded image-turn baseline**, not the previously manually initialised tracker. All detection ran on the local CPU. It starts candidate tracks automatically in a common frame 50–115 excerpt and looks for two downward movements followed by two upward movements. The first qualifying turn is its bounce proposal. No reference timing or manual ball seed enters prediction. Labels are read after predictions.

{df.to_markdown(index=False)}

## Result

Of four clips with reviewed bounce timing, {len(scored)} received a proposal and **{hits}/4 were within one frame**. C2 has no reliable reviewed bounce and cannot be scored. Timing agreement alone does not prove the tracked object is the ball; inspect event_review.jpg. These are known development examples, not held-out validation. The frame window is preselected, so this is not whole-video automatic event acquisition.

Reference bounce times come from an earlier tracker event subsequently visually reviewed, with nominal half-frame uncertainty. They are not independently blinded labels. The tolerance is one frame (40 ms at 25 fps). The algorithm confirms turns after subsequent observations; confirmation_frame records that delay rather than pretending to know the bounce immediately.

## Release timing

**Not automatically measured.** A track's first detection is not evidence that the ball just left the hand. It can start early on a distractor or late after occlusion. Track-start values are saved for diagnosis only, not reported as release estimates. Reliable release timing requires identifying the bowling hand and the ball separating from it; this experiment has no such signal. Existing manually reviewed release intervals remain the only release timings.

## Reproduce

Run `python3 analysis/event_timing_trial/run.py`, then `python3 analysis/event_timing_trial/report.py` from the workspace root. Same Python/YOLO dependencies as earlier trials. protocol.json contains fixed rules; raw_detections.json and events.json preserve intermediate results; results.csv contains scoring. No source files or production tracker were changed.
'''
(R/'REPORT.md').write_text(text);print(f'Within one frame: {hits}/4; proposals {len(scored)}/4')
