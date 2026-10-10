import os,json
from pathlib import Path
os.environ['YOLO_CONFIG_DIR']='/tmp/Ultralytics';os.environ['MPLCONFIGDIR']='/tmp/cricket-gap-mpl'
import cv2,torch
from ultralytics import YOLO
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;D=Path('~/Downloads/cricket_project');torch.set_num_threads(4);model=YOLO(str(D/'models/yolo26_ball_detector.pt'));cap=cv2.VideoCapture(str(next((D/'data/videos').glob('9ef5c0e*'))));rows=[];tiles=[]
for f in range(58,87):
 cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,im=cap.read()
 if not ok:raise RuntimeError(f)
 res=model.predict(im,conf=.05,imgsz=1280,device='cpu',verbose=False)[0];boxes=res.boxes.xyxy.cpu().numpy();scores=res.boxes.conf.cpu().numpy();candidates=[]
 for j,i in enumerate(sorted(range(len(boxes)),key=lambda i:(boxes[i,0],boxes[i,1]))):
  b=boxes[i];x1,y1,x2,y2=map(float,b);candidates.append({'id':j,'x':(x1+x2)/2,'y':(y1+y2)/2,'box':b.tolist(),'confidence':float(scores[i])});cv2.rectangle(im,(int(x1),int(y1)),(int(x2),int(y2)),(0,0,255),1);cv2.putText(im,f'{j}:{scores[i]:.2f}',(int(x1),int(y1)-6),cv2.FONT_HERSHEY_SIMPLEX,.4,(0,0,255),1)
 rows.append({'clip':'C2','frame':f,'candidates':candidates});cv2.imwrite(str(R/f'C2_{f}.jpg'),im);tiles.append((f,Image.fromarray(cv2.cvtColor(im[100:640,300:850],cv2.COLOR_BGR2RGB)).resize((275,270))))
(R/'c2_detections.json').write_text(json.dumps(rows,indent=2))
for part in range(2):
 tt=tiles[part*15:(part+1)*15];sheet=Image.new('RGB',(1375,3*295),'white');draw=ImageDraw.Draw(sheet)
 for i,(f,tile) in enumerate(tt):x=i%5*275;y=i//5*295;sheet.paste(tile,(x,y));draw.text((x+5,y+273),f'C2 F{f}',fill='black')
 sheet.save(R/f'C2_review_{part}.jpg')
print('C2 cached:',len(rows),'frames')
