"""Local CPU-only sequential ROI experiment. Run: python3 analysis/search_area_trial/run.py"""
import os
os.environ['YOLO_CONFIG_DIR']='/tmp/Ultralytics'
os.environ['MPLCONFIGDIR']='/tmp/cricket-gap-mpl'
from pathlib import Path
import sys,json,time,hashlib
import numpy as np,pandas as pd,cv2,torch
from ultralytics import YOLO
R=Path(__file__).resolve().parent; A=R.parent/'ambiguity_trial'; G=R.parent/'gap_trial'
sys.path.insert(0,str(R.parent/'gap_trial_v2'))
from predictor_v2 import predict,select_candidate
D=Path('~/Downloads/cricket_project')
protocol={'device':'cpu','threads':4,'crop_size':384,'crop_imgsz':640,'conf':.05,'base_radius':60,'radius_growth_per_missing_frame':20,'max_radius':160,'match_radius':20,'methods':['predicted_roi','last_position_roi'],'fallback':'cached full-frame candidates with unchanged motion selector','labels':'scoring only after choice; five original manually verified seeds; no later corrections','hypothesis':'Does rerunning detector in predicted crop help beyond filtering full-frame boxes? Last-position crop controls for magnification.','limitation':'Known development clips, not held-out; local image motion, not calibrated metric physics.'}
(R/'protocol.json').write_text(json.dumps(protocol,indent=2))
raw=json.loads((G/'detections.json').read_text())+json.loads((A/'c2_detections.json').read_text()); det={(r['clip'],r['frame']):r['candidates'] for r in raw}
refs=json.loads((G/'references.json').read_text())+json.loads((A/'c2_references.json').read_text()); ref={(r['clip'],r['frame']):r for r in refs if r['status']=='visible'}
seeds=json.loads((A/'seeds.json').read_text()); prefixes={'C1':'f81d','C2':'9ef5','C3':'98e5','C4':'6a79','C5':'bad1'}
torch.set_num_threads(4);model=YOLO(str(D/'models/yolo26_ball_detector.pt')); rows=[]; details=[]
for s in seeds:
 clip=s['clip'];cap=cv2.VideoCapture(str(next((D/'data/videos').glob(prefixes[clip]+'*'))))
 initial=[]
 for f in s['frames']:
  c=next(c for c in det[clip,f] if c['id']==ref[clip,f]['reviewed_candidate_id']);initial.append([f,c['x'],c['y']])
 for method in protocol['methods']:
  history=[p[:] for p in initial]
  for f in range(s['evaluation_start'],s['end']+1):
   cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,im=cap.read();assert ok
   point,meta=predict(history,f);gap=f-history[-1][0];radius=min(160,60+20*(gap-1));center=point if method=='predicted_roi' else np.array(history[-1][1:]);h,w=im.shape[:2]
   x0=int(np.clip(round(center[0])-192,0,max(0,w-384)));y0=int(np.clip(round(center[1])-192,0,max(0,h-384)));crop=im[y0:y0+384,x0:x0+384]
   start=time.perf_counter();result=model.predict(crop,conf=.05,imgsz=640,device='cpu',verbose=False)[0];elapsed=time.perf_counter()-start;candidates=[]
   for j,(b,conf) in enumerate(zip(result.boxes.xyxy.cpu().numpy(),result.boxes.conf.cpu().numpy())):
    x1,y1,x2,y2=map(float,b);candidates.append({'id':j,'x':(x1+x2)/2+x0,'y':(y1+y2)/2+y0,'confidence':float(conf)})
   # Both crop arms use the same causal motion gate. Only crop location differs.
   chosen,_,_=select_candidate(history,f,candidates,'bounce_reset',radius=radius);source='crop'
   if chosen is None:
    chosen,_,_=select_candidate(history,f,det[clip,f],'bounce_reset_visual_override',radius=radius);source='full_frame_fallback' if chosen else 'prediction_only'
   status='unscorable';error=None;covered=None
   if (clip,f) in ref:
    truth=ref[clip,f];covered=x0<=truth['x']<x0+384 and y0<=truth['y']<y0+384
    error=float(np.hypot(chosen['x']-truth['x'],chosen['y']-truth['y'])) if chosen else None
    status=('correct' if error<=20 else 'wrong') if chosen else 'missed_visible'
   elif clip=='C1' and f==97:status='wrong_known_pitch_mark' if chosen else 'safe_abstention'
   row={'clip':clip,'frame':f,'method':method,'status':status,'error_px':error,'source':source,'prediction_x':float(point[0]),'prediction_y':float(point[1]),'x0':x0,'y0':y0,'radius':radius,'selected_x':chosen['x'] if chosen else None,'selected_y':chosen['y'] if chosen else None,'roi_covers_reference':covered,'cpu_seconds':elapsed,'history_last_frame':history[-1][0]};rows.append(row);details.append({**row,'candidates':candidates})
   if chosen:history.append([f,chosen['x'],chosen['y']])
  print(clip,method,'complete',flush=True)
 cap.release()
df=pd.DataFrame(rows);assert (df.history_last_frame<df.frame).all();df.to_csv(R/'cases.csv',index=False);(R/'detections.json').write_text(json.dumps(details,indent=2))
baseline=pd.read_csv(A/'sequential_cases.csv');combined=pd.concat([baseline[baseline.method.isin(['detector_only','bounce_reset_visual_override'])],df]);summary=combined.groupby(['method','status']).size().unstack(fill_value=0);summary.to_csv(R/'summary.csv');print(summary.to_string());print('Crop CPU seconds:',df.cpu_seconds.sum())
(R/'audit.json').write_text(json.dumps({'torch':torch.__version__,'device':'cpu','model_sha256':hashlib.sha256((D/'models/yolo26_ball_detector.pt').read_bytes()).hexdigest(),'causality_check':True,'crop_seconds_total':float(df.cpu_seconds.sum())},indent=2))
