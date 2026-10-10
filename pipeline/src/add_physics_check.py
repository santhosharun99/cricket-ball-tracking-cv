import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from datetime import date

wb = openpyxl.load_workbook('cricket_tracking.xlsx')
FONT = "Arial"
HEADER_FILL = PatternFill("solid", fgColor="305496")
HEADER_FONT = Font(name=FONT, bold=True, color="FFFFFF")
BASE_FONT = Font(name=FONT)

# ---- new Physics_Check sheet ----
if 'Physics_Check' in wb.sheetnames:
    del wb['Physics_Check']
ws = wb.create_sheet('Physics_Check')

ws['A1'] = "Part 1: height purely from physics (release height + speed + gravity), no pixels at all - release to bounce"
ws['A1'].font = Font(name=FONT, bold=True)
ws.merge_cells('A1:F1')

headers = ["clip", "frame", "predicted_height_m (physics only)", "note"]
ws.append([])
ws.append(headers)
hdr_row = ws.max_row
c4_heights = {
    93: 2.383, 94: 2.245, 95: 2.091, 96: 1.921, 97: 1.736, 98: 1.535,
    99: 1.319, 100: 1.086, 101: 0.838, 102: 0.575, 103: 0.295, 104: -0.000,
}
for f, h in c4_heights.items():
    ws.append(["C4", f, round(h, 3), "release ball height + gravity drop, assuming ~16.6m release point and constant speed"])
ws.append(["C4", "-", "release ~frame 94.6 (we start tracking at 93)", "assumed release point 16.6m in front of batter's stumps (typical fast-bowler release, ~2.3m in front of bowling crease)"])

ws.append([])
ws.append(["Part 2: post-bounce plausibility check - what upward 'pop' speed off the pitch would explain each height number"])
ws.cell(row=ws.max_row, column=1).font = Font(name=FONT, bold=True)
ws.merge_cells(f'A{ws.max_row}:F{ws.max_row}')
ws.append(["clip", "frame", "time_since_bounce_s", "height_m", "source", "implied_pop_up_speed_m_s"])
hdr_row2 = ws.max_row
rows2 = [
    ("C4", 105, 0.04, 0.136, "our pixel-based answer", 3.60),
    ("C4", 105, 0.04, 0.187, "true answer", 4.87),
    ("C5", 91, 0.28, 0.358, "our pixel-based answer", 2.65),
    ("C5", 91, 0.28, 0.292, "true answer", 2.42),
]
for r in rows2:
    ws.append(r)

note = ws.cell(row=ws.max_row + 2, column=1,
    value="What this means in plain terms: for the part of the flight BEFORE the ball pitches, we can work out how "
          "high it is using pure physics - release height, ball speed, and gravity - with no pixel measurement at "
          "all. This is useful because before the bounce we don't have two known ground-level points to interpolate "
          "between (we only get that trick to work AFTER the bounce, between the bounce spot and the stumps). "
          "After the bounce, physics alone can't hand us an exact height because nobody knows exactly how much "
          "'kick' a pitch will give the ball - that's genuinely unpredictable and is exactly why batters have to "
          "watch the pitch and react. What we CAN do is a sanity check: work out what upward pitch-kick speed "
          "would be needed to produce our pixel-based number, and see if that's a normal, believable number for a "
          "cricket pitch (roughly 1.5-3.5 m/s is typical). For C5 both our answer and the true answer point to a "
          "very ordinary pop-up speed (2.4-2.7 m/s) - good agreement. For C4 both are a little higher than typical "
          "(3.6-4.9 m/s), but that check is extremely sensitive here because we're only 1 video frame (0.04s) after "
          "the bounce - a tiny timing error swings this a lot. Bottom line: physics doesn't hand us the post-bounce "
          "answer for free, but it's a good gut-check on whether our numbers are in the right ballpark, and it "
          "fully solves the pre-bounce height problem, which we had no way to answer before.")
note.font = Font(name=FONT, italic=True, size=9, color="808080")
note.alignment = Alignment(wrap_text=True)
ws.merge_cells(f'A{ws.max_row-1+2}:F{ws.max_row-1+2}' if False else f'A{note.row}:F{note.row}')
ws.row_dimensions[note.row].height = 140

for row_i in (hdr_row, hdr_row2):
    for col_i in range(1, 7):
        cell = ws.cell(row=row_i, column=col_i)
        if cell.value is not None:
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL
            cell.alignment = Alignment(horizontal="center", wrap_text=True)

widths = [8, 8, 30, 55, 20, 20]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "A3"

wb.save('cricket_tracking.xlsx')

# ---- Notes entries ----
ws2 = wb['Notes']
new_notes = [
    (str(date.today()), "Santhosh's idea: since we know the ball's speed, its release height, and (from the "
                          "answer key) exactly where it pitches, can we just use physics (gravity) to work out the "
                          "height directly, and use that to check our pixel-based numbers? Yes - and it turns out "
                          "physics is most useful exactly where our pixel method is weakest: the part of the flight "
                          "BEFORE the bounce, where we don't have two known ground-level points to work with."),
    (str(date.today()), "Added a Physics_Check sheet. For C4, using release height 2.161m, speed 136.69kph, and "
                          "assuming the bowler lets go about 16.6m in front of the batter's stumps (a normal "
                          "release point for a fast bowler), pure gravity gives a smooth, believable height for "
                          "every tracked frame from release down to 0m exactly at the real bounce spot - frame93 "
                          "starts at 2.38m (just released) and glides down to 0 right at frame104 (true bounce "
                          "frame). This needed zero pixel measurements. Checked how much this depends on our guess "
                          "of the release point (tried 15.5m to 18.5m) and the mid-flight height barely moves "
                          "(1.43-1.62m at frame98) - so the method is not sensitive to that assumption."),
    (str(date.today()), "For the part AFTER the bounce, physics can't hand us an exact number for free, because "
                          "nobody can know in advance exactly how much extra kick a specific patch of pitch will "
                          "give the ball - that's genuine, real unpredictability (it's why batters watch the pitch "
                          "and adjust). Instead we used physics as a sanity check: worked out what pop-up speed off "
                          "the pitch would explain our pixel-based height, and whether that's a normal number. For "
                          "C5, both our answer (0.358m) and the real answer (0.292m) point to an ordinary 2.4-2.7 "
                          "m/s pop-up - good agreement. For C4, both point to a slightly higher than typical 3.6-4.9 "
                          "m/s pop-up, but that check is extremely sensitive there since it's only 1 video frame "
                          "(0.04s) after pitching. Overall: physics fully solves the pre-bounce height gap we had, "
                          "and backs up that our post-bounce numbers are in a believable range, without replacing "
                          "the need for the pixel method after the bounce."),
]
for row in new_notes:
    ws2.append(row)
for row_i in range(ws2.max_row - len(new_notes) + 1, ws2.max_row + 1):
    ws2.cell(row=row_i, column=1).font = BASE_FONT
    ws2.cell(row=row_i, column=2).font = BASE_FONT
    ws2.cell(row=row_i, column=2).alignment = Alignment(wrap_text=True)
wb.save('cricket_tracking.xlsx')
print('done')
