from pathlib import Path
import json,sys
import numpy as np,pandas as pd
from predictor_v2 import predict,select_candidate
R=Path(__file__).resolve().parent;BASE=R.parent/'gap_trial';cfg=json.loads((BASE/'protocol.json').read_text());protocol=json.loads((R/'protocol.json').read_text());old=pd.read_csv(BASE/'cases.csv');raw=json.loads((BASE/'detections.json').read_text());det={(r['clip'],r['frame']):r['candidates'] for r in raw};ref={(r['clip'],r['frame']):r for r in json.loads((BASE/'references.json').read_text()) if r['status']=='visible'}
rows=[]
# Use the exact same case list, not a fresh sample or tuned exclusions.
for _,case in old.drop_duplicates('case').iterrows():
 clip=case['clip'];target=int(case.target_frame);cutoff=int(case.last_seen_frame)
 history=[]
 for f in map(int,case.history_frames.split(',')):
  r=ref[clip,f];c=next(c for c in det[clip,f] if c['id']==r['reviewed_candidate_id']);history.append([f,c['x'],c['y']])
 assert max(h[0] for h in history)==cutoff<target
 truth=np.array([case.truth_x,case.truth_y])
 for method in protocol['methods']:
  chosen,point,meta=select_candidate(history,target,det[clip,target],method,cfg['search_radius_px'])
  correct=chosen is not None and np.linalg.norm(np.array([chosen['x'],chosen['y']])-truth)<=cfg['reference_match_radius_px']
  row={k:case[k] for k in ['case','clip','gap','target_frame','last_seen_frame','history_frames','phase','truth_x','truth_y']};row.update(method=method,success=bool(correct),wrong_selection=bool(chosen is not None and not correct),abstained=chosen is None,prediction_error_px=float(np.linalg.norm(point-truth)) if point is not None else np.nan,pred_x=float(point[0]) if point is not None else np.nan,pred_y=float(point[1]) if point is not None else np.nan,selected_id=chosen['id'] if chosen else None,**meta)
  # Identical causal retry policy to v1: do not consume hidden observations;
  # accepted wrong ball is terminal failure, rejection may retry next frames.
  delay=0 if correct else None;status='recovered' if correct else ('wrong_ball' if chosen is not None else 'unrecovered')
  if chosen is None:
   for lag in [1,2]:
    f=target+lag
    if f>cfg['clips'][clip]['end']:break
    candidate,_,_=select_candidate(history,f,det[clip,f],method,cfg['search_radius_px'])
    if candidate is None:continue
    if (clip,f) not in ref:status='unscorable_accept';break
    actual=np.array([ref[clip,f]['x'],ref[clip,f]['y']])
    if np.linalg.norm(np.array([candidate['x'],candidate['y']])-actual)<=cfg['reference_match_radius_px']:delay=lag;status='recovered'
    else:status='wrong_ball'
    break
  row.update(recovery_delay_frames=delay,retry_status=status,three_frame_followup_available=target+2<=cfg['clips'][clip]['end']);rows.append(row)
df=pd.DataFrame(rows);df.to_csv(R/'cases.csv',index=False);primary=df[df.gap.isin([2,3])]
for name,group in [('overall',primary),('long_gaps',df[df.gap==5])]:
 s=group.groupby('method').agg(cases=('case','count'),correct=('success','sum'),wrong=('wrong_selection','sum'),abstained=('abstained','sum'),rate=('success','mean'),median_error_px=('prediction_error_px','median')).reset_index();s.to_csv(R/f'{name}.csv',index=False);print(name,s.to_string(index=False))
for axis in ['clip','phase','gap','state','selection_reason']:
 primary.groupby([axis,'method']).agg(cases=('case','count'),correct=('success','sum'),wrong=('wrong_selection','sum'),median_error_px=('prediction_error_px','median')).to_csv(R/f'per_{axis}.csv')
p=primary.pivot(index='case',columns='method',values='success');p.to_csv(R/'paired_outcomes.csv')
# Check the original baselines reproduce exactly on the identical cases.
for m in ['blend','detector_only']:
 a=df[df.method==m].set_index('case').sort_index();b=old[old.method==m].set_index('case').sort_index();assert a.success.equals(b.success)
 if m=='blend':np.testing.assert_allclose(a.pred_x,b.pred_x);np.testing.assert_allclose(a.pred_y,b.pred_y)
# Functional causality/turn checks, independent of video outcome scoring.
h=[[0,0,0],[1,1,10],[2,2,25],[3,3,45],[4,4,30]]
point,meta=predict(h,6);assert meta['state']=='tentative_turn' and meta['fit_points']==2;np.testing.assert_allclose(point,[6,0],atol=1e-8)
h2=[[0,0,0],[1,1,15],[2,2,35],[3,3,20],[4,4,5]]
point,meta=predict(h2,6);assert meta['state']=='confirmed_turn';np.testing.assert_allclose(point,[6,-25],atol=1e-8)
assert predict([[i,i,20*i] for i in range(5)],6)[1]['state']=='no_observed_turn'
assert predict([[i,i,1*(-1)**i] for i in range(5)],6)[1]['state']=='no_observed_turn'
try:predict(h,4)
except ValueError:pass
else:raise AssertionError('non-causal target')
assert select_candidate(h,6,[],'bounce_reset_visual_override')[0] is None
candidate={'id':0,'x':500,'y':500,'confidence':.8};c2={'id':1,'x':800,'y':800,'confidence':.75}
assert select_candidate(h,6,[candidate],'bounce_reset_visual_override')[2]['selection_reason']=='clear_visual_override'
assert select_candidate(h,6,[candidate,c2],'bounce_reset_visual_override')[0] is None
# Repeated detections at the same location are not a rival object.
cdup={'id':2,'x':501,'y':501,'confidence':.7};assert select_candidate(h,6,[candidate,cdup],'bounce_reset_visual_override')[0]['id']==0
(R/'checks.json').write_text(json.dumps({'same_cases_and_baselines_reproduced':True,'causal_history_boundaries_checked':True,'turn_reset_equations_checked':True,'small_jitter_does_not_trigger':True,'ambiguous_override_rejected':True,'empty_detection_abstains':True,'duplicate_box_handling_checked':True},indent=2))
