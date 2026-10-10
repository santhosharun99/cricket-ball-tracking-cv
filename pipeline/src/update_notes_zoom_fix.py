import openpyxl
from openpyxl.styles import Font, Alignment
from datetime import date

wb = openpyxl.load_workbook('cricket_tracking.xlsx')
ws2 = wb['Notes']
BASE_FONT = Font(name='Arial')
new_notes = [
    (str(date.today()), "BREAKTHROUGH (Santhosh's idea): re-checked whether the camera actually stays still "
                          "during the run-up. It does not - the broadcast camera zooms in steadily and continuously "
                          "as the bowler runs in (confirmed by measuring the stumps' size across many frames: they "
                          "grow from ~73px tall at the start of the run-up to ~165px tall by the time the ball "
                          "reaches the bat). We had been using ONE stump measurement (from before the run-up even "
                          "started) as the ruler for the whole delivery - that ruler was only correct for that one "
                          "moment, and wrong (too small) by the time the ball is actually in the air, which is "
                          "exactly why the bounce point came out so wildly off before."),
    (str(date.today()), "FIX: measured the stumps' size and position at each frame across the actual ball flight "
                          "(93-103, wherever any part of the stumps peeks out from behind the batter), fit a smooth "
                          "line through those measurements (the zoom rate is steady, about +5.6 pixels of stump "
                          "height per frame), and used the correct ruler for each individual frame instead of one "
                          "ruler for the whole delivery."),
    (str(date.today()), "RESULT: with the corrected, per-frame ruler, C4's bounce point comes out at -0.393m "
                          "sideways from off the stump line - the real answer is -0.36m. That is only 3.3cm off, "
                          "down from being off by over 2 metres before. The ball's position just before reaching "
                          "the bat comes out at -0.343m, versus the real impact_y of -0.335m - also within a few "
                          "centimetres. This is a genuine fix, not a lucky guess - the whole tracked path from "
                          "release to bounce now moves smoothly and believably (starts wide at -0.65m, drifts in "
                          "toward -0.34/-0.39m as it nears the stumps), which is what a real swinging/seaming "
                          "delivery should look like."),
    (str(date.today()), "Next: check whether C5's camera also zooms during its delivery (the earlier locked-off "
                          "check may have missed a slow zoom the same way it did for C4) and redo C5's numbers "
                          "with the same fix if so. Then see if this same fix also rescues the height (stump_z) "
                          "number, which was the other one that came out impossible earlier."),
]
for row in new_notes:
    ws2.append(row)
for row_i in range(ws2.max_row - len(new_notes) + 1, ws2.max_row + 1):
    ws2.cell(row=row_i, column=1).font = BASE_FONT
    ws2.cell(row=row_i, column=2).font = BASE_FONT
    ws2.cell(row=row_i, column=2).alignment = Alignment(wrap_text=True)
wb.save('cricket_tracking.xlsx')
print('saved, notes rows now', ws2.max_row)
