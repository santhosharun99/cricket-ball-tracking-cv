exec(open('analysis/video_trial/inspect_frames.py').read().split('for name,prefix')[0])
for name,ids,box in [('C1',range(96,101),(750,450,1100,800)),('C3',range(93,98),(720,500,1100,880)),('C4',range(102,107),(700,570,1100,970)),('C5',range(82,87),(770,420,1150,800))]:
 cap=cv2.VideoCapture(str(next(ROOT.glob(clips[name]+'*'))));sheet=Image.new('RGB',(400*5,430),'white');draw=ImageDraw.Draw(sheet)
 for i,f in enumerate(ids):
  cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,im=cap.read();im=Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB)).crop(box);im.thumbnail((400,400));sheet.paste(im,(400*i,0));draw.text((400*i+5,410),f'{name} F{f}',fill='black')
 sheet.save(OUT/f'{name}_bounce_detail.jpg')
cap=cv2.VideoCapture(str(next(ROOT.glob(clips['C3']+'*'))));ids=list(range(450,1295,25));sheet=Image.new('RGB',(960,130*len(ids)),'white');draw=ImageDraw.Draw(sheet)
for i,f in enumerate(ids):
 cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,im=cap.read()
 if ok:
  crop=Image.fromarray(cv2.cvtColor(im[900:],cv2.COLOR_BGR2RGB));crop.thumbnail((960,105));sheet.paste(crop,(0,i*130));draw.text((5,i*130+108),f'C3 F{f} {f/25}s',fill='black')
sheet.save(OUT/'C3_late_score.jpg')
for name,f in [('C1',340),('C4',390),('C5',260)]:
 cap=cv2.VideoCapture(str(next(ROOT.glob(clips[name]+'*'))));cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,im=cap.read();cv2.imwrite(str(OUT/f'{name}_speed_evidence.jpg'),im[920:1080,1300:1800])
