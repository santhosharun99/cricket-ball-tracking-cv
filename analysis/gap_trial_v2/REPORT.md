# Bounce restart: second hidden-frame trial

Recognising an observed bounce and restarting the curve helped. On exactly the same 46 short-gap cases, the earlier blend recovered 26 balls; adding the restart recovered 31. Allowing a strong, unambiguous visual detection to override a rejected prediction recovered 44. Detector-only still recovered 46.

| Method | Correct first returns | Rate |
|---|---:|---:|
| Previous straight/curved blend | 26/46 | 56.5% |
| Blend with observed-bounce restart | 31/46 | 67.4% |
| Restart plus clear visual override | 44/46 | 95.7% |
| Detector only | 46/46 | 100% |

The restart itself added five successes without losing any short-gap successes. The visual override added another thirteen. The 95.7% result is mostly evidence that allowing clear visual evidence prevents the prediction from blocking correct detections; it is not evidence that physics outperforms the detector.

The restart helped only after an upward turn was already observed. It cannot predict a completely hidden bounce from an entirely incoming track. In the 17 gaps starting before the bounce and returning at/after it, restart-only stayed at 8/17; allowing visual override raised it to 17/17. For the ten cases with last-seen at/after bounce, restart-only rose from 0/10 to 5/10, and visual override to 8/10. Before the bounce, restart left the original blend unchanged at 18/19.

Five-frame gaps remain difficult: previous blend 5/15, restart-only 4/15, restart plus visual override 13/15, detector-only 15/15. Restart is therefore not uniformly better. The two remaining short-gap failures both have a last-seen observation at the C1 bounce before upward motion becomes visible, with competing detections preventing the conservative override.

## What changed

The predictor sees only five earlier, manually verified detector sightings. After two downward image-motion intervals above 5 pixels/frame followed by an upward interval below -5 pixels/frame, it discards the incoming portion and fits the outgoing path starting at the observed peak. One upward interval is tentative; two consistent upward intervals confirm the motion turn. With fewer than four outgoing observations it uses a straight fit; otherwise the earlier 50/50 linear/quadratic blend.

This is an image-motion turn cue, not independent proof of contact with the pitch. Camera movement and other direction changes can fool it. It remains a local screen-space prediction experiment, not a calibrated gravity/drag simulator.

The optional override applies when the motion search rejects all candidates. A candidate needs detector confidence at least 0.60 and a lead of at least 0.20 over every spatially distinct candidate more than 20 pixels away. Near-duplicate boxes are not treated as competing objects. These are fixed illustrative settings, not calibrated probabilities. The override does not currently rescue a wrongly accepted in-gate candidate; that risk needs ambiguous-scene tests.

## Evaluation boundaries

The same cached detections, reference labels, case list, history inputs, 60-pixel search radius, 20-pixel correctness radius and exclusions were used. Baseline outputs reproduced exactly. Neither the predictor nor its reset has access to future bounce annotations, hidden-frame detections, later speed graphics or metric ground-truth answers. Phase labels appear only in scoring.

This is a development rerun on known examples, not new held-out evidence. The 46 overlapping gaps come from four deliveries. Histories are manually seeded correctly, and return-frame labels were detector-assisted and manually checked. Four primary cases returning to unlabelled/obscured frames remain excluded. No additional clips or difficult frames were removed for v2. Clear returning frames favour the detector baseline; these percentages are not general tracking accuracy. C2 remains untested.

Equation, causality-boundary, jitter, missing-candidate, ambiguity and duplicate-box checks passed. The existing tracker and source videos were not modified. The module is experimental and has not been installed into the production tracker.

## Reproduce

From the project directory:

```sh
python3 analysis/gap_trial_v2/evaluate.py
```

`protocol.json` records settings before scoring. `predictor_v2.py` contains the standalone causal predictor and selector. `cases.csv` records each outcome, prediction and selection reason. `overall.csv`, `long_gaps.csv`, `per_phase.csv`, `per_clip.csv`, `per_state.csv`, `per_selection_reason.csv` and `paired_outcomes.csv` provide the audit trail; `checks.json` records verification.

The script reuses `../gap_trial/detections.json`, `references.json`, `cases.csv` and `protocol.json`. The original trial's environment and model hashes remain applicable.

Keep the restart as an experimental component. The next useful evidence would come from genuinely ambiguous returning frames or new deliveries, with the same fixed settings. No new weighting should be chosen merely to maximise this small sample.
