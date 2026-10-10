import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from datetime import date

wb = openpyxl.load_workbook('cricket_tracking.xlsx')
FONT = "Arial"
BASE_FONT = Font(name=FONT)
HEADER_FILL = PatternFill("solid", fgColor="305496")
HEADER_FONT = Font(name=FONT, bold=True, color="FFFFFF")
GREEN = PatternFill("solid", fgColor="C6EFCE")
YELLOW = PatternFill("solid", fgColor="FFEB9C")
RED = PatternFill("solid", fgColor="FFC7CE")

if 'Dense_Tracking_Swing' in wb.sheetnames:
    del wb['Dense_Tracking_Swing']
ws = wb.create_sheet('Dense_Tracking_Swing', 3)

ws['A1'] = "Second attempt at swing_angle/deviation - now using the trained ball-detector's frame-by-frame tracking instead of just 2 points"
ws['A1'].font = Font(name=FONT, bold=True)
ws.merge_cells('A1:F1')

ws.append([])
ws.append(["What changed since the last attempt:"])
ws.cell(row=ws.max_row, column=1).font = Font(name=FONT, bold=True)
p0 = [
    "Last time (see Swing_Deviation_Attempt sheet) we only had 2 points to work with - where the ball is released, "
    "and where it bounces - so all we could draw was one straight line between them. That line shows the AVERAGE "
    "direction the ball travelled, not which way it was actually pointing right at the moment it bounced.",
    "Now that we have a trained ball-detector, we can see the ball in almost every single frame between release "
    "and bounce (10-12 frames, not just 2). That means instead of one long straight line, we can look at just the "
    "last few frames right before the bounce and draw a much shorter line - this shows the ball's real direction "
    "right at the moment it lands, not the average over the whole flight.",
]
for s in p0:
    ws.append([s]); ws.cell(row=ws.max_row, column=1).alignment = Alignment(wrap_text=True)
    ws.merge_cells(f'A{ws.max_row}:F{ws.max_row}')

ws.append([])
ws.append(["SWING_ANGLE - comparing direction near release vs direction near the bounce:"])
ws.cell(row=ws.max_row, column=1).font = Font(name=FONT, bold=True)
headers = ["clip", "old method (1 line, whole flight)", "new method (direction near release vs near bounce)", "true value", "verdict"]
ws.append(headers)
hdr_row = ws.max_row
rows = [
    ("C4", "+0.72°", "+0.02°", "-0.16°", "much closer to zero than before, but still wrong sign - true swing here is smaller than our measurement noise"),
    ("C5", "+0.97°", "-0.03°", "0.00°", "big improvement - correctly reads as basically no swing, matching this ball which really did fly dead straight"),
]
for r in rows:
    ws.append(r)
for i in range(len(rows)):
    row_i = hdr_row+1+i
    for c in range(1,6):
        ws.cell(row=row_i, column=c).font = BASE_FONT
        ws.cell(row=row_i, column=c).alignment = Alignment(wrap_text=True, vertical="top")
for col_idx, h in enumerate(headers, 1):
    c = ws.cell(row=hdr_row, column=col_idx)
    c.font = HEADER_FONT; c.fill = HEADER_FILL
    c.alignment = Alignment(horizontal="center", wrap_text=True)

ws.append([])
p1 = [
    "Honest read: the new method is clearly better - it no longer cries 'big swing!' on a ball that flew perfectly "
    "straight (C5), which the old method did. But on the one ball that genuinely swings (C4), we still can't "
    "recover the right number. The real swing on C4 is tiny (-0.16 degrees) over a 15-16 metre flight - that's a "
    "sideways bend of only about 4-5 centimetres, total, over the whole distance. Our pixel-reading and camera "
    "calibration have some natural wobble that's roughly the same size as that 4-5cm bend, so the true signal gets "
    "buried in our own measurement noise. It's not that the method is wrong - it's that we'd need sharper "
    "measurements (better calibration points, more decimal places of pixel precision) to reliably see a curve "
    "this small.",
]
for s in p1:
    ws.append([s]); ws.cell(row=ws.max_row, column=1).alignment = Alignment(wrap_text=True)
    ws.merge_cells(f'A{ws.max_row}:F{ws.max_row}')

