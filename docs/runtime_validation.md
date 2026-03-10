# Runtime Validation

## Purpose

This stage validates the platform runtime without pretending that real computer vision or clinical analytics are already connected.

## Labels

- `Dummy`: deterministic orchestration-safe computation
- `Fake`: synthetic payload derived from uploaded video metadata rather than a production CV model
- `Placeholder`: scaffolded component that proves the contract but is not production-ready

## Vertical Slice

The current validated slice is:

```text
upload video
-> create run
-> enqueue job
-> placeholder worker bridge
-> dummy pipeline
-> fake metrics output
-> agent reads metrics
```

## Current Outputs

Each runtime validation run produces:

- `keypoints.json` as fake pose output
- `metrics.json` with fake `stride_length` and `asymmetry_index`
- `report.json` with placeholder summary and notes

These outputs are deterministic for the same uploaded video asset and manifest.

## What Is Not Real Yet

- no production keypoint extractor
- no real gait model
- no clinical scoring logic
- no Azure-backed worker runtime in the local validation loop
- no full research dashboard

## Upgrade Path

Replace the dummy pipeline step-by-step:

1. replace fake keypoint generation with a real extractor
2. replace fake metric generation with real metric engine execution
3. replace the placeholder local worker bridge with an actual worker runtime
4. keep the same run, asset, metric, and tool contracts during the transition
