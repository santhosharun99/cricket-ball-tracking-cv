import cv2
from PIL import Image,ImageDraw
from pathlib import Path
ROOT=Path('pipeline/data/videos')
OUT=Path(__file__).resolve().parent
clips={'C1':'f81d092','C2':'9ef5c0e','C3':'98e537','C4':'6a79','C5':'bad153'}
for name,prefix in clips.items():
 path=next(ROOT.glob(prefix+'*'));cap=cv2.VideoCapture(str(path));fps=cap.get(5)
 ids=list(range(int(2.6*fps),int(4.3*fps)+1,2)) if name not in ['C5','C2'] else list(range(int((2.5 if name=='C5' else 1)*fps),int((3.7 if name=='C5' else 4)*fps)+1,2))
 cols=5;w=384;h=238;sheet=Image.new('RGB',(cols*w,((len(ids)+cols-1)//cols)*h),'white');draw=ImageDraw.Draw(sheet)
 for i,f in enumerate(ids):
  cap.set(0 if False else cv2.CAP_PROP_POS_FRAMES,f);ok,im=cap.read()
  if not ok:continue
  im=cv2.cvtColor(im,cv2.COLOR_BGR2RGB);tile=Image.fromarray(im).resize((384,216));x=(i%cols)*w;y=(i//cols)*h;sheet.paste(tile,(x,y));draw.text((x+5,y+218),f'{name} frame {f} / {f/fps:.3f}s',fill='black')
 sheet.save(OUT/f'{name}_events.jpg');cap.release()
