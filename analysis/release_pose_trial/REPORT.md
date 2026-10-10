# release_pose_trial - first look, C1 only

Question: can the bowler's wrist position (mediapipe pose, CPU, no external model
download needed - see note below) act as a stand-in for "where the ball is" during the
pre-release phase, where the ball detector finds nothing because the ball is still in/near
the hand? If the wrist-to-ball gap is small before the reviewed release frame and clearly
grows after it, that gap could become an automatic release signal.

## Setup

- Clip: C1 (f81d092b...), reviewed release interval 90-91 (per the project notes).
- Window inspected: frames 80-99.
- Pose: mediapipe 0.10.14, LEGACY `mp.solutions.pose` API (static_image_mode, CPU, XNNPACK
  delegate). This API bundles its own small model inside the pip package - it does NOT need
  the newer Tasks-API `.task` file, and does NOT hit the `libEGL.so.1` missing-library error
  that mediapipe 1.0.1's Tasks API hit in this sandbox (no root access to install libegl1).
  Recorded for whoever continues this: if a future step specifically needs the newer
  Tasks API (e.g. for its extra hand-detail features), that still requires either root to
  install libegl1, or running on a machine that already has it - the legacy API sidesteps
  the whole problem for plain landmark tracking.
- Ball positions: the cached `analysis/event_timing_trial/raw_detections.json`, reused
  as-is, not re-detected. Important: this cache has NO candidates at all for C1 frames
  80-90, i.e. the detector found nothing there in the original run either - consistent with
  the ball being in/against the hand, not yet a separate visible object.

## Result (both wrists recorded; bowler is right-arm, so right wrist is the relevant one)

| frame | pose found? | right-wrist to nearest ball-candidate (px) | note |
|---:|---|---:|---|
| 82-88 | mostly yes | mostly no ball candidate to compare | detector empty pre-release, as expected |
| 89 | yes | **24.6px** | closest reading in the whole window - wrist right next to a ball candidate, one frame before the reviewed release window |
| 90-93 | pose or ball missing every frame | - | gap in coverage right across the reviewed release window itself |
| 94 | yes | 230.3px (jumped from ~25 to ~230) | ball candidate now well out into the pitch, clearly separated |
| 97-99 | yes | 138-152px | ball further down the pitch, gap holding |

Visually confirmed (not just trusting the numbers): frame 89 and 90's mediapipe skeleton is
correctly drawn on the actual bowler (Hazlewood), not a spectator or the wrong player - the
stick-figure follows his bowling arm through release. Frame 94 shows the ball candidate
clearly out over the pitch, well away from the bowler.

## Honest read

This is a promising first look, not a working detector. The one usable before/after pair
(24.6px at frame 89 -> 230px at frame 94) is in the right direction and the right rough size
- but there are real gaps: no ball candidate exists at all for 6 of the 9 pre-release frames,
and BOTH pose and ball tracking drop out across frames 90-93, which is exactly the reviewed
release window itself - so this run cannot yet claim it caught the release moment directly,
only that it caught the state before and the state clearly after. One clip, one pair of
readings either side of a gap is not a validated method. Do not call this solved.

## What would actually test this properly

1. Run on all 5 clips, not 1, and report every clip's numbers including failures - same
   standard used throughout this project.
2. Fix the coverage gap across the release window itself: either lower the pose detector's
   confidence threshold, or track pose on every frame in sequence (not independently frame-
   by-frame) so a temporary occlusion doesn't produce a total miss.
3. Get a real pre-release ball-candidate signal for the missing frames 82-88, or accept
   that gap is real and design the release rule around "last confident small gap" rather
   than needing every single frame.
4. Confirm bowling arm automatically (currently assumed right-arm by eye) rather than by
   inspecting both wrists manually per clip.

## Reproduction

```
cd '.'
python3 analysis/release_pose_trial/run.py
```

Reuses `analysis/event_timing_trial/raw_detections.json` - no new YOLO inference, no
network calls. Output: `results.json` (full per-frame data) and `frames/` (annotated JPGs
for visual review, one per frame in the 80-99 window).


## v2 attempt (FAILED - wrong subject tracked, keeping for the record)

