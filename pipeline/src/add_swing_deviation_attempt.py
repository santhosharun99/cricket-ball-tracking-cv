import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from datetime import date

wb = openpyxl.load_workbook('cricket_tracking.xlsx')
FONT = "Arial"
BASE_FONT = Font(name=FONT)
HEADER_FILL = PatternFill("solid", fgColor="305496")
HEADER_FONT = Font(name=FONT, bold=True, color="FFFFFF")

if 'Swing_Deviation_Attempt' in wb.sheetnames:
    del wb['Swing_Deviation_Attempt']
ws = wb.create_sheet('Swing_Deviation_Attempt', 3)

ws['A1'] = "First attempt at swing_angle + deviation - correcting an earlier over-claim that these were 'free points'"
ws['A1'].font = Font(name=FONT, bold=True)
ws.merge_cells('A1:F1')

ws.append([])
ws.append(["What we said before vs what actually happened:"])
ws.cell(row=ws.max_row, column=1).font = Font(name=FONT, bold=True)
p0 = [
    "Earlier we said swing_angle and deviation were basically free - that we already had every number the formula "
    "needs (release point, bounce point, stump/impact point). Actually tried it now, and that was wrong. The "
    "simple version of the calc only works for a ball that flies dead straight - it breaks for a ball that "
    "actually swings, which is exactly the case we care about most. Owning that up front rather than quietly "
    "dropping the earlier claim.",
]
for s in p0:
    ws.append([s]); ws.cell(row=ws.max_row, column=1).alignment = Alignment(wrap_text=True)
    ws.merge_cells(f'A{ws.max_row}:F{ws.max_row}')

ws.append([])
ws.append(["The simple version we tried:"])
ws.cell(row=ws.max_row, column=1).font = Font(name=FONT, bold=True)
p1 = [
    "swing_angle = the sideways angle of a straight line from where the ball is released to where it bounces.",
    "deviation = that same pre-bounce angle, compared against the angle of a straight line from the bounce to "
    "where it reaches the bat (or the stumps, if it isn't hit) - i.e. how much the line bends at the bounce.",
]
for s in p1:
    ws.append([s]); ws.cell(row=ws.max_row, column=1).alignment = Alignment(wrap_text=True)
    ws.merge_cells(f'A{ws.max_row}:F{ws.max_row}')

ws.append([])
headers = ["clip", "field", "our attempt", "true value", "verdict"]
ws.append(headers)
hdr_row = ws.max_row
rows = [
    ("C4", "swing_angle", "+0.72°", "-0.16°", "wrong - wrong sign, wrong size"),
    ("C4", "deviation", "-0.28°", "+0.45°", "wrong - wrong sign, wrong size"),
    ("C5", "swing_angle", "+0.97°", "0.00°", "wrong - this ball flew dead straight, ours says it swung a lot"),
    ("C5", "deviation", "+0.037°", "+0.04°", "spot on - almost exact"),
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
ws.append(["Why it worked on one ball but not the other - and what it actually tells us:"])
ws.cell(row=ws.max_row, column=1).font = Font(name=FONT, bold=True)
p2 = [
    "Ball 5 truly does fly dead straight (true swing = 0.00) - so a straight line from release to bounce IS the "
    "real path, and our calc nailed the deviation almost exactly (0.037 vs 0.04).",
    "Ball 4 genuinely swings in the air (true swing = -0.16, a real curve). For a ball that curves, a straight "
    "line drawn between just its start point and its end point does NOT show which way it was pointing right "
    "before it hit the pitch - it only shows the average direction over the whole trip. That's the wrong thing to "
    "compare against. It's like judging which way a car was steering at the finish line using only its start and "
    "finish coordinates, ignoring the bend in the road.",
    "So the real fix isn't a smarter formula - it's tracking one or two extra points: the ball's position a couple "
    "of frames BEFORE it bounces (to get the direction it's actually travelling right at the moment of landing), "
    "and ideally a point shortly after release too (to get the direction it was actually launched in, before any "
    "swing has had time to act). We currently only track the two endpoints (release and bounce), which is enough "
    "for bounce_x and bounce_y but not enough for swing and deviation on a ball that curves.",
]
for s in p2:
    ws.append([s]); ws.cell(row=ws.max_row, column=1).alignment = Alignment(wrap_text=True)
    ws.merge_cells(f'A{ws.max_row}:F{ws.max_row}')

note = ws.cell(row=ws.max_row+2, column=1,
    value="Bottom line: swing_angle and deviation are NOT free points after all - correcting the earlier claim. "
          "They need at least one more tracked frame near the bounce (and ideally one near release) to capture "
          "the ball's real direction at those moments, not just its two endpoint positions. Real next step: add "
          "one or two extra frame-reads to our tracking process (a couple of frames before the bounce is the "
          "priority, since deviation only needs that one), then redo this calc.")
note.font = Font(name=FONT, italic=True, size=9, color="808080")
note.alignment = Alignment(wrap_text=True)
ws.merge_cells(f'A{note.row}:F{note.row}')
ws.row_dimensions[note.row].height = 90

widths = [10, 14, 16, 14, 40]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w

wb.save('cricket_tracking.xlsx')

ws2 = wb['Notes']
new_notes = [
    (str(date.today()), "Santhosh said to actually try building swing_angle and deviation, since we'd called them "
                          "'free points' earlier. Correction: they're not free. Built the simple version (straight "
                          "line release->bounce for swing, and the bend in that line at the bounce for deviation) "
                          "and tested against both known balls. Deviation nailed C5 almost exactly (0.037 vs true "
                          "0.04) - but that ball happens to fly dead straight (true swing=0), which is the one case "
                          "where the simple straight-line approach is actually correct. On C4, which genuinely "
                          "swings in the air, both swing_angle and deviation came out wrong (wrong sign and size)."),
    (str(date.today()), "Root cause: a ball that swings curves through the air, so a straight line drawn only "
                          "between its release point and bounce point doesn't show which way it was actually "
                          "pointing right before landing - it only shows the average direction, and the curve gets "
                          "washed out. Fix isn't a better formula, it's tracking 1-2 more points: the ball's spot a "
                          "couple of frames before it bounces (most important, needed for deviation), and ideally "
                          "one soon after release too (needed for a proper swing_angle). Logged as the real next "
                          "step in a new Swing_Deviation_Attempt sheet - being upfront that the earlier 'free "
                          "points' framing was wrong rather than quietly moving past it."),
]
for row in new_notes:
    ws2.append(row)
for row_i in range(ws2.max_row - len(new_notes) + 1, ws2.max_row + 1):
    ws2.cell(row=row_i, column=1).font = BASE_FONT
    ws2.cell(row=row_i, column=2).font = BASE_FONT
    ws2.cell(row=row_i, column=2).alignment = Alignment(wrap_text=True)
wb.save('cricket_tracking.xlsx')
print('done')
