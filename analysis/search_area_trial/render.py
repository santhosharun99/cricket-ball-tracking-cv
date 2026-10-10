from pathlib import Path
import json,cv2,pandas as pd,numpy as np,subprocess,shutil
R=Path(__file__).resolve().parent;A=R.parent/'ambiguity_trial';df=pd.read_csv(R/'cases.csv');summary=pd.read_csv(R/'summary.csv');base=pd.read_csv(A/'sequential_cases.csv');D=Path('pipeline/data/videos');prefix={'C1':'f81d','C2':'9ef5','C3':'98e5','C4':'6a79','C5':'bad1'}
writer=cv2.VideoWriter(str(R/'preview_raw.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),6,(1280,500));stills=[]
for clip in prefix:
 cap=cv2.VideoCapture(str(next(D.glob(prefix[clip]+'*'))))
 for _,r in df[(df['clip']==clip)&(df.method=='predicted_roi')].iterrows():
  cap.set(cv2.CAP_PROP_POS_FRAMES,int(r.frame));ok,orig=cap.read();assert ok;canvas=np.full((500,1280,3),245,np.uint8)
  for k in range(2):
   im=orig.copy()
   if k==0:
    b=base[(base['clip']==clip)&(base.frame==r.frame)&(base.method=='bounce_reset_visual_override')].iloc[0];status=b.status;raw=json.loads((A/'c2_detections.json').read_text()) if clip=='C2' else json.loads((R.parent/'gap_trial/detections.json').read_text());cs=next(x['candidates'] for x in raw if x['clip']==clip and x['frame']==r.frame)
    c=next((x for x in cs if x['id']==b.selected_id),None);title='Previous motion-guided detector'
    if c:cv2.circle(im,(round(c['x']),round(c['y'])),18,(0,180,0) if status=='correct' else (0,0,255),3)
   else:
    title='Predicted area + local ball search';status=r.status;cv2.rectangle(im,(int(r.x0),int(r.y0)),(int(r.x0+384),int(r.y0+384)),(255,160,0),3);cv2.drawMarker(im,(round(r.prediction_x),round(r.prediction_y)),(0,190,255),cv2.MARKER_CROSS,20,2)
    if pd.notna(r.selected_x):cv2.circle(im,(round(r.selected_x),round(r.selected_y)),18,(0,180,0) if status=='correct' else (0,0,255),3)
   canvas[70:430,k*640:(k+1)*640]=cv2.resize(im,(640,360));cv2.putText(canvas,title,(k*640+10,27),cv2.FONT_HERSHEY_SIMPLEX,.6,(30,30,30),2);cv2.putText(canvas,f'{clip} frame {int(r.frame)}: {status}',(k*640+10,54),cv2.FONT_HERSHEY_SIMPLEX,.5,(30,30,30),1)
  cv2.putText(canvas,'Blue box: search crop | yellow cross: prediction | green/red ring: correct/wrong selection',(10,456),cv2.FONT_HERSHEY_SIMPLEX,.52,(30,30,30),1);cv2.putText(canvas,'Development clips; five verified starting sightings. Predictions are never counted as detections.',(10,482),cv2.FONT_HERSHEY_SIMPLEX,.5,(30,30,30),1)
  for _ in range(3):writer.write(canvas)
  if clip=='C2' and r.frame==85:stills.append(canvas)
 cap.release()
writer.release();cv2.imwrite(str(R/'example.jpg'),stills[0]);subprocess.run([shutil.which('ffmpeg'),'-y','-loglevel','error','-i',str(R/'preview_raw.mp4'),'-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(R/'comparison.mp4')],check=True)
lines=['# Predicted search-area experiment','','**Result: no additional detection improvement in this trial.** Predicted-area search and last-position search both matched the previous guide at 39/40 visible frames. Both crops contained the ball in all 40 labelled frames. C2 frame 85 remained undetected despite being inside the crop. This suggests the remaining failure concerns recognising the ball, rather than locating the search area. The extra search is an experimental option, not yet justified as the default.','',summary.to_markdown(index=False),'','## What was tested','The same local YOLO26 ball model ran on CPU, using 4 threads. Each method began with the same five verified observations. Later history contained only its own accepted detections. A 384-pixel square around the predicted position was resized for detection at 640 pixels. Candidates were checked against the causal motion prediction. When none passed, the previous full-frame candidate selector was used. The allowed distance grows after missed detections.','', 'A second method cropped around the last sighting instead of the prediction. This controls for the benefit of enlarging the ball. Full-frame results were reused from the previous run; crop timing therefore measures additional cost, not end-to-end speed.','', '## Metrics and limitations','Correct means within 20 pixels of a reviewed visible-ball reference. There are 40 visible labelled frames, one known false pitch-mark frame and one unscorable frame. All are correlated development examples. This is not held-out or fully automatic accuracy: starting points were manually verified and model training overlap remains unknown. No thresholds were tuned after scoring.','', 'This uses local image motion, not calibrated gravity/drag in world coordinates. No future bounce, speed graphic or true bounce location enters selection. A 2D overlay is valid; metre distances and 3D/post-bounce angles cannot be validated from this experiment. Existing metric simulator results remain separate.','', '## Additional measurements']
for method,g in df.groupby('method'):
 v=g[g.status.isin(['correct','wrong','missed_visible'])];e=v.error_px.dropna();lines.append(f'- {method}: crop includes labelled ball in {int(v.roi_covers_reference.sum())}/{len(v)} frames; mean accepted position error {e.mean():.2f}px; additional mean crop inference {g.cpu_seconds.mean():.3f}s/frame. Position error excludes missed detections; use counts above alongside it.')
lines+=['','## Reproduce','Run from project root:','```sh','python3 analysis/search_area_trial/run.py','python3 analysis/search_area_trial/render.py','```','Dependencies: Python, torch, ultralytics, numpy, pandas, opencv-python, tabulate, and ffmpeg. Input paths are at the top of run.py. Outputs include per-frame choices, all crop candidates, fixed protocol, model hash and a comparison video. All model inference explicitly uses device=cpu.']
(R/'REPORT.md').write_text('\n'.join(lines)+'\n')
print(summary.to_string(index=False))
