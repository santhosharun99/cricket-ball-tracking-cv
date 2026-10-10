import os,json
from pathlib import Path
os.environ.setdefault('YOLO_CONFIG_DIR','/tmp/cricket-gap-yolo')
import cv2,torch
from ultralytics import YOLO
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;cfg=json.loads((R/'protocol.json').read_text());D=Path('~/Downloads/cricket_project')
torch.set_num_threads(4)
model=YOLO(str(D/'models/yolo26_ball_detector.pt'))
allrows=[]
for c,p in cfg['clips'].items():
 cap=cv2.VideoCapture(str(next((D/'data/videos').glob(p['prefix']+'*'))));tiles=[]
 for f in range(p['start'],p['end']+1):
  cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,im=cap.read()
  if not ok:raise RuntimeError(f'{c} {f}')
  result=model.predict(im,conf=cfg['detector_confidence'],imgsz=cfg['detector_image_size'],device='cpu',verbose=False)[0]
  boxes=result.boxes.xyxy.cpu().numpy();confs=result.boxes.conf.cpu().numpy()
  # Sort spatially for stable review labels; no track filtering.
  order=sorted(range(len(boxes)),key=lambda i:(boxes[i,0],boxes[i,1]));items=[]
  for j,i in enumerate(order):
   b=boxes[i];x1,y1,x2,y2=map(float,b);item={'id':j,'x':(x1+x2)/2,'y':(y1+y2)/2,'box':b.tolist(),'confidence':float(confs[i])};items.append(item)
   cv2.rectangle(im,(int(x1),int(y1)),(int(x2),int(y2)),(0,0,255),2);cv2.putText(im,f'{j}:{confs[i]:.2f}',(int(x1)-5,int(y1)-8),cv2.FONT_HERSHEY_SIMPLEX,.5,(0,0,255),1)
  allrows.append({'clip':c,'frame':f,'candidates':items})
  # Full frame preview plus central crop allows independent visual review.
  cv2.imwrite(str(R/f'{c}_{f}_detections.jpg'),im)
  crop=im[260:950,620:1190];tile=Image.fromarray(cv2.cvtColor(crop,cv2.COLOR_BGR2RGB)).resize((285,345));tiles.append((f,tile))
 cols=5;sheet=Image.new('RGB',(cols*285,((len(tiles)+cols-1)//cols)*370),'white');draw=ImageDraw.Draw(sheet)
 for i,(f,tile) in enumerate(tiles):x=(i%cols)*285;y=(i//cols)*370;sheet.paste(tile,(x,y));draw.text((x+5,y+347),f'{c} F{f}',fill='black')
 sheet.save(R/f'{c}_candidate_review.jpg');print(c,'done',flush=True)
 (R/'detections.json').write_text(json.dumps(allrows,indent=2))
