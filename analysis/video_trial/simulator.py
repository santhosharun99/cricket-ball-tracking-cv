"""Standalone research simulator. No ground-truth access, no tracker modification."""
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

def simulate(speed_kph,height,duration,release_x=18.8,drag_coefficient=.5,mass=.156,radius=.036,rho=1.225,n=100):
    if speed_kph<=0 or height<=0 or duration<=0:raise ValueError('positive speed, height, duration required')
    v=speed_kph/3.6;g=9.81;k=.5*rho*drag_coefficient*np.pi*radius**2/mass
    def rhs(t,q):
        x,z,u,w=q;s=np.hypot(u,w)
        return [-u,w,-k*s*u,-g-k*s*w]
    def trajectory(w,ts):
        u=np.sqrt(max(0,v*v-w*w))
        return solve_ivp(rhs,[0,duration],[release_x,height,u,w],t_eval=ts,rtol=1e-8,atol=1e-9)
    if k==0:
        w=(.5*g*duration**2-height)/duration
        if abs(w)>=v:raise ValueError('incompatible timing and speed')
    else:
        w=brentq(lambda w:trajectory(w,[duration]).y[1,-1],-.999999*v,.999999*v)
    ts=np.linspace(0,duration,n);q=trajectory(w,ts).y
    return {'bounce_x':float(q[0,-1]),'impact_angle_deg':float(np.degrees(np.arctan2(-q[3,-1],q[2,-1]))),'release_angle_deg':float(np.degrees(np.arcsin(w/v))),'time':ts,'x':q[0],'z':q[1],'u':q[2],'w':q[3]}

def fuse_position(visual_x,visual_sd,physics_x,physics_sd,max_disagreement_sigma=3):
    """Optional metric-position experiment, not integrated or calibrated on real tracks.
    Assumes independent unbiased errors in the SAME metric coordinate system.
    Returns conflict instead of forcing incompatible estimates together.
    Shared timing/camera errors violate independence; calibrate covariance before deployment.
    """
    if not np.isfinite([visual_x,visual_sd,physics_x,physics_sd]).all() or min(visual_sd,physics_sd)<=0:raise ValueError('finite inputs and positive uncertainty required')
    if abs(visual_x-physics_x)>max_disagreement_sigma*np.hypot(visual_sd,physics_sd):return {'status':'conflict','position':None}
    weight=physics_sd**2/(visual_sd**2+physics_sd**2)
    return {'status':'candidate','position':weight*visual_x+(1-weight)*physics_x,'visual_weight':weight,'physics_weight':1-weight,'sd':np.sqrt(1/(1/visual_sd**2+1/physics_sd**2))}
