"""
Build cricket_tracking.xlsx - the running tracker for the cricket ball-tracking
prototype project. Sheets:
  1. Clips           - metadata per clip + which camera segment is the usable delivery view
  2. Ground_Truth     - official answer key (from examples.json) per clip
  3. Ball_Tracking     - frame-by-frame pixel coordinates of the ball (filled in as we detect it)
  4. Our_Predictions   - our computed six scored fields per clip, plus error vs ground truth
  5. Notes             - assumptions / methodology log, dated
"""
import json
from datetime import date
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

FONT = "Arial"
HEADER_FILL = PatternFill("solid", fgColor="305496")
HEADER_FONT = Font(name=FONT, bold=True, color="FFFFFF")
NOTE_FONT = Font(name=FONT, italic=True, size=9, color="808080")
BASE_FONT = Font(name=FONT)

wb = Workbook()

# ---------------------------------------------------------------- Clips ----
ws = wb.active
ws.title = "Clips"
headers = ["clip_id", "filename", "width", "height", "fps", "frame_count",
           "duration_s", "delivery_segment_start_frame", "delivery_segment_end_frame",
           "ball_release_frame_approx", "camera_locked_off", "status", "notes"]
ws.append(headers)

clips = [
    ["C1", "f81d092b6117be1126e0d6be97220b3f9a2870eb.mp4", 1920, 1080, 25, 813, 32.52,
     None, None, None, "Yes", "problem clip",
     "First camera cut ends before ball release; second segment starts after the shot is "
     "already played. Neither obvious segment cleanly brackets the ball flight - unresolved."],
    ["C2", "9ef5c0e6e68a01d5435499bc0527c04386e527fc.mp4", 1280, 720, 30, 1260, 42.00,
     None, None, None, "Not yet checked", "not yet reviewed", ""],
    ["C3", "98e537a2a3555da28ca7eea3227babb61df228d1.mp4", 1920, 1080, 25, 1295, 51.80,
     None, None, None, "Not yet checked", "not yet reviewed", ""],
    ["C4", "6a79fbe0fd6792126c69087568f7f08318dcf449.mp4", 1920, 1080, 25, 543, 21.72,
     None, None, None, "No (11.9/2.1px shift, scale 1.0114)", "not yet reviewed", ""],
    ["C5", "bad1530d039b7146a8ce4a1b1a6b29502c3c9491.mp4", 1920, 1080, 25, 556, 22.24,
     42, 139, 74, "Yes (0.0px shift, scale 1.0000)", "confirmed clean example",
     "Segment 42-139 shows full delivery view (both stumps + pitch). Ball visible in flight "
     "from ~frame 74 (bball_8.jpg) just after release."],
]
for row in clips:
    ws.append(row)

for col_idx, h in enumerate(headers, 1):
    c = ws.cell(row=1, column=col_idx)
    c.font = HEADER_FONT
    c.fill = HEADER_FILL
    c.alignment = Alignment(horizontal="center", wrap_text=True)
for r in range(2, ws.max_row + 1):
    for c in range(1, len(headers) + 1):
        ws.cell(row=r, column=c).font = BASE_FONT
widths = [6, 42, 7, 7, 6, 11, 10, 14, 14, 14, 30, 20, 55]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "A2"

# --------------------------------------------------------- Ground_Truth ----
ws2 = wb.create_sheet("Ground_Truth")
with open("data/examples.json") as f:
    examples = json.load(f)

gt_fields = ["kph", "release_y", "release_z", "bounce_x", "bounce_y",
             "impact_x", "impact_y", "impact_z", "interception_distance",
             "stump_y", "stump_z", "swing_angle", "deviation", "runs", "wickets"]
gt_headers = ["clip_id", "video_url"] + gt_fields
ws2.append(gt_headers)

clip_ids = ["C1", "C2", "C3", "C4", "C5"]
for cid, ex in zip(clip_ids, examples):
    row = [cid, ex["video_url"]] + [ex["prediction"].get(f) for f in gt_fields]
    ws2.append(row)

for col_idx, h in enumerate(gt_headers, 1):
    c = ws2.cell(row=1, column=col_idx)
    c.font = HEADER_FONT
    c.fill = HEADER_FILL
    c.alignment = Alignment(horizontal="center", wrap_text=True)
for r in range(2, ws2.max_row + 1):
    for c in range(1, len(gt_headers) + 1):
        ws2.cell(row=r, column=c).font = BASE_FONT
ws2.column_dimensions["A"].width = 8
ws2.column_dimensions["B"].width = 55
for i in range(3, len(gt_headers) + 1):
    ws2.column_dimensions[get_column_letter(i)].width = 13
ws2.freeze_panes = "A2"
note = ws2.cell(row=len(clip_ids) + 3, column=1,
                 value="Source: https://console.scorestudio.ai/starter-packs/cricket-balltrack/examples.json "
                       "(official Score Studio example answer key, fetched 2026-09).")
note.font = NOTE_FONT

# -------------------------------------------------------- Ball_Tracking ----
ws3 = wb.create_sheet("Ball_Tracking")
bt_headers = ["clip_id", "frame_number", "time_s", "ball_x_px", "ball_y_px",
              "detection_method", "confidence", "verified_by_eye", "notes"]
ws3.append(bt_headers)
for col_idx, h in enumerate(bt_headers, 1):
    c = ws3.cell(row=1, column=col_idx)
    c.font = HEADER_FONT
    c.fill = HEADER_FILL
    c.alignment = Alignment(horizontal="center", wrap_text=True)
