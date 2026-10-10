import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from datetime import date
from openpyxl.utils import get_column_letter

wb = openpyxl.load_workbook('cricket_tracking.xlsx')
ws = wb['Our_Predictions']
# C4 row=5, C5 row=6 ; pred_stump_z is column L, pred_impact_z is column I
ws['I5'] = 0.136   # pred_impact_z for C4, depth-aware
ws['L6'] = 0.358   # pred_stump_z for C5, depth-aware
wb.save('cricket_tracking.xlsx')

# Add a Pitch_Length sheet
if 'Pitch_Length' in wb.sheetnames:
    del wb['Pitch_Length']
ws3 = wb.create_sheet('Pitch_Length')
FONT = "Arial"
HEADER_FILL = PatternFill("solid", fgColor="305496")
HEADER_FONT = Font(name=FONT, bold=True, color="FFFFFF")
BASE_FONT = Font(name=FONT)

headers = ["clip_id", "bounce_x_m (distance in front of batter's stumps)", "length_category", "kph", "source"]
ws3.append(headers)
rows = [
    ("C1", 8.177, "Short of a length", 138.58, "official answer key"),
    ("C2", 13.284, "Short of a length", 127.96, "official answer key"),
    ("C3", 5.286, "Good length", 114.18, "official answer key"),
    ("C4", 2.258, "Full length", 136.69, "official answer key"),
    ("C5", 3.142, "Full length", 138.82, "official answer key"),
]
for r in rows:
    ws3.append(r)

for col_idx, h in enumerate(headers, 1):
    c = ws3.cell(row=1, column=col_idx)
    c.font = HEADER_FONT
    c.fill = HEADER_FILL
    c.alignment = Alignment(horizontal="center", wrap_text=True)
for r in range(2, ws3.max_row+1):
    for c in range(1, len(headers)+1):
        ws3.cell(row=r, column=c).font = BASE_FONT
widths = [8, 40, 20, 8, 22]
for i, w in enumerate(widths, 1):
    ws3.column_dimensions[get_column_letter(i)].width = w
ws3.freeze_panes = "A2"

note = ws3.cell(row=8, column=1, value="Length bands used (as given): Yorker/very full <=2m, Full 2-4m, Good 4-8m, Short >8m, measured "
                                          "as distance the ball pitches in front of the batter's stumps. These bands come from the "
                                          "official answer key's bounce_x for these 5 example clips. Working these out for a brand-new "
                                          "clip (no answer key) still needs us to estimate bounce_x ourselves from the video, which is "
                                          "the next open piece - see Notes.")
note.font = Font(name=FONT, italic=True, size=9, color="808080")
note.alignment = Alignment(wrap_text=True)
ws3.merge_cells('A8:E8')
ws3.row_dimensions[8].height = 60

wb.save('cricket_tracking.xlsx')

ws2 = wb['Notes']
new_notes = [
    (str(date.today()), "Height (Z) fix, per Santhosh's suggestion: the first attempt used the stump ruler for "
                          "height too but treated the ball as if it were right at the stumps' own distance, which "
                          "isn't true for a point still partway down the pitch - so it needs one more step: work out "
                          "roughly how far from the stumps the ball actually is at that moment, and stretch the "
                          "ruler to match THAT distance, not the stumps' distance. We already know exactly where "
                          "ground level is at two distances - right at the stumps (0m) and right at the bounce spot "
                          "(a known distance in front, from the answer key) - so for any point in between, we can "
                          "estimate ground level at the ball's own distance by blending between those two knowns."),
    (str(date.today()), "RESULT: C4's height near the bat improves from 0.012m (clearly too low) to 0.136m against "
                          "a real answer of 0.187m. C5's height near the keeper improves from 0.153m to 0.358m "
                          "against a real answer of 0.292m. Both roughly HALVE the error compared to ignoring the "
                          "ball's own distance from the stumps. Still not as tight as the sideways numbers, mainly "
                          "because we had to guess which exact frame the ball reaches the bat/keeper - a small "
                          "guess there shifts the answer a fair bit. This is real, meaningful progress though, not "
                          "a wrong-in-a-new-way result like before."),
    (str(date.today()), "New Pitch_Length sheet added: sorts all 5 clips into short / good / full / yorker bands "
                          "using the official pitching-distance answer, per Santhosh's exact definitions. C1 and C2 "
                          "are short of a length, C3 is a good length ball, C4 and C5 are full. This currently uses "
                          "the answer key's own distance number - the real test is doing this for a new ball with "
                          "no answer key, which needs us to work out the pitching distance ourselves from the "
                          "video (not yet solved, see above)."),
]
for row in new_notes:
    ws2.append(row)
for row_i in range(ws2.max_row - len(new_notes) + 1, ws2.max_row + 1):
    ws2.cell(row=row_i, column=1).font = BASE_FONT
    ws2.cell(row=row_i, column=2).font = BASE_FONT
    ws2.cell(row=row_i, column=2).alignment = Alignment(wrap_text=True)
wb.save('cricket_tracking.xlsx')
print('done')
