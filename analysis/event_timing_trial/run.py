"""Exploratory unseeded image-turn timing. All inference runs on local CPU."""
import os
os.environ['YOLO_CONFIG_DIR']='/tmp/Ultralytics'
from pathlib import Path
import json,time,sys
import cv2,numpy as np,pandas as pd,torch
from ultralytics import YOLO
R=Path(__file__).resolve().parent;D=Path('~/Downloads/cricket_project');torch.set_num_threads(4)
protocol={'window':[50,115],'device':'cpu','threads':4,'imgsz':1280,'confidence':.05,'link_max_px_per_frame':100,'max_gap_frames':2,'event_rule':'two downward segments then two upward segments, each over 5 px/frame; report first qualifying track turn','initialization':'all detector candidates start tracks; nearest spatial links, no manual seeds','release_rule':'first detection in qualifying track is only a track-start proxy, NOT release','limitations':'Image turn may be distractor/bat/camera motion. Fixed common excerpt, not whole-video acquisition. Known development examples. No pose/hand separation evidence.'}
(R/'protocol.json').write_text(json.dumps(protocol,indent=2));model=YOLO(str(D/'models/yolo26_ball_detector.pt'))
prefix={'C1':'f81d','C2':'9ef5','C3':'98e5','C4':'6a79','C5':'bad1'};allraw=[];events=[]
for clip,pre in prefix.items():
 cap=cv2.VideoCapture(str(next((D/'data/videos').glob(pre+'*'))));fps=cap.get(cv2.CAP_PROP_FPS);tracks=[];found=[]
 for f in range(50,116):
  cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,im=cap.read();assert ok
  result=model.predict(im,conf=.05,imgsz=1280,device='cpu',verbose=False)[0];cs=[]
  for b,score in zip(result.boxes.xyxy.cpu().numpy(),result.boxes.conf.cpu().numpy()):cs.append([float((b[0]+b[2])/2),float((b[1]+b[3])/2),float(score)])
  allraw.append({'clip':clip,'frame':f,'candidates':cs});active=[i for i,t in enumerate(tracks) if f-t[-1][0]<=2];pairs=[]
  for i in active:
   t=tracks[i];gap=f-t[-1][0]
   for j,c in enumerate(cs):
    distance=np.hypot(c[0]-t[-1][1],c[1]-t[-1][2])
    if distance<=100*gap:pairs.append((distance/gap,i,j))
  usedt=set();usedc=set()
  for dist,i,j in sorted(pairs):
   if i in usedt or j in usedc:continue
   tracks[i].append([f,*cs[j]]);usedt.add(i);usedc.add(j)
  for j,c in enumerate(cs):
   if j not in usedc:tracks.append([[f,*c]])
  for i,t in enumerate(tracks):
   if t[-1][0]!=f or len(t)<5:continue
   a=np.array(t[-5:]);v=np.diff(a[:,2])/np.diff(a[:,0])
   if np.all(v[:2]>5) and np.all(v[2:]<-5):found.append({'clip':clip,'track_id':i,'turn_frame':int(a[2,0]),'confirmed_frame':f,'track_start_proxy':t[0][0],'fps':fps,'points':t[-5:]})
 cap.release();events.extend(found);print(clip,'complete; turn candidates',len(found),flush=True)
 (R/'raw_detections.json').write_text(json.dumps(allraw));(R/'events.json').write_text(json.dumps(events,indent=2))
# Labels are read only after all predictions have been generated.
labels=json.loads((R.parent/'video_trial/observations.json').read_text())['clips'];rows=[]
for label in labels:
 clip=label['clip'];es=[e for e in events if e['clip']==clip];e=es[0] if es else None;interval=label['bounce_frames'];truth=np.mean(interval) if interval else None
 rows.append({'clip':clip,'turn_candidates':len(es),'predicted_bounce_frame':e['turn_frame'] if e else None,'confirmation_frame':e['confirmed_frame'] if e else None,'reference_bounce_frame':truth,'abs_error_frames':abs(e['turn_frame']-truth) if e and truth is not None else None,'error_ms':1000*abs(e['turn_frame']-truth)/e['fps'] if e and truth is not None else None,'track_start_proxy_not_release':e['track_start_proxy'] if e else None,'release_reference':str(label['release_frames']),'release_status':'not measured: hand-ball separation unavailable'})
pd.DataFrame(rows).to_csv(R/'results.csv',index=False);print(pd.DataFrame(rows).to_string(index=False))