widths3 = [8, 13, 9, 11, 11, 20, 11, 15, 40]
for i, w in enumerate(widths3, 1):
    ws3.column_dimensions[get_column_letter(i)].width = w
ws3.freeze_panes = "A2"
ex_row = ["C5", 74, "=B2/25", 0, 0, "manual / motion-diff / model", "0-1", "yes/no", ""]
ws3.append(ex_row)
for c in range(1, len(bt_headers) + 1):
    ws3.cell(row=2, column=c).font = Font(name=FONT, color="0000FF", italic=True)
legend = ws3.cell(row=4, column=1,
                   value="Legend: blue italic row 2 is an example row only - delete once real "
                         "tracking data is entered. time_s = frame_number / fps (formula).")
legend.font = NOTE_FONT

# ------------------------------------------------------- Our_Predictions ----
ws4 = wb.create_sheet("Our_Predictions")
pred_headers = ["clip_id"] + [f"pred_{f}" for f in gt_fields] + \
               [f"truth_{f}" for f in ["kph", "bounce_x", "stump_y", "deviation", "swing_angle", "stump_z"]] + \
               ["abs_error_kph", "abs_error_bounce_x", "abs_error_stump_y",
                "abs_error_deviation", "abs_error_swing_angle", "abs_error_stump_z", "weighted_score"]
ws4.append(pred_headers)
for cid in clip_ids:
    ws4.append([cid] + [None] * (len(pred_headers) - 1))
for col_idx, h in enumerate(pred_headers, 1):
    c = ws4.cell(row=1, column=col_idx)
    c.font = HEADER_FONT
    c.fill = HEADER_FILL
    c.alignment = Alignment(horizontal="center", wrap_text=True)
for i in range(1, len(pred_headers) + 1):
    ws4.column_dimensions[get_column_letter(i)].width = 14
ws4.freeze_panes = "A2"

# Pull truth values in with formulas referencing Ground_Truth sheet, and compute abs error
# gt_headers = clip_id(A), video_url(B), kph(C), release_y(D), release_z(E), bounce_x(F),
# bounce_y(G), impact_x(H), impact_y(I), impact_z(J), interception_distance(K), stump_y(L),
# stump_z(M), swing_angle(N), deviation(O), runs(P), wickets(Q)
truth_col_map = {"kph": "C", "bounce_x": "F", "stump_y": "L", "deviation": "O", "swing_angle": "N", "stump_z": "M"}
gt_row_for = {cid: i + 2 for i, cid in enumerate(clip_ids)}
pred_col_map = {h: get_column_letter(i + 1) for i, h in enumerate(pred_headers)}

for cid in clip_ids:
    r = gt_row_for[cid]
    for f, gt_col in truth_col_map.items():
        truth_cell = pred_col_map[f"truth_{f}"] + str(r)
        ws4[truth_cell] = f"=Ground_Truth!{gt_col}{r}"
        pred_cell = pred_col_map[f"pred_{f}"] + str(r)
        err_cell = pred_col_map[f"abs_error_{f}"] + str(r)
        ws4[err_cell] = f"=IF(OR({pred_cell}=\"\",{truth_cell}=\"\"),\"\",ABS({pred_cell}-{truth_cell}))"

note4 = ws4.cell(row=len(clip_ids) + 3, column=1,
                  value="Fill pred_* columns once our pipeline computes each field. "
                        "abs_error_* and weighted_score are formulas - do not hardcode.")
note4.font = NOTE_FONT

# ------------------------------------------------------------------ Notes --
ws5 = wb.create_sheet("Notes")
ws5.append(["date", "note"])
for col_idx in (1, 2):
    c = ws5.cell(row=1, column=col_idx)
    c.font = HEADER_FONT
    c.fill = HEADER_FILL
notes_log = [
    (str(date.today()), "5 official example clips + ground truth downloaded from Score Studio "
                          "(console.scorestudio.ai starter pack). Confirmed real, playable MP4s."),
    (str(date.today()), "Scene-cut detection (histogram Bhattacharyya) found 3-11 camera cuts per "
                          "clip - real broadcast footage, not single-camera academic clean feed."),
    (str(date.today()), "Camera-motion check (ORB+homography) confirmed the delivery segment is "
                          "locked-off (no pan/zoom) in C1, C4, C5 - one calibration per clip is enough."),
    (str(date.today()), "First automatic pitch/segment detector (HSV tan-color heuristic) failed - "
                          "picked wrong segment on 4/5 clips (fooled by sponsor banners/skin tone). "
                          "Segment identification is being done by manual visual inspection for now."),
    (str(date.today()), "C1 (f81d092b) has a real problem: neither obvious camera segment cleanly "
                          "shows the full ball flight (cut happens between run-up and post-shot)."),
    (str(date.today()), "C5 (bad1530d) confirmed clean: segment frames 42-139, ball visible in "
                          "flight from ~frame 74. Using this as the first full test case."),
    (str(date.today()), "Motion-based ball candidate detector (frame differencing + brightness "
                          "weighting for white ball) is too noisy on C1 (140-540 candidates/frame, "
                          "dominated by animated LED sponsor boards). Re-testing on C5's clean segment next."),
]
for row in notes_log:
    ws5.append(row)
for r in range(2, ws5.max_row + 1):
    ws5.cell(row=r, column=1).font = BASE_FONT
    ws5.cell(row=r, column=2).font = BASE_FONT
    ws5.cell(row=r, column=2).alignment = Alignment(wrap_text=True)
ws5.column_dimensions["A"].width = 12
ws5.column_dimensions["B"].width = 110
ws5.freeze_panes = "A2"

wb.save("cricket_tracking.xlsx")
print("saved")
