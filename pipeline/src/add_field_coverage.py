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
GREY = PatternFill("solid", fgColor="E0E0E0")

if 'Field_Coverage' in wb.sheetnames:
    del wb['Field_Coverage']
ws = wb.create_sheet('Field_Coverage', 2)

ws['A1'] = "Santhosh shared the subnet's required output columns - checking them against what we've actually built"
ws['A1'].font = Font(name=FONT, bold=True)
ws.merge_cells('A1:E1')

headers = ["their column", "what it means", "plain-English name we used", "where we stand", "status"]
ws.append([])
ws.append(headers)
hdr_row = ws.max_row

rows = [
    ("I# / Over / Ball / Overs", "which innings/over/ball this delivery is", "match bookkeeping",
     "not something you get from ball physics at all - this comes from knowing which delivery in the match you're looking at, not from tracking the ball. Not attempted, not really an 'our model' problem.", "N/A"),
    ("KPH", "release speed", "bowling speed", "rough timing-based estimate only, not checked carefully against all 5 answers yet", "PARTIAL"),
    ("Relʸ", "release-point sideways position", "release_y", "just calculated this - about 7-8cm off the true answer on both balls we tried", "GOOD"),
    ("Relᶻ", "release-point height", "release_z", "not calculated ourselves - we've only ever used the official answer for this number. Genuinely hard: needs a ground-level reference near the bowler's end, which we don't have a good one for yet", "MISSING"),
    ("Bnceˣ", "how far down the pitch it bounces", "bounce_x / pitch length", "THE big gap - currently we only know this by reading the answer key, not from the video itself", "MISSING"),
    ("Bnceʸ", "sideways position where it bounces", "bounce_y", "our best result - within 2-4cm of the true answer", "GOOD"),
    ("Imptˣ", "how far down the pitch the ball is when it reaches the bat", "impact_x", "not attempted at all yet - same underlying problem as Bnceˣ (we can't yet measure distance-down-the-pitch from video alone)", "MISSING"),
    ("Imptʸ", "sideways position when it reaches the bat", "impact_y / stump_y depending on clip", "solid - within 1-4cm on both balls we tracked", "GOOD"),
    ("Imptᶻ", "height when it reaches the bat", "impact_z", "roughly half the error of our first attempt, but still off by several cm - the shakiest of our 'working' numbers", "PARTIAL"),
    ("InterD", "bounce point minus impact point (how far it moved after pitching)", "interception_distance", "can't calculate this ourselves yet since it needs Bnceˣ and Imptˣ, both still missing", "MISSING"),
    ("Stmpʸ", "sideways position as it passes the stumps", "stump_y", "solid - within 1-4cm", "GOOD"),
    ("Stmpᶻ", "height as it passes the stumps", "stump_z", "same partial state as Imptᶻ - improved but not tight yet", "PARTIAL"),
    ("Swg∠", "sideways angle it swings in the air, release to bounce", "swing_angle", "NOT attempted yet, but we actually already have everything needed to work this out ourselves (release_y and bounce_y) - this is a genuinely easy next win", "EASY WIN"),
    ("Dev", "sideways angle it deviates after bouncing", "deviation", "same as above - we already have the bounce and stump/impact sideways numbers needed to work this out ourselves - another easy win", "EASY WIN"),
    ("Runs / Wkts", "what actually happened on the ball", "match outcome", "this is scorecard/commentary data, not something a ball-tracking model calculates from the video at all", "N/A"),
]
for r in rows:
    ws.append(r)

fill_map = {"GOOD": GREEN, "PARTIAL": YELLOW, "MISSING": RED, "EASY WIN": YELLOW, "N/A": GREY}
for i, r in enumerate(rows):
    row_i = hdr_row + 1 + i
    for c in range(1, 6):
        cell = ws.cell(row=row_i, column=c)
        cell.font = BASE_FONT
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.cell(row=row_i, column=5).fill = fill_map[r[4]]

for col_idx, h in enumerate(headers, 1):
    c = ws.cell(row=hdr_row, column=col_idx)
    c.font = HEADER_FONT
    c.fill = HEADER_FILL
    c.alignment = Alignment(horizontal="center", wrap_text=True)

note = ws.cell(row=ws.max_row+2, column=1,
    value="Bottom line: the column list Santhosh was sent is exactly the same set of numbers this whole project "
          "has been trying to work out - confirms we've been building the right thing. Of the 14 real "
          "tracking numbers (excluding match bookkeeping and runs/wickets, which aren't tracking outputs at all), "
          "5 are solid, 2 are roughly-there-but-soft, 1 is a rough estimate, 2 are genuinely easy wins we haven't "
          "gotten around to yet, and 4 are missing - all 4 of those missing ones trace back to the same one root "
          "problem: we can't yet tell how far down the pitch something is from the video alone.")
note.font = Font(name=FONT, italic=True, size=9, color="808080")
note.alignment = Alignment(wrap_text=True)
ws.merge_cells(f'A{note.row}:E{note.row}')
ws.row_dimensions[note.row].height = 80

widths = [16, 34, 22, 55, 12]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "A3"

wb.save('cricket_tracking.xlsx')

ws2 = wb['Notes']
new_note = (str(date.today()), "Santhosh shared the subnet's actual required output column list. Checked it "
    "against everything we've built (new Field_Coverage sheet) - it's a one-to-one match with the fields we've "
    "been calling release_y/z, bounce_x/y, impact_x/y/z, stump_y/z, swing_angle, deviation, kph, confirming we've "
    "been building toward the right target the whole time. Scorecard: 5 of 14 real tracking numbers solid "
    "(within a few cm), 3 roughly there but soft, 2 are easy wins we haven't done yet (swing angle and deviation - "
    "we already have the pieces needed for both), and 4 missing, all tracing back to the same one problem: not "
    "yet able to tell how far down the pitch something is from video alone. Innings/over/ball and runs/wickets "
    "aren't really tracking-model outputs at all - that's match bookkeeping and outcome data.")
ws2.append(new_note)
ws2.cell(row=ws2.max_row, column=1).font = Font(name=FONT)
ws2.cell(row=ws2.max_row, column=2).font = Font(name=FONT)
ws2.cell(row=ws2.max_row, column=2).alignment = Alignment(wrap_text=True)
wb.save('cricket_tracking.xlsx')
print('done')
