from pathlib import Path
import os,json,hashlib
os.environ.setdefault('MPLCONFIGDIR','/tmp/cricket-mpl')
import cv2,numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from simulator import simulate,fuse_position
ROOT=Path(__file__).resolve().parent
DATA=Path('pipeline/data')
obs=json.loads((ROOT/'observations.json').read_text());gt=json.loads((DATA/'examples.json').read_text());rows=[];sens=[];trajectories={};inventory=[]
for c in obs['clips']:
    f=next((DATA/'videos').glob(c['prefix']+'*'));cap=cv2.VideoCapture(str(f));fps=cap.get(5);cap.release();g=next(g['prediction'] for g in gt if c['prefix'] in g['video_url'])
    inventory.append({'clip':c['clip'],'file':str(f),'fps':fps,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'status':c['status']})
    if c['release_frames'] is None:continue
    duration=(np.mean(c['bounce_frames'])-np.mean(c['release_frames']))/fps
    for mode,v,h in [('answer_speed_height_diagnostic',g['kph'],g['release_z']),('answer_speed_assumed_height_diagnostic',g['kph'],2.0),('video_speed_assumed_height',c['broadcast_speed_kph'],2.0)]:
        if v is None:continue
        for name,cd in [('no_air_resistance',0.),('air_resistance',.5)]:
            pred=simulate(v,h,duration,drag_coefficient=cd)
            error=abs(pred['bounce_x']-g['bounce_x'])
            rows.append({'clip':c['clip'],'mode':mode,'model':name,'release_frame':np.mean(c['release_frames']),'bounce_frame':np.mean(c['bounce_frames']),'duration_s':duration,'speed_kph':v,'height_m':h,'predicted_bounce_x_m':pred['bounce_x'],'true_bounce_x_m':g['bounce_x'],'absolute_error_m':error,'within_0_5m':error<=.5,'within_1m':error<=1,'impact_angle_deg_unvalidated':pred['impact_angle_deg']})
            if name=='air_resistance' and mode in ['video_speed_assumed_height','answer_speed_assumed_height_diagnostic']:
                if c['clip'] not in trajectories or mode=='video_speed_assumed_height':trajectories[c['clip']]=(pred,g['bounce_x'],mode)
        # Fixed one-at-a-time assumption sensitivity; never select best setting against labels.
        if mode=='video_speed_assumed_height':
            for parameter,values in [('drag_coefficient',[.2,.35,.5,.65]),('release_x',[18.7,18.8,18.9,19.0]),('height',[1.8,2.,2.2]),('duration_offset',[-.04,0,.04])]:
                for value in values:
                    kw={'speed_kph':v,'height':h,'duration':duration};kw[parameter if parameter!='duration_offset' else 'duration']=value if parameter!='duration_offset' else duration+value
                    p=simulate(**kw);sens.append({'clip':c['clip'],'parameter':parameter,'value':value,'bounce_x_m':p['bounce_x'],'absolute_error_m':abs(p['bounce_x']-g['bounce_x'])})
            lo=(c['bounce_frames'][0]-c['release_frames'][1])/fps;hi=(c['bounce_frames'][1]-c['release_frames'][0])/fps
            sens.append({'clip':c['clip'],'parameter':'timing_interval_lower','value':lo,'bounce_x_m':simulate(v,h,lo)['bounce_x']})
            sens.append({'clip':c['clip'],'parameter':'timing_interval_upper','value':hi,'bounce_x_m':simulate(v,h,hi)['bounce_x']})
df=pd.DataFrame(rows);df.to_csv(ROOT/'results.csv',index=False);pd.DataFrame(sens).to_csv(ROOT/'sensitivity.csv',index=False);(ROOT/'inventory.json').write_text(json.dumps(inventory,indent=2))
summary=df.groupby(['mode','model']).agg(n=('clip','count'),mean_error_m=('absolute_error_m','mean'),max_error_m=('absolute_error_m','max'),within_half_m=('within_0_5m','mean'),within_one_m=('within_1m','mean')).reset_index();summary.to_csv(ROOT/'summary.csv',index=False)
fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained')
for ax,(c,(p,actual,mode)) in zip(axes.flat,trajectories.items()):
    ax.plot(p['x'],p['z'],color='#2563eb',label='Calculated path (height not validated)');ax.scatter([p['bounce_x']],[0],s=90,color='#2563eb',marker='o',label='Calculated bounce');ax.scatter([actual],[0],s=110,color='#ea580c',marker='x',label='Answer-sheet bounce');ax.axhline(0,color='#94a3b8',lw=1);ax.set_xlim(20,0);ax.set_ylim(-.2,2.4);ax.set_xlabel('Metres from batter’s wicket');ax.set_ylabel('Height (m)');ax.set_title(c+(' — answer-sheet speed' if 'diagnostic' in mode else ' — speed read from video'));ax.spines[['top','right']].set_visible(False)
axes.flat[0].legend(fontsize=7);fig.suptitle('First timing-based trial — same assumptions for every clip');fig.savefig(ROOT/'comparison.png',dpi=160)
# Equation and blending checks, not accuracy evidence for real tracking.
p=simulate(140,2,.35,drag_coefficient=0);assert abs(p['bounce_x']-5.260991)<1e-5
assert abs(simulate(140,2,.35)['z'][-1])<1e-6
assert fuse_position(5,.1,5.2,1)['visual_weight']>.98
assert fuse_position(5,1,5.2,.1)['physics_weight']>.98
assert fuse_position(1,.1,10,.1)['status']=='conflict'
print(df.query("mode=='video_speed_assumed_height'")[['clip','model','predicted_bounce_x_m','true_bounce_x_m','absolute_error_m']].to_string(index=False));print(summary.to_string(index=False))