Tried switching mediapipe to sequential/video mode (`static_image_mode=False`) plus
`model_complexity=2` and lower confidence thresholds, hoping to close the frame-90-93 gap
seen in the v1 result above. `model_complexity=2` immediately failed - it needs an on-demand
model download that is blocked from this sandbox (same allowlist wall as the Tasks-API
`.task` file), so complexity was kept at 1.

Result with video mode: pose was found in nearly every frame (gap "closed"), but the
wrist-to-ball distances became large and unstable (C1 frame 89: 304.0px, versus 24.6px in
v1). Visually checked frame C1_f089.jpg from this run: **the skeleton is drawn on the
UMPIRE, not the bowler.** Video mode carries the region-of-interest from the previous frame
forward instead of re-detecting the person each frame, and it locked onto the umpire (who
stands still, centred in frame) instead of the moving bowler at the frame's edge. This
completely invalidates v2's numbers - discarded. Real lesson: closing a coverage gap by
changing tracking mode is not automatically progress if it changes WHICH PERSON is tracked;
always re-verify against the actual frames after any parameter change, not just the printed
numbers.

Files kept for the record: run_v2.py, results_v2.json, frames_v2/ (do not reuse the numbers
in results_v2.json for anything).

## v3 attempt: back to what worked (static_image_mode=True), all 4 scorable clips

Reverted to `static_image_mode=True` (confirmed correct on the bowler in v1) and only
lowered `min_detection_confidence` (0.5 -> 0.2), no other changes. Ran on all 4 clips with a
reviewed release reference (C1, C3, C4, C5 - C2 excluded, no reviewed release exists for it).
Visually re-confirmed on 3 sample frames (C1 f085, f089, f090) that the skeleton is correctly
on the bowler, not the umpire, this time.

Closest right-wrist-to-ball reading per clip, in the window around its reviewed release:

| clip | reviewed release | closest reading (px) | at frame | how many frames before it had no pose+ball pair to compare |
|---|---:|---:|---:|---|
| C1 | 90-91 | **8.9px** | 89 (one frame before) | several - detector cache empty most pre-release frames |
| C3 | 83-84 | 220-246px range, nothing close | various | pose dropped out entirely frames 77-81 |
| C4 | 92-93 | 153.8px (frame 85), nothing closer near release | 85 | pose dropped out frames 82-83, 86-87, 90-92 |
| C5 | 73-74 | 111.0px (frame 79, AFTER release, not before) | 79 | pose dropped out frames 63-65, 67-69, 71, 73, 75, 77-78 |

## Honest overall verdict

C1 alone shows a real, visually-confirmed, tight wrist-ball proximity (8.9-24.6px depending
on exact settings) exactly one frame before its reviewed release - a genuinely encouraging
sign on that one clip. **This does NOT repeat on C3, C4 or C5** - their closest readings are
10-25x larger and none of them land convincingly right before the reviewed release frame.
Pose detection itself is also much patchier on C3/C4/C5 than C1 (many more missed frames),
which may be the camera angle, bowler distance from camera, or motion blur rather than
anything about the release-detection idea itself - not yet diagnosed which.

Conclusion: one promising clip out of four is not a validated method. This is exactly the
kind of result the project's own standard calls for reporting plainly rather than dressing
up - hand/pose tracking for release detection remains an open, partially-encouraging,
mostly-unproven lead, not a solved step. Do not use the 8.9px number as a general threshold.

## Next steps if continuing this thread

1. Diagnose why C3/C4/C5 lose pose tracking so much more than C1 - likely candidates:
   bowler is smaller/further from camera, different run-up direction crosses more clutter,
   or motion blur is worse on these specific deliveries. Check by cropping tighter around
   the known bowler run-up area (per-clip, using the crease location) before running pose,
   instead of running it on the full wide frame where the person-detector has to find the
   bowler among several people.
2. If cropping doesn't help, this method may simply not generalise across camera angles
   with the current, unmodified mediapipe person-detector - worth stating plainly rather
   than forcing more parameter sweeps on the same setup.
3. Separately: the cached ball-detector (event_timing_trial/raw_detections.json) has no
   candidates at all for most pre-release frames on every clip, not just C1 - re-running
   detection with a much lower confidence threshold specifically on the pre-release window
   might recover some of that (this needs torch/ultralytics installed, deliberately deferred
   so far - a real, scoped decision point, not a small add-on).
