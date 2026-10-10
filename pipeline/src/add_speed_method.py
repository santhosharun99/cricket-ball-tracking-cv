import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from datetime import date

wb = openpyxl.load_workbook('cricket_tracking.xlsx')
FONT = "Arial"
BASE_FONT = Font(name=FONT)
HEADER_FILL = PatternFill("solid", fgColor="305496")
HEADER_FONT = Font(name=FONT, bold=True, color="FFFFFF")

if 'Speed_Method' in wb.sheetnames:
    del wb['Speed_Method']
ws = wb.create_sheet('Speed_Method', 3)

ws['A1'] = "Working out our OWN bowling speed (not from the on-screen speed-gun) - what we tried, what works, what doesn't"
ws['A1'].font = Font(name=FONT, bold=True)
ws.merge_cells('A1:F1')

ws.append([])
ws.append(["Problem with our old method:"])
ws.cell(row=ws.max_row, column=1).font = Font(name=FONT, bold=True)
p1 = [
    "Old method = total distance (18.9m, release to bat) divided by total time (release frame to bat-contact frame).",
    "This blends together TWO very different speeds: the fast pre-bounce flight, and the slower post-bounce hop "
    "(the ball loses a big chunk of speed hitting the pitch - that's just physics, not a tracking error).",
    "The more of the total TIME that happens after the bounce, the worse this drags the average down below the "
    "true release speed.",
]
for s in p1:
    ws.append([s]); ws.cell(row=ws.max_row, column=1).alignment = Alignment(wrap_text=True)
    ws.merge_cells(f'A{ws.max_row}:F{ws.max_row}')

ws.append([])
headers = ["clip", "method", "predicted kph", "true kph", "diff", "note"]
ws.append(headers)
hdr_row = ws.max_row
rows = [
    ("C4", "OLD: whole flight, release->bat (0.52s total, 15% of that time is after the bounce)", 130.8, 136.69, "-5.9", "underestimate"),
    ("C4", "NEW: pre-bounce segment only, release->bounce (0.44s)", 136.2, 136.69, "-0.5", "much tighter"),
    ("C5", "OLD: whole flight, release->keeper (0.68s total, 41% of that time is after the bounce)", 100.1, 138.82, "-38.8", "way off - most of the flight time here was the slow post-bounce crawl to the keeper"),
    ("C5", "NEW: pre-bounce segment only, release->bounce (0.40s)", 141.8, 138.82, "+3.0", "much tighter"),
]
for r in rows:
    ws.append(r)
for i in range(len(rows)):
    row_i = hdr_row+1+i
    for c in range(1,7):
        ws.cell(row=row_i, column=c).font = BASE_FONT
        ws.cell(row=row_i, column=c).alignment = Alignment(wrap_text=True, vertical="top")
for col_idx, h in enumerate(headers, 1):
    c = ws.cell(row=hdr_row, column=col_idx)
    c.font = HEADER_FONT; c.fill = HEADER_FILL
    c.alignment = Alignment(horizontal="center", wrap_text=True)

ws.append([])
ws.append(["The catch:"])
ws.cell(row=ws.max_row, column=1).font = Font(name=FONT, bold=True)
p2 = [
    "The fix above (only time the ball BEFORE it bounces) is much more accurate - but to know the pre-bounce "
    "DISTANCE, we need to already know where it bounces (bounce_x). And bounce_x is exactly the number we're "
    "using speed to calculate in the first place. One equation, two unknowns - can't solve both from scratch with "
    "nothing else to go on.",
    "So this fix is best used as a SECOND PASS: get a first speed number from wherever we can (true answer, or "
    "the on-screen speed-gun graphic when it's shown), use that to get a first bounce_x, then re-time using only "
    "the pre-bounce window to sharpen the speed number, then redo bounce_x with the sharper speed. It tightens "
    "things up, it doesn't invent a speed number from nothing.",
]
for s in p2:
    ws.append([s]); ws.cell(row=ws.max_row, column=1).alignment = Alignment(wrap_text=True)
    ws.merge_cells(f'A{ws.max_row}:F{ws.max_row}')

