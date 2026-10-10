"""Reproduce detector-assisted, visually adjudicated reference centroids.
Review labels define ball identity; centroid comes from original image brightness,
not the candidate's predicted box centre. Never label a missing/occluded ball by interpolation.
"""
from pathlib import Path
import json,cv2,numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;cfg=json.loads((R/'protocol.json').read_text());D=Path('pipeline/data/videos');raw=json.loads((R/'detections.json').read_text())
# Explicit review exceptions, decided from original frames before scoring predictions.
exclude={('C1',97):'ball partly occluded by bowler; detector picked a pitch mark',('C1',103):'bat interaction/ball not independently separable; candidate is pitch mark',('C5',86):'ball overlaps bat region; no unambiguous separate ball reference'}
choose={('C1',101):1,('C1',102):1,('C3',93):1}
refs=[]
for c,p in cfg['clips'].items():
 cap=cv2.VideoCapture(str(next(D.glob(p['prefix']+'*'))));tiles=[]
 for row in [r for r in raw if r['clip']==c]:
  f=row['frame']
  if (c,f) in exclude:
   refs.append({'clip':c,'frame':f,'status':'unscorable','reason':exclude[c,f]});continue
  candidates=row['candidates'];candidate=next(x for x in candidates if x['id']==choose[c,f]) if (c,f) in choose else max(candidates,key=lambda x:x['confidence'])
  sx,sy=candidate['x'],candidate['y'];cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,im=cap.read();x0,y0=int(sx)-18,int(sy)-18;crop=im[y0:y0+37,x0:x0+37];gray=cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY);hsv=cv2.cvtColor(crop,cv2.COLOR_BGR2HSV)
  mask=((gray>190)&(hsv[:,:,1]<85)).astype(np.uint8);n,labels,stats,centroids=cv2.connectedComponentsWithStats(mask)
  choices=[i for i in range(1,n) if stats[i,cv2.CC_STAT_AREA]>=4 and np.linalg.norm(centroids[i]-[sx-x0,sy-y0])<12]
  if not choices:raise RuntimeError(f'needs manual reference {c} {f}')
  i=min(choices,key=lambda i:np.linalg.norm(centroids[i]-[sx-x0,sy-y0]));x,y=centroids[i]+[x0,y0]
  refs.append({'clip':c,'frame':f,'x':float(x),'y':float(y),'status':'visible','reviewed_candidate_id':candidate['id'],'method':'human ball-identity review + original-image white-component centroid'})
  tile=im[max(0,int(y)-35):int(y)+36,max(0,int(x)-35):int(x)+36].copy();cv2.drawMarker(tile,(35,35),(0,255,0),cv2.MARKER_CROSS,7,1);tiles.append((f,Image.fromarray(cv2.cvtColor(tile,cv2.COLOR_BGR2RGB)).resize((142,142))))
 sheet=Image.new('RGB',(8*142,((len(tiles)+7)//8)*165),'white');draw=ImageDraw.Draw(sheet)
 for i,(f,tile) in enumerate(tiles):x=(i%8)*142;y=(i//8)*165;sheet.paste(tile,(x,y));draw.text((x+4,y+145),f'{c} F{f}',fill='black')
 sheet.save(R/f'{c}_reference_review.jpg')
(R/'references.json').write_text(json.dumps(refs,indent=2))
print('Visible labels',sum(r['status']=='visible' for r in refs),'unscorable',sum(r['status']!='visible' for r in refs))
