"""Causal screen-space research predictors; no labels, videos or future event access."""
import numpy as np

def predict(history,target_frame,method):
    a=np.asarray(history,float) # frame, x, y
    if a.ndim!=2 or a.shape[1]!=3 or len(a)<5:raise ValueError('five prior observations required')
    a=a[-5:]
    if np.any(np.diff(a[:,0])<=0) or target_frame<=a[-1,0]:raise ValueError('history must be ordered and strictly in the past')
    t=a[:,0]-a[-1,0];h=target_frame-a[-1,0]
    linear=np.array([np.polyval(np.polyfit(t,a[:,i],1),h) for i in [1,2]])
    quad=np.array([np.polyval(np.polyfit(t,a[:,i],2),h) for i in [1,2]])
    if method=='straight':return linear
    if method=='curved':return quad
    if method=='blend':return .5*linear+.5*quad
    if method=='detector_only':return None
    raise ValueError(method)

def select_candidate(history,target_frame,candidates,method,radius=60):
    pred=predict(history,target_frame,method)
    if not candidates:return None,pred
    if method=='detector_only':return max(candidates,key=lambda c:c['confidence']),pred
    candidates=[c for c in candidates if np.linalg.norm(np.array([c['x'],c['y']])-pred)<=radius]
    if not candidates:return None,pred
    def score(c):
        distance=np.linalg.norm(np.array([c['x'],c['y']])-pred)
        return np.log(max(c['confidence'],1e-9))-.5*(distance/(radius/2))**2
    return max(candidates,key=score),pred