ws.append([])
ws.append(["For clips where NO speed number shows up anywhere on screen at all - what then?"])
ws.cell(row=ws.max_row, column=1).font = Font(name=FONT, bold=True)
p3 = [
    "Tried one genuinely from-scratch idea: cricket balls lose a fairly consistent chunk of their speed hitting "
    "the pitch (it's a known real-world effect - the ball grips and skids). If we knew that 'how much speed is "
    "kept after the bounce' number reliably, we could work backward from the total release-to-bat time using "
    "gravity/physics alone, no outside speed reading needed.",
    "Checked what that number actually was on our 2 known clips: C4 the ball kept about 47% of its speed after "
    "bouncing; C5 it kept about 28%. That's a big difference for what should be a fairly physical constant, "
    "which tells us it's not reliable yet - the post-bounce window we're timing is only 2-7 video frames long, "
    "so a single frame of rounding error swings the number a lot.",
    "Honest conclusion: this from-scratch idea is a real avenue, but with only 2 clips to check it against and "
    "such short post-bounce timing windows, we don't have a trustworthy number yet. Needs either more example "
    "clips or a way to time the post-bounce hop more precisely (e.g. slow-motion / higher frame rate) before it "
    "can be used as a genuine fallback. Not using it yet - flagging it as unfinished rather than pretending it "
    "works.",
]
for s in p3:
    ws.append([s]); ws.cell(row=ws.max_row, column=1).alignment = Alignment(wrap_text=True)
    ws.merge_cells(f'A{ws.max_row}:F{ws.max_row}')

note = ws.cell(row=ws.max_row+2, column=1,
    value="Bottom line / recommended order for getting a speed number, best to worst: (1) on-screen speed-gun "
          "graphic if the broadcast shows one anywhere in the clip - proven accurate, not answer-key reading; "
          "(2) our timing method, but re-run using only the pre-bounce window once a first bounce_x guess exists "
          "- tight, within a few kph; (3) our old whole-flight timing method as a rough last resort - known to "
          "run low, worse the longer the ball sits around after pitching; (4) a pure physics fallback with no "
          "speed reading at all is not ready yet - the piece we'd need (typical post-bounce speed retention) "
          "isn't measuring consistently enough on just 2 clips to trust.")
note.font = Font(name=FONT, italic=True, size=9, color="808080")
note.alignment = Alignment(wrap_text=True)
ws.merge_cells(f'A{note.row}:F{note.row}')
ws.row_dimensions[note.row].height = 110

widths = [10, 46, 14, 12, 10, 30]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w

wb.save('cricket_tracking.xlsx')

ws2 = wb['Notes']
new_notes = [
    (str(date.today()), "Dug into why our own timing-based speed guess was off (asked to keep this method alive "
                          "as a fallback for whenever the broadcast doesn't show a speed-gun graphic). Found the "
                          "cause: our old calc used the WHOLE flight (release to bat), which blends the fast "
                          "pre-bounce ball with the much slower post-bounce hop after it grips the pitch. C4 "
                          "(only 15% of its flight time was post-bounce) was off by -5.8kph; C5 (41% of its "
                          "flight time was post-bounce) was off by a huge -38.8kph. The more time spent crawling "
                          "along after the bounce, the worse the average speed underestimates the real release "
                          "speed."),
    (str(date.today()), "Fix: time only the PRE-BOUNCE part of the flight (release frame to bounce frame) instead "
                          "of the whole thing. Tested: C4 goes from -5.8kph off to -0.5kph off; C5 goes from "
                          "-38.8kph off to +3.0kph off. Big improvement. Catch: this needs to already know roughly "
                          "where the ball bounces, which is the very thing speed is used to calculate - so it's a "
                          "second-pass sharpening step (get a rough speed -> rough bounce_x -> re-time pre-bounce "
                          "only -> sharper speed -> sharper bounce_x), not a from-scratch answer."),
    (str(date.today()), "Also tried a genuinely from-scratch idea for clips with no speed reading available at all: "
                          "cricket balls keep a fairly consistent % of their speed after bouncing, so if we knew "
                          "that % reliably we could solve for release speed using gravity/timing alone. Checked it "
                          "on our 2 known clips: C4 kept ~47% of its speed after the bounce, C5 only ~28% - too "
                          "inconsistent to trust with just 2 clips and only 2-7 video frames to time the bounce-to-"
                          "bat gap. Logged as a genuine but unfinished idea (Speed_Method sheet), not used yet - "
                          "didn't want to bolt on a shaky number and call it solved."),
]
for row in new_notes:
    ws2.append(row)
for row_i in range(ws2.max_row - len(new_notes) + 1, ws2.max_row + 1):
    ws2.cell(row=row_i, column=1).font = BASE_FONT
    ws2.cell(row=row_i, column=2).font = BASE_FONT
    ws2.cell(row=row_i, column=2).alignment = Alignment(wrap_text=True)
wb.save('cricket_tracking.xlsx')
print('done')
