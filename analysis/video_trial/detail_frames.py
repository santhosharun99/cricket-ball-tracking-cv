exec(open('analysis/video_trial/inspect_frames.py').read().split('for name,prefix')[0])
for name,ids,box in [('C1',range(88,94),(650,350,1000,850)),('C3',range(80,86),(650,300,1000,800)),('C4',range(90,96),(650,280,1000,850)),('C5',range(70,76),(680,220,1050,750))]:
 cap=cv2.VideoCapture(str(next(ROOT.glob(clips[name]+'*'))));sheet=Image.new('RGB',(350*6,560),'white');draw=ImageDraw.Draw(sheet)
 for i,f in enumerate(ids):
  cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,im=cap.read();im=Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB)).crop(box);im.thumbnail((350,530));sheet.paste(im,(350*i,0));draw.text((350*i+5,540),f'{name} F{f}',fill='black')
 sheet.save(OUT/f'{name}_release_detail.jpg')
# Scan full clip scoreboard at half-second intervals after initial delivery.
for name,prefix in clips.items():
 cap=cv2.VideoCapture(str(next(ROOT.glob(prefix+'*'))));fps=cap.get(5);n=int(cap.get(7));ids=list(range(int(4.5*fps),min(n,int(18*fps)),int(fps/2)));sheet=Image.new('RGB',(960,130*len(ids)),'white');draw=ImageDraw.Draw(sheet)
 for i,f in enumerate(ids):
  cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,im=cap.read()
  if not ok: continue
  H,W=im.shape[:2];crop=Image.fromarray(cv2.cvtColor(im[int(.84*H):],cv2.COLOR_BGR2RGB));crop.thumbnail((960,105));sheet.paste(crop,(0,i*130));draw.text((5,i*130+108),f'{name} F{f} {f/fps:.2f}s',fill='black')
 sheet.save(OUT/f'{name}_score_scan.jpg')
