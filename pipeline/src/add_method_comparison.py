import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from datetime import date

wb = openpyxl.load_workbook('cricket_tracking.xlsx')
FONT = "Arial"
HEADER_FILL = PatternFill("solid", fgColor="305496")
HEADER_FONT = Font(name=FONT, bold=True, color="FFFFFF")
BASE_FONT = Font(name=FONT)

if 'Method_Comparison' in wb.sheetnames:
    del wb['Method_Comparison']
ws = wb.create_sheet('Method_Comparison')

ws['A1'] = "Our ruler (fixed stump height) vs the paper's ruler (batsman's own height) - same math, only the ruler swapped"
ws['A1'].font = Font(name=FONT, bold=True)
ws.merge_cells('A1:G1')

headers = ["clip", "frame", "what it measures", "true answer (m)", "our stump-ruler result (m)",
           "batsman-ruler result (m)", "stump error / batsman error"]
ws.append([])
ws.append(headers)
hdr_row = ws.max_row
rows = [
    ("C4", 104, "sideways position where it pitches", -0.360, -0.393, -0.419, "3.3cm / 5.9cm"),
    ("C4", 105, "sideways position just before the bat", -0.335, -0.343, -0.367, "0.8cm / 3.2cm"),
    ("C5", 84, "sideways position where it pitches (anchor frame - both methods start equal here)", -0.330, -0.308, -0.308, "2.2cm / 2.2cm"),
    ("C5", 85, "sideways position right after it pitches", -0.279, -0.276, -0.270, "0.3cm / 0.9cm"),
]
for r in rows:
    ws.append(r)

note = ws.cell(row=ws.max_row+2, column=1,
    value="What we tested: Santhosh downloaded the dataset behind the IEEE paper we looked at earlier, and asked "
          "us to actually try the paper's method side by side with ours rather than just talk about it. Their "
          "dataset itself only ships annotation files pointing at specific YouTube frames, not the video frames or "
          "a ready-to-run trained model, so we couldn't run their exact model on our 5 clips. What we COULD do "
          "fairly: copy their core idea - track something of a known size to work out how much the camera has "
          "zoomed in - but swap in their choice of ruler (the batsman's own height, tracked automatically with an "
          "off-the-shelf person detector) in place of ours (the stumps, which we measure by hand), with everything "
          "else in the calculation left exactly the same, and see which one lands closer to the real answer.")
note.font = Font(name=FONT, italic=True, size=9, color="808080")
note.alignment = Alignment(wrap_text=True)
ws.merge_cells(f'A{note.row}:G{note.row}')
ws.row_dimensions[note.row].height = 100

note2 = ws.cell(row=note.row+1, column=1,
    value="Result: our stump ruler wins in every case, and the gap gets bigger the further the frame is from where "
          "we last checked the ruler (C4's checks are 11-12 frames from the anchor point and the batsman-ruler "
          "error roughly doubles; C5's checks are only 1 frame away and the two methods are nearly tied). This "
          "makes sense - the stumps are a fixed size by law, so once we've measured them carefully they don't "
          "wobble, but a batsman shifts stance, crouches, and lifts the bat as the ball arrives, and an automatic "
          "person-detector box jitters frame to frame - all of that noise feeds straight into the ruler and drifts "
          "further off the more frames you extrapolate across. The paper's choice isn't wrong for their situation: "
          "a fully automatic pipeline processing thousands of deliveries can't hand-measure stumps in every frame, "
          "and the batsman usually stays visible for longer since the stumps get hidden behind his own body as the "
          "camera zooms in. But for us, since we're measuring by hand anyway, sticking with the stumps was the "
          "right call.")
note2.font = Font(name=FONT, italic=True, size=9, color="808080")
note2.alignment = Alignment(wrap_text=True)
ws.merge_cells(f'A{note2.row}:G{note2.row}')
ws.row_dimensions[note2.row].height = 120

for col_idx, h in enumerate(headers, 1):
    c = ws.cell(row=hdr_row, column=col_idx)
    c.font = HEADER_FONT
    c.fill = HEADER_FILL
    c.alignment = Alignment(horizontal="center", wrap_text=True)
for r in range(hdr_row+1, hdr_row+1+len(rows)):
    for c in range(1, len(headers)+1):
        ws.cell(row=r, column=c).font = BASE_FONT
        ws.cell(row=r, column=c).alignment = Alignment(wrap_text=True, vertical="top")

widths = [8, 8, 42, 15, 20, 20, 22]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "A3"

wb.save('cricket_tracking.xlsx')

ws2 = wb['Notes']
new_notes = [
    (str(date.today()), "Santhosh downloaded the actual dataset behind the IEEE paper and asked us to try the "
                          "paper's method head to head with ours rather than just discuss it on paper. Reality "
                          "check first: their public download only has annotation files pointing at specific "
                          "YouTube frames, not the actual images and not a ready trained model - so we couldn't "
                          "literally run their model on our 5 clips. Instead we did the fair version: their core "
                          "idea is 'track something of known size to measure how zoomed-in the camera is'; we "
                          "swapped their ruler choice (the batsman's own height, tracked with an off-the-shelf "
                          "person detector) into our own pipeline in place of the stumps, changed nothing else, "
                          "and compared the two side by side on C4 and C5, added as a new Method_Comparison sheet."),
    (str(date.today()), "RESULT: our stump ruler beat the batsman ruler in every check we ran, and the gap widens "
                          "the further you are from the last careful measurement - on C4 (checking 11-12 frames "
                          "later) the batsman-ruler error was roughly double ours (5.9cm vs 3.3cm at the pitch "
                          "point, 3.2cm vs 0.8cm near the bat); on C5 (checking just 1 frame later) they were "
                          "almost tied. Makes sense: the stumps are a fixed, law-defined size that never wobbles "
                          "once measured, while a batsman shifts stance and lifts the bat as the ball arrives, and "
                          "an automatic body-detector box jitters a bit frame to frame - that noise compounds the "
                          "more frames you stretch it across. Their choice still makes sense for THEM though - a "
                          "fully automated pipeline running on thousands of deliveries can't hand-measure the "
                          "stumps every time, and the batsman usually stays in view longer since the stumps "
                          "themselves get hidden behind his body as the camera zooms in. For us, since we're "
                          "measuring things by hand anyway, sticking with the stumps was the right call."),
]
for row in new_notes:
    ws2.append(row)
for row_i in range(ws2.max_row - len(new_notes) + 1, ws2.max_row + 1):
    ws2.cell(row=row_i, column=1).font = BASE_FONT
    ws2.cell(row=row_i, column=2).font = BASE_FONT
    ws2.cell(row=row_i, column=2).alignment = Alignment(wrap_text=True)
wb.save('cricket_tracking.xlsx')
print('done')
