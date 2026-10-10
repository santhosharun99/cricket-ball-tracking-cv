from pathlib import Path
import json,numpy as np,pandas as pd
from predictor import predict,select_candidate
R=Path(__file__).resolve().parent;cfg=json.loads((R/'protocol.json').read_text());refs=json.loads((R/'references.json').read_text());raw=json.loads((R/'detections.json').read_text());det={(r['clip'],r['frame']):r['candidates'] for r in raw};ref={(r['clip'],r['frame']):r for r in refs if r['status']=='visible'}
rows=[];skip=[];methods=['detector_only','straight','curved','blend']
for clip,p in cfg['clips'].items():
    for cutoff in range(p['start']+4,p['end']):
        prior=[ref[clip,f] for f in range(p['start'],cutoff+1) if (clip,f) in ref]
        if len(prior)<5 or prior[-1]['frame']!=cutoff:continue
        prior=prior[-5:]
        # Seed from verified detector observations, not metric GT or smoothed references.
        history=[]
        for r in prior:
            c=next(c for c in det[clip,r['frame']] if c['id']==r['reviewed_candidate_id']);history.append([r['frame'],c['x'],c['y']])
        for gap in cfg['hidden_frame_counts']:
            target=cutoff+gap+1
            if target>p['end']:continue
            case=f'{clip}_last{cutoff}_hide{gap}'
            if (clip,target) not in ref:
                skip.append({'case':case,'reason':'first return frame lacks unambiguous visible reference'});continue
            truth=np.array([ref[clip,target]['x'],ref[clip,target]['y']]);bounce=p['bounce_frame_for_scoring_only']
            phase='pre_bounce' if target<bounce else ('bounce_or_after' if cutoff<bounce else 'post_bounce_history')
            for method in methods:
                selected,point=select_candidate(history,target,det[clip,target],method,cfg['search_radius_px'])
                correct=selected is not None and np.linalg.norm(np.array([selected['x'],selected['y']])-truth)<=cfg['reference_match_radius_px']
                row={'case':case,'clip':clip,'last_seen_frame':cutoff,'gap':gap,'target_frame':target,'method':method,'phase':phase,'success':bool(correct),'wrong_selection':bool(selected is not None and not correct),'abstained':selected is None,'candidate_count':len(det[clip,target]),'prediction_error_px':float(np.linalg.norm(point-truth)) if point is not None else np.nan,'pred_x':float(point[0]) if point is not None else np.nan,'pred_y':float(point[1]) if point is not None else np.nan,'truth_x':truth[0],'truth_y':truth[1],'selected_id':selected['id'] if selected else None,'history_frames':','.join(str(int(h[0])) for h in history)}
                # Retry only after rejection; an accepted wrong ball is terminal failure.
                recovered_after=None;status='wrong_ball' if selected is not None and not correct else ('recovered' if correct else 'unrecovered')
                if correct:recovered_after=0
                if selected is None:
                    for delay in [1,2]:
                        f=target+delay
                        if f>p['end']:break
                        candidate,_=select_candidate(history,f,det[clip,f],method,cfg['search_radius_px'])
                        if candidate is None:continue
                        if (clip,f) not in ref:status='unscorable_accept';break
                        truth2=np.array([ref[clip,f]['x'],ref[clip,f]['y']])
                        if np.linalg.norm(np.array([candidate['x'],candidate['y']])-truth2)<=cfg['reference_match_radius_px']:recovered_after=delay;status='recovered'
                        else:status='wrong_ball'
                        break
                row.update(recovery_delay_frames=recovered_after,retry_status=status,three_frame_followup_available=target+2<=p['end']);rows.append(row)
frame=pd.DataFrame(rows);frame.to_csv(R/'cases.csv',index=False);pd.DataFrame(skip).to_csv(R/'excluded_cases.csv',index=False)
primary=frame[frame.gap.isin(cfg['primary_gap_counts'])]
for name,group in [('overall',primary),('long_gaps',frame[frame.gap==5])]:
 s=group.groupby('method').agg(cases=('case','count'),correct=('success','sum'),wrong=('wrong_selection','sum'),abstained=('abstained','sum'),recovery_rate=('success','mean'),median_prediction_error_px=('prediction_error_px','median'),mean_prediction_error_px=('prediction_error_px','mean')).reset_index();s.to_csv(R/f'{name}.csv',index=False);print(name,s.to_string(index=False))
primary.groupby(['clip','method']).agg(cases=('case','count'),correct=('success','sum'),wrong=('wrong_selection','sum'),median_error_px=('prediction_error_px','median')).to_csv(R/'per_clip.csv')
primary.groupby(['phase','method']).agg(cases=('case','count'),correct=('success','sum'),wrong=('wrong_selection','sum'),median_error_px=('prediction_error_px','median'),mean_error_px=('prediction_error_px','mean')).to_csv(R/'per_phase.csv')
primary.groupby(['gap','method']).agg(cases=('case','count'),correct=('success','sum'),median_error_px=('prediction_error_px','median')).to_csv(R/'per_gap.csv')
# Causality / numerical checks: only passed historical observations can affect output.
h=[[f,2*f,3*f+f*f] for f in range(5)];np.testing.assert_allclose(predict(h,7,'curved'),[14,70],atol=1e-8)
try:predict(h,4,'curved')
except ValueError:pass
else:raise AssertionError('future/present target accepted')
assert select_candidate(h,7,[],'blend')[0] is None
(R/'checks.json').write_text(json.dumps({'quadratic_equation_check':True,'future_or_present_history_rejected':True,'empty_candidates_abstain':True,'uses_metric_ground_truth':False,'uses_future_speed_or_bounce':False,'correct_history_seed_assumption':True},indent=2))
