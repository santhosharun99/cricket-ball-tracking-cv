import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from datetime import date

wb = openpyxl.load_workbook('cricket_tracking.xlsx')
FONT = "Arial"
BASE_FONT = Font(name=FONT)
HEADER_FILL = PatternFill("solid", fgColor="305496")
HEADER_FONT = Font(name=FONT, bold=True, color="FFFFFF")

if 'Other_3_Clips_Attempt' in wb.sheetnames:
    del wb['Other_3_Clips_Attempt']
ws = wb.create_sheet('Other_3_Clips_Attempt', 3)

ws['A1'] = "Tried running the ball-detector on the 3 clips we hadn't touched yet - found a real, important limitation"
ws['A1'].font = Font(name=FONT, bold=True)
ws.merge_cells('A1:F1')

ws.append([])
ws.append(["What we found:"])
ws.cell(row=ws.max_row, column=1).font = Font(name=FONT, bold=True)
p0 = [
    "Everything we've built so far (calibration, swing/deviation, bounce_x method) was built around one specific "
    "camera view - the tight 'straight down the pitch from behind the bowler' shot that both C4 and C5 happen to "
    "use. It's a great angle for tracking: the ball travels roughly down the middle of the picture, nice and big.",
    "The 3 remaining clips use completely different camera work. Scanning through them with the ball-detector, "
    "we found: a very wide, full-ground side-on shot (bowler top-left, batsman bottom-right, tiny ball) for one "
    "clip; and for another, a sequence of close-up cutaways, slow-motion replays, and player reaction shots "
    "edited together, with the actual ball only flying clearly into view for a couple of seconds total in the "
    "whole clip - and for the wrong ball in the over at that (we found a replay of an earlier ball in the same "
    "over, not the specific delivery the answer key is asking about).",
]
for s in p0:
    ws.append([s]); ws.cell(row=ws.max_row, column=1).alignment = Alignment(wrap_text=True)
    ws.merge_cells(f'A{ws.max_row}:F{ws.max_row}')

ws.append([])
headers = ["clip", "true bounce_x / kph", "camera style found", "status"]
ws.append(headers)
hdr_row = ws.max_row
rows = [
    ("f81d092b (good length)", "8.177m / 138.58 kph", "wide, full-ground side-on shot - different geometry to C4/C5, needs its own fresh calibration", "found the right delivery's rough location, camera type identified"),
    ("9ef5c0e6 (last ball of the over)", "13.284m / 127.96 kph", "heavily edited highlight package - found the ball clearly for an earlier ball in the same over, not this exact one", "correct delivery not pinned down yet"),
    ("98e537a2 (full-ish length)", "5.286m / 114.18 kph", "wide, full-ground side-on shot, same style as f81d092b", "camera type identified, tracking not yet built"),
]
for r in rows:
    ws.append(r)
for i in range(len(rows)):
    row_i = hdr_row+1+i
    for c in range(1,5):
        ws.cell(row=row_i, column=c).font = BASE_FONT
        ws.cell(row=row_i, column=c).alignment = Alignment(wrap_text=True, vertical="top")
for col_idx, h in enumerate(headers, 1):
    c = ws.cell(row=hdr_row, column=col_idx)
    c.font = HEADER_FONT; c.fill = HEADER_FILL
    c.alignment = Alignment(horizontal="center", wrap_text=True)

ws.append([])
ws.append(["Why this matters more than it might sound:"])
ws.cell(row=ws.max_row, column=1).font = Font(name=FONT, bold=True)
p1 = [
    "This isn't a small bug - it's a real, honest limit on what we've built. Our whole pipeline (camera "
    "calibration, the stump/release/bounce maths, all of it) silently assumes the 'straight down the pitch' "
    "camera. Feed it a different camera angle and none of that maths applies - we'd need to build a fresh "
    "calibration for every different camera style a broadcast uses, and first automatically figure out which "
    "shot is even the right one to look at, out of many cuts in a highlights package.",
    "The real Score Vision subnet will almost certainly throw all sorts of camera angles at us, since it's "
    "pulling from real match footage, not a curated set. So this is worth knowing now rather than being "
    "surprised by it later: our current pipeline is proven on one common angle, not camera-angle-general yet.",
]
for s in p1:
    ws.append([s]); ws.cell(row=ws.max_row, column=1).alignment = Alignment(wrap_text=True)
    ws.merge_cells(f'A{ws.max_row}:F{ws.max_row}')

note = ws.cell(row=ws.max_row+2, column=1,
    value="Bottom line: not giving up on these 3 clips, but being honest that finishing them isn't 'run the same "
          "script again' - it's real new work (a second camera-geometry calibration, and a way to automatically "
          "find the right delivery inside an edited package). Recommending we treat that as its own next project "
          "phase rather than something to rush through, and in the meantime keep our score estimate honestly "
          "labelled as 'proven on 2 of 5 clips, one camera style' rather than implying it generalises yet.")
note.font = Font(name=FONT, italic=True, size=9, color="808080")
note.alignment = Alignment(wrap_text=True)
ws.merge_cells(f'A{note.row}:F{note.row}')
ws.row_dimensions[note.row].height = 90

widths = [26, 20, 45, 30]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w

wb.save('cricket_tracking.xlsx')

ws2 = wb['Notes']
new_notes = [
    (str(date.today()), "Santhosh said okay to try the detector on the 3 example clips we hadn't touched all "
        "session (f81d092b, 9ef5c0e6, 98e537a2). Scanned through all of them with the trained ball-detector "
        "to locate each delivery automatically instead of hunting frame-by-frame by eye."),
    (str(date.today()), "Found something important: C4 and C5 both happen to use the same tight 'straight down "
        "the pitch from behind the bowler' camera, which our whole pipeline (calibration, bounce_x maths, swing) "
        "is built around. These 3 clips use different filming: two are wide, full-ground side-on shots (totally "
        "different geometry, would need a fresh calibration built from scratch); one is a heavily-edited "
        "highlights package where we found the ball clearly for the WRONG ball in the over, not the exact "
        "delivery the answer key asks about - the real one is buried somewhere in a sequence of cutaways and "
        "replays we haven't isolated yet."),
    (str(date.today()), "This isn't a quick fix - each different camera angle effectively needs its own "
        "calibration work, and edited/highlight-style footage needs a way to automatically find the right shot "
        "before we can even start tracking. Logged this honestly as a real scope item for next time rather than "
        "rushing a wrong answer through. Added a new Other_3_Clips_Attempt sheet with the details. Score_Estimate "
        "stays labelled as tested on 2 of 5 clips, not changed by this - we didn't get numbers to add for these "
        "3 yet, just a much clearer picture of what's actually needed to get them."),
]
for row in new_notes:
    ws2.append(row)
for row_i in range(ws2.max_row - len(new_notes) + 1, ws2.max_row + 1):
    ws2.cell(row=row_i, column=1).font = BASE_FONT
    ws2.cell(row=row_i, column=2).font = BASE_FONT
    ws2.cell(row=row_i, column=2).alignment = Alignment(wrap_text=True)
wb.save('cricket_tracking.xlsx')
print('done')
