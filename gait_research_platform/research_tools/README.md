# research_tools

Agent-oriented toolkit for extracting gait research capabilities out of the legacy platform.

## Tool contract
- Each tool exposes `tool(input_path, output_path, config=None) -> dict`.
- Inputs are local files and explicit config only.
- Outputs are JSON artifacts written to caller-provided paths.
- No DB, queue, storage, worker runtime, or pipeline orchestrator dependencies.

## Tools
- `video/decode_video.py`
- `video/sample_frames.py`
- `pose/extract_keypoints.py`
- `gait/detect_direction.py`
- `gait/segment_sections.py`
- `gait/compute_stride.py`
- `gait/compute_gait_metrics.py`
- `reports/generate_report.py`

## Example
```bash
python research_tools/gait/detect_direction.py \
  --input /tmp/keypoints.json \
  --output /tmp/directions.json
```

For tools with secondary inputs, pass JSON config:

```bash
python research_tools/gait/compute_stride.py \
  --input /tmp/keypoints.json \
  --output /tmp/stride_analysis.json \
  --config '{"sections_path":"/tmp/sections.json"}'
```
