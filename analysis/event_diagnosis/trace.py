"""Separate timing test conditional on the existing five verified starting sightings."""
from pathlib import Path
import json,sys
import numpy as np,pandas as pd
R=Path(__file__).resolve().parent.parent/'event_timing_trial';sys.path.insert(0,str(R.parent/'gap_trial_v2'));from predictor_v2 import select_candidate
raw=json.loads((R/'raw_detections.json').read_text());det={(r['clip'],r['frame']):[{'id':i,'x':c[0],'y':c[1],'confidence':c[2]} for i,c in enumerate(r['candidates'])] for r in raw}
old=json.loads((R.parent/'gap_trial/detections.json').read_text())+json.loads((R.parent/'ambiguity_trial/c2_detections.json').read_text());old={(r['clip'],r['frame']):r['candidates'] for r in old};refs=json.loads((R.parent/'gap_trial/references.json').read_text())+json.loads((R.parent/'ambiguity_trial/c2_references.json').read_text());refs={(r['clip'],r['frame']):r for r in refs if r['status']=='visible'};rows=[];trace=[]
for s in json.loads((R.parent/'ambiguity_trial/seeds.json').read_text()):
 clip=s['clip'];history=[];event=None
 for f in s['frames']:
  c=next(c for c in old[clip,f] if c['id']==refs[clip,f]['reviewed_candidate_id']);history.append([f,c['x'],c['y']])
 for f in range(s['evaluation_start'],116):
  c,pred,meta=select_candidate(history,f,det[clip,f],'bounce_reset_visual_override')
  trace.append({"clip":clip,"frame":f,"selected":c,"prediction":pred.tolist(),"meta":meta,"history_before":[p[:] for p in history[-5:]],"candidates":det[clip,f]})
  if c is None:continue
  history.append([f,c['x'],c['y']]);a=np.array(history[-5:]);v=np.diff(a[:,2])/np.diff(a[:,0])
  if np.all(v[:2]>5) and np.all(v[2:]<-5):event=event or {'turn_frame':int(a[2,0]),'confirmation_frame':f}
 rows.append({'clip':clip,'bounce_proposal':event['turn_frame'] if event else None,'confirmation_frame':event['confirmation_frame'] if event else None})
labels={r['clip']:r['bounce_frames'] for r in json.loads((R.parent/'video_trial/observations.json').read_text())['clips']}
for r in rows:
 truth=labels[r['clip']];r['reference']=np.mean(truth) if truth else None;r['error_frames']=abs(r['bounce_proposal']-r['reference']) if truth and r['bounce_proposal'] is not None else None
(R.parent/'event_diagnosis/trace.json').write_text(json.dumps(trace,indent=2));print(pd.DataFrame(rows).to_string(index=False))
