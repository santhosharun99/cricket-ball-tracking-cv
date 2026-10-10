"""Causal local bounce-turn reset. No files, ground truth or future inputs."""
import numpy as np

def predict(history,target_frame,reset=True):
    a=np.asarray(history,float)
    if a.ndim!=2 or a.shape[1]!=3 or len(a)<5 or not np.isfinite(a).all():raise ValueError('five finite prior observations required')
    a=a[-5:]
    if np.any(np.diff(a[:,0])<=0) or target_frame<=a[-1,0]:raise ValueError('history must be ordered and strictly before target')
    original=a.copy();turn=None;state='no_observed_turn'
    if reset:
        v=np.diff(a[:,2])/np.diff(a[:,0])
        for k in range(2,len(v)):
            if v[k-2]>5 and v[k-1]>5 and v[k]<-5:
                turn=k
        if turn is not None:
            a=a[turn:];out=np.diff(a[:,2])/np.diff(a[:,0]);state='confirmed_turn' if len(out)>=2 and np.all(out[:2]<-5) else 'tentative_turn'
    t=a[:,0]-original[-1,0];h=target_frame-original[-1,0]
    line=np.array([np.polyval(np.polyfit(t,a[:,j],1),h) for j in [1,2]])
    if len(a)>=4:
        curve=np.array([np.polyval(np.polyfit(t,a[:,j],2),h) for j in [1,2]]);point=.5*line+.5*curve
    else:point=line
    return point,{'state':state,'fit_points':len(a),'turn_frame':float(a[0,0]) if turn is not None else None}

def select_candidate(history,target_frame,candidates,method,radius=60):
    point,meta=predict(history,target_frame,reset=method!='blend')
    meta['selection_reason']='abstain'
    if not candidates:return None,point,meta
    top=max(candidates,key=lambda c:c['confidence'])
    if method=='detector_only':meta['selection_reason']='detector_only';return top,None,meta
    nearby=[c for c in candidates if np.linalg.norm(np.array([c['x'],c['y']])-point)<=radius]
    if nearby:
        selected=max(nearby,key=lambda c:np.log(max(c['confidence'],1e-9))-.5*(np.linalg.norm(np.array([c['x'],c['y']])-point)/(radius/2))**2)
        meta['selection_reason']='motion_gate';return selected,point,meta
    if method=='bounce_reset_visual_override':
        competitors=[c['confidence'] for c in candidates if np.hypot(c['x']-top['x'],c['y']-top['y'])>20]
        if top['confidence']>=.60 and top['confidence']-max(competitors,default=0)>=.20:
            meta['selection_reason']='clear_visual_override';return top,point,meta
    return None,point,meta
