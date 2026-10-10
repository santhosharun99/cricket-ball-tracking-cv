from pathlib import Path
import json,cv2,numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;raw=json.loads((R/'c2_detections.json').read_text());cap=cv2.VideoCapture(str(next(Path('pipeline/data/videos').glob('9ef5*'))));refs=[];tiles=[]
ids={76:0,77:0,78:0,79:1,80:0,81:2,82:0,83:1,84:0,86:0}
for row in raw:
 f=row['frame']
 if f<76:refs.append({'clip':'C2','frame':f,'status':'unscorable','reason':'no reliable independent in-flight ball reference'});continue
 if f==85:sx,sy=530,123;ident=None
 else:
  c=next(c for c in row['candidates'] if c['id']==ids[f]);sx,sy=c['x'],c['y'];ident=c['id']
 cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,im=cap.read();x0,y0=int(sx)-10,int(sy)-10;crop=im[y0:y0+21,x0:x0+21];gray=cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY);hsv=cv2.cvtColor(crop,cv2.COLOR_BGR2HSV);mask=((gray>190)&(hsv[:,:,1]<85)).astype('uint8');n,labels,stats,cent=cv2.connectedComponentsWithStats(mask);choices=[i for i in range(1,n) if stats[i,4]>=3 and np.linalg.norm(cent[i]-[sx-x0,sy-y0])<8]
 if not choices:raise RuntimeError(f'needs review {f}')
 i=min(choices,key=lambda i:np.linalg.norm(cent[i]-[sx-x0,sy-y0]));x,y=cent[i]+[x0,y0];refs.append({'clip':'C2','frame':f,'status':'visible','x':float(x),'y':float(y),'reviewed_candidate_id':ident,'method':'manual ball identity + raw bright-component centroid; F85 manually seeded visible ball with no detector box'})
 tile=im[int(y)-20:int(y)+21,int(x)-20:int(x)+21].copy();cv2.drawMarker(tile,(20,20),(0,255,0),cv2.MARKER_CROSS,5,1);tiles.append((f,Image.fromarray(cv2.cvtColor(tile,cv2.COLOR_BGR2RGB)).resize((123,123))))
sheet=Image.new('RGB',(6*123,2*148),'white');draw=ImageDraw.Draw(sheet)
for i,(f,t) in enumerate(tiles):x=i%6*123;y=i//6*148;sheet.paste(t,(x,y));draw.text((x+5,y+125),f'C2 F{f}',fill='black')
sheet.save(R/'C2_reference_review.jpg');(R/'c2_references.json').write_text(json.dumps(refs,indent=2))
