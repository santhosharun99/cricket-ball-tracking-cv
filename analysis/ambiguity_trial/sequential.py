from pathlib import Path
import sys,json
import numpy as np,pandas as pd
R=Path(__file__).resolve().parent;BASE=R.parent/'gap_trial';sys.path.insert(0,str(R.parent/'gap_trial_v2'));from predictor_v2 import select_candidate
raw=json.loads((BASE/'detections.json').read_text());refs=json.loads((BASE/'references.json').read_text());cfg=json.loads((BASE/'protocol.json').read_text());protocol=json.loads((R/'protocol.json').read_text());cfg['clips']['C1']['end']=102
if (R/'c2_references.json').exists():
 raw+=json.loads((R/'c2_detections.json').read_text());refs+=json.loads((R/'c2_references.json').read_text());cfg['clips']['C2']={'start':58,'end':86}
det={(r['clip'],r['frame']):r['candidates'] for r in raw};ref={(r['clip'],r['frame']):r for r in refs if r['status']=='visible'}
def confident(candidates):
 if not candidates:return None
 top=max(candidates,key=lambda c:c['confidence']);rivals=[c['confidence'] for c in candidates if np.hypot(c['x']-top['x'],c['y']-top['y'])>20]
 return top if top['confidence']>=.6 and top['confidence']-max(rivals,default=0)>=.2 else None
rows=[];seedlog=[]
for clip,p in cfg['clips'].items():
 seeds=[]
 for f in range(p['start'],p['end']+1):
  if (clip,f) not in ref:continue
  r=ref[clip,f];c=next((c for c in det[clip,f] if c['id']==r.get('reviewed_candidate_id')),None)
  if c is not None:seeds.append([f,c['x'],c['y']])
  if len(seeds)==5:break
 if len(seeds)<5:seedlog.append({'clip':clip,'status':'insufficient_seed'});continue
 seedlog.append({'clip':clip,'frames':[int(s[0]) for s in seeds],'evaluation_start':int(seeds[-1][0])+1,'end':p['end']})
 for method in protocol['methods']:
  history=[s[:] for s in seeds]
  for f in range(int(seeds[-1][0])+1,p['end']+1):
   candidates=det[clip,f];meta={};point=None
   if method=='detector_only':chosen=max(candidates,key=lambda c:c['confidence']) if candidates else None
   elif method=='confidence_only':chosen=confident(candidates)
   else:chosen,point,meta=select_candidate(history,f,candidates,method)
   # Scoring occurs after choice; labels never alter predictor history.
   status='unscorable';error=np.nan
   if (clip,f) in ref:
    truth=np.array([ref[clip,f]['x'],ref[clip,f]['y']])
    if chosen is None:status='missed_visible'
    else:
     error=float(np.linalg.norm(np.array([chosen['x'],chosen['y']])-truth));status='correct' if error<=20 else 'wrong'
   elif clip=='C1' and f==97:status='wrong_known_pitch_mark' if chosen is not None else 'safe_abstention'
   rows.append({'clip':clip,'frame':f,'method':method,'status':status,'selected_id':chosen['id'] if chosen else None,'confidence':chosen['confidence'] if chosen else np.nan,'error_px':error,'history_last_frame_before_choice':history[-1][0],'history_frames':','.join(str(int(h[0])) for h in history[-5:]),'prediction_x':point[0] if point is not None else np.nan,'prediction_y':point[1] if point is not None else np.nan,**meta})
   if chosen is not None:history.append([f,chosen['x'],chosen['y']])
df=pd.DataFrame(rows);df.to_csv(R/'sequential_cases.csv',index=False);(R/'seeds.json').write_text(json.dumps(seedlog,indent=2));summary=df.groupby(['method','status']).size().unstack(fill_value=0);summary.to_csv(R/'summary.csv');print(summary.to_string());df.groupby(['clip','method','status']).size().to_csv(R/'per_clip.csv')
assert (df.history_last_frame_before_choice<df.frame).all()
