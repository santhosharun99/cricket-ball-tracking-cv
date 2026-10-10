from pathlib import Path
import json,pandas as pd
from event_state import BounceState
R=Path(__file__).resolve().parent;trace=json.loads((R/'trace.json').read_text());rows=[];timeline=[]
for clip in ['C1','C2','C3','C4','C5']:
 rs=[r for r in trace if r['clip']==clip];state=BounceState()
 for f,x,y in rs[0]['history_before']:state.update(int(f),(x,y))
 for r in rs:
  c=r['selected'];e=state.update(r['frame'],(c['x'],c['y']) if c else None);timeline.append({'clip':clip,'frame':r['frame'],'selected':c,'event':dict(e) if e else None})
 first=state.events[0] if state.events else None;rows.append({'clip':clip,**(first or {'bounce_frame':None,'first_up_frame':None,'status':'none','confirmation_frame':None}),'event_count':len(state.events)})
# Score after inference; never choose event closest to reference.
labels={x['clip']:x['bounce_frames'] for x in json.loads((R.parent/'video_trial/observations.json').read_text())['clips']}
for r in rows:
 truth=labels[r['clip']];r['reference_frame']=sum(truth)/2 if truth else None;r['error_frames']=abs(r['bounce_frame']-r['reference_frame']) if truth and r['bounce_frame'] is not None else None
pd.DataFrame(rows).to_csv(R/'event_results.csv',index=False);(R/'timeline.json').write_text(json.dumps(timeline,indent=2));print(pd.DataFrame(rows).to_string(index=False))
# State-machine correctness, not evidence of real-video generalisation.
s=BounceState()
for f,y in enumerate([0,10,25,10]):s.update(f,(0,y))
assert s.candidate['status']=='tentative' and s.candidate['bounce_frame']==2
s.update(4,None);s.update(5,None);s.update(6,None);assert s.candidate['status']=='tentative'
s.update(7,None);assert s.candidate['status']=='unconfirmed'
s=BounceState()
for f,y in enumerate([0,10,25,10,0]):s.update(f,(0,y))
assert s.candidate['status']=='confirmed' and s.candidate['confirmation_frame']==4
s=BounceState()
for f,y in enumerate([0,10,25,10,20]):s.update(f,(0,y))
assert s.candidate['status']=='rejected'
s=BounceState()
for f,y in enumerate([0,1,-1,2,0]):s.update(f,(0,y))
assert not s.events
print('Confirmed/unconfirmed/rejected/jitter checks passed.')