ws.append([])
ws.append(["DEVIATION - tried to extend the same idea to after the bounce, and it backfired:"])
ws.cell(row=ws.max_row, column=1).font = Font(name=FONT, bold=True)
p2 = [
    "Tried the same trick for deviation: track the ball for a few frames AFTER the bounce too, and compare that "
    "direction to the direction just before the bounce. Problem: to convert those after-bounce frames into a "
    "real sideways distance, we need to know how far forward (towards the batsman) the ball has travelled each "
    "frame - and the only number we have for the ball's after-bounce speed is the 'how much speed does it keep "
    "after hitting the pitch' estimate from the Speed_Method sheet, which we already flagged as unreliable (47% "
    "on one ball, 28% on the other - not consistent).",
    "Result of actually trying it: for C5, this gave a deviation of about -4 degrees, when the true answer is "
    "0.04 degrees - roughly 100 times too big. Using a shaky number to build another number just multiplies the "
    "error. This approach for deviation does not work and we are not using it.",
    "What we ARE keeping for deviation: the simpler method from the last attempt (a straight line from bounce to "
    "the stumps/bat, compared against the straight line from release to bounce). It doesn't need any guess about "
    "after-bounce speed at all - it just uses the bounce point and the final stump point, both of which we "
    "already know. That one actually worked well on the straight ball (0.037 vs true 0.04) and poorly on the "
    "swinging ball (-0.28 vs true 0.45, same root cause as swing_angle above - the true bend is too small to see "
    "over the noise). So: no change to deviation from the last attempt; the new tracking data only ended up "
    "helping swing_angle, not deviation.",
]
for s in p2:
    ws.append([s]); ws.cell(row=ws.max_row, column=1).alignment = Alignment(wrap_text=True)
    ws.merge_cells(f'A{ws.max_row}:F{ws.max_row}')

note = ws.cell(row=ws.max_row+2, column=1,
    value="Bottom line: the new ball-tracking model is a genuine step up for swing_angle - it now correctly tells "
          "a straight ball from a swinging one instead of guessing 'swing' on everything, even though it still "
          "can't measure a small real swing precisely on broadcast-quality video. Deviation is unchanged - our "
          "attempt to improve it using the same dense-tracking idea made things worse, not better, so we're "
          "keeping the older, simpler bounce-to-stumps method for that field instead.")
note.font = Font(name=FONT, italic=True, size=9, color="808080")
note.alignment = Alignment(wrap_text=True)
ws.merge_cells(f'A{note.row}:F{note.row}')
ws.row_dimensions[note.row].height = 90

widths = [10, 30, 40, 12, 45]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w

wb.save('cricket_tracking.xlsx')

ws2 = wb['Notes']
new_notes = [
    (str(date.today()), "Santhosh said to go ahead and use the newly trained ball-detector's frame-by-frame "
        "tracking to properly compute swing_angle and deviation, now that we can see the ball in nearly every "
        "frame instead of just 2 points. Built a 3-point camera calibration for each clip (stump base, release "
        "point, bounce point) to convert the tracked pixels into real sideways-distance numbers, then compared "
        "the ball's direction near release against its direction right near the bounce (instead of one straight "
        "line for the whole flight)."),
    (str(date.today()), "Result for swing_angle: big improvement on the straight ball (C5: -0.03 vs true 0.00, "
        "was +0.97 with the old 2-point method) and a smaller error on the swinging ball (C4: +0.02 vs true "
        "-0.16, was +0.72 with the old method) - still wrong sign on C4 because the true swing there is only a "
        "4-5cm bend over 15m, which is about the same size as our own measurement noise. Genuinely better, not "
        "yet reliable for a real swinging delivery."),
    (str(date.today()), "Tried extending the same dense-tracking idea to deviation (using frames after the "
        "bounce too) - it backfired badly (C5 came out as -4 degrees vs true 0.04) because it needed the shaky "
        "'post-bounce speed retention' number from the Speed_Method sheet to work out depth per frame, and that "
        "number was already known to be unreliable. Dropped this approach for deviation and kept the older, "
        "simpler bounce-to-stumps line method instead, which still works about as well as before."),
]
for row in new_notes:
    ws2.append(row)
for row_i in range(ws2.max_row - len(new_notes) + 1, ws2.max_row + 1):
    ws2.cell(row=row_i, column=1).font = BASE_FONT
    ws2.cell(row=row_i, column=2).font = BASE_FONT
    ws2.cell(row=row_i, column=2).alignment = Alignment(wrap_text=True)
wb.save('cricket_tracking.xlsx')
print('done')
