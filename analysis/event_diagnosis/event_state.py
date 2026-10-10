"""Causal bounce candidates; predictions must never be passed as observations."""
class BounceState:
    def __init__(self, min_velocity=5., max_confirmation_gap=3):
        self.min_velocity=min_velocity;self.max_confirmation_gap=max_confirmation_gap
        self.history=[];self.candidate=None;self.events=[];self.last_frame=-1
    def update(self,frame,point=None):
        if frame<=self.last_frame:raise ValueError('frames must increase')
        self.last_frame=frame
        if self.candidate and self.candidate['status']=='tentative' and frame-self.candidate['first_up_frame']>self.max_confirmation_gap:
            self.candidate['status']='unconfirmed';self.candidate['closed_frame']=frame
        if point is None:return self.candidate
        x,y=map(float,point)
        if self.candidate and self.candidate['status']=='tentative':
            previous=self.history[-1];velocity=(y-previous[2])/(frame-previous[0])
            if velocity < -self.min_velocity:
                self.candidate['status']='confirmed';self.candidate['confirmation_frame']=frame
            else:
                self.candidate['status']='rejected';self.candidate['closed_frame']=frame
        self.history.append((frame,x,y))
        if len(self.history)>=4:
            a=self.history[-4:];gaps=[a[i+1][0]-a[i][0] for i in range(3)]
            v=[(a[i+1][2]-a[i][2])/gaps[i] for i in range(3)]
            if max(gaps)<=2 and v[0]>self.min_velocity and v[1]>self.min_velocity and v[2]<-self.min_velocity:
                self.candidate={'bounce_frame':a[2][0],'first_up_frame':frame,'status':'tentative','confirmation_frame':None};self.events.append(self.candidate)
        return self.candidate
