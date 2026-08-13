# Adaptive Capacity

Capacity is a prediction for planning, not a judgment or permanent ceiling.

## Bands

- `constrained`: protect essentials; normally 1–2 meaningfully scoped outcomes.
- `normal`: baseline of 3 outcomes.
- `open`: up to 4 outcomes only when recent delivery and upcoming constraints support it.

Required maintenance and fixed commitments are tracked separately from outcomes.

## Evidence

Use the most recent 4 completed weeks when available:

- planned versus completed outcomes
- partial completion and deliberate de-scoping
- carryover and repeated skips
- calendar density and fragmented days
- travel, on-call, non-work blocks, and evening commitments
- health/energy signals only when relevant and sufficiently supported

Favor recent weeks. Record missing history rather than manufacturing precision.

## Deterministic helper

Run:

```sh
python3 scripts/capacity.py assess --input capacity-input.json
```

The input contains `history` and `upcoming`; run `--example` for the schema. Treat the result as a recommendation. Put its band, suggested outcome count, factors, and evidence summary in agent context.

## Interaction

In attended weekly mode, state the predicted band and recommendation before choosing outcomes. If Micah wants more, identify what must be shrunk, swapped, or accepted as risk. Do not prevent an explicit override.

At the next weekly review, compare prediction to outcome. Do not infer chronic incapacity from isolated hard weeks.
