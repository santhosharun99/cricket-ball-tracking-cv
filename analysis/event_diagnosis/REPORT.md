# Bounce confirmation diagnosis

C4 was not a wrong bounce position: the seeded guide selected the ball through frame105, including its downward-to-upward turn at104. There are no detector boxes at106–108, so the previous rule cannot obtain a second upward observation. Visual review of original frames saved in C4_review.jpg supports this account. Later low-confidence boxes at109/110 are rejected by the guide. Do not assume they are the ball.

A new small state machine retains a tentative bounce after two downward segments and one upward segment. Another upward observation within three frames confirms it. A contradictory sighting rejects it; no confirming sighting leaves it explicitly unconfirmed. Only accepted detections enter this rule, never predicted points. Segment gaps must be at most two frames when opening a candidate. Threshold remains5px/frame.

| clip   |   bounce_frame |   first_up_frame | status      |   confirmation_frame |   event_count |   reference_frame |   error_frames |   closed_frame |
|:-------|---------------:|-----------------:|:------------|---------------------:|--------------:|------------------:|---------------:|---------------:|
| C1     |             98 |               99 | confirmed   |                  100 |             1 |                98 |              0 |            nan |
| C2     |            nan |              nan | none        |                  nan |             0 |               nan |            nan |            nan |
| C3     |             95 |               96 | confirmed   |                   97 |             1 |                95 |              0 |            nan |
| C4     |            104 |              105 | unconfirmed |                  nan |             1 |               104 |              0 |            109 |
| C5     |             84 |               85 | confirmed   |                   87 |             1 |                84 |              0 |            nan |

There are still **three confirmed bounces out of four scorable clips**, plus one correctly located but unconfirmed candidate. This is not a new 100% accuracy claim. C2 has no event/reference. All tracks start from five manually verified ball sightings. This modification was motivated by a known C4 failure; all results are development diagnostics.

The new state does not solve unseeded foot/body false tracks or release timing. Its value is preserving useful uncertainty instead of silently losing the event. No source/production pipeline changed.

Checks passed for confirmed, expired/unconfirmed, contradictory/rejected and jitter sequences. All five clip histories replayed using cached local detections; no model inference or cloud compute was needed. events.mp4 shows state transitions, not a ground-truth-labelled detection accuracy test after the original scoring windows.

Reproduce from project root:
```
python3 analysis/event_diagnosis/trace.py
python3 analysis/event_diagnosis/evaluate_state.py
python3 analysis/event_diagnosis/report.py
```

Next: inspect locally available hand/pose tools for acquisition and release, then test explicit hand-ball separation rather than equating track start with release. No pose/X3D model files were found in the two inspected project directories; this is not a search of every computer cache. Models must not be downloaded or trained silently.
