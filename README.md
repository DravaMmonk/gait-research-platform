# Gait Research Platform MVP

Research-oriented platform for gait motion representation experiments. The MVP ships a configuration-driven pipeline, a velocity-based signal builder, a temporal CNN embedding model, a contrastive training experiment, embedding visualization, and a bounded AI agent orchestration layer.

## Structure

`gait_research_platform/` contains six primary layers:

- `core`: config loading, registries, storage helpers
- `signals`: motion feature builders
- `representations`: trainable embedding models
- `experiments`: executable pipelines
- `analysis`: post-hoc analysis tasks
- `agents`: experiment planning and execution helpers

Repository governance and research workflow conventions are documented in:

- [docs/engineering_principles.md](/Users/drava/Documents/Hound/hf-playground/docs/engineering_principles.md)
- [docs/github_research_workflow.md](/Users/drava/Documents/Hound/hf-playground/docs/github_research_workflow.md)
- [docs/agent_architecture.md](/Users/drava/Documents/Hound/hf-playground/docs/agent_architecture.md)

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

For OpenAI-compatible agent support:

```bash
pip install -e .[agent]
```

## Generate toy pose data

```bash
python3 -c "from gait_research_platform.data.sample_pose_dataset import generate_sample_pose_dataset; generate_sample_pose_dataset('gait_research_platform/data/poses')"
```

## Run the MVP experiment

```bash
python3 -m gait_research_platform.pipeline.run_experiment \
  --config gait_research_platform/configs/experiments/contrastive.yaml \
  --print-result
```

Results are stored in:

- `gait_research_platform/results/{experiment_id}/`
- `gait_research_platform/results/manifest.jsonl`

Each manifest entry records the experiment id, timestamp, config path, status, and Git metadata when the repo is under version control.

## AI Agent integration

The agent is intentionally limited to:

- generate experiment configs
- request and run approved experiments
- review results and recommend the next config-safe step

The agent does not:

- edit source code
- run Git operations
- preprocess datasets
- manipulate large datasets directly

Set environment variables:

```bash
export OPENAI_API_KEY=...
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_MODEL=gpt-4o-mini
```

Compatible backends include any OpenAI-compatible endpoint, such as OpenAI, Ollama, vLLM, and compatible gateways.

Use the Python API:

```python
from gait_research_platform.agents.experiment_agent import ExperimentAgent
from gait_research_platform.agents.llm_client import OpenAICompatibleClient
from gait_research_platform.core.config_loader import load_config

base_config = load_config("gait_research_platform/configs/experiments/contrastive.yaml")
agent = ExperimentAgent(
    base_config,
    llm_client=OpenAICompatibleClient(),
)

configs = agent.plan(
    goal="Explore larger embeddings for velocity-based gait representation",
    allowed_signals=["velocity_signal", "pose_signal"],
    allowed_representations=["temporal_embedding"],
    use_llm=True,
    num_candidates=2,
)
saved = agent.save_generated_plan(configs[0], name="velocity_embedding_search")
run_request = agent.request_run(configs[0])
result = agent.run(run_request, approved=True)
review = agent.review(result)
print(saved, review)
```

Operator CLI is available as a thin wrapper around the same Python API:

```bash
python -m gait_research_platform.agents.agent_loop \
  --base-config gait_research_platform/configs/experiments/contrastive.yaml \
  plan --goal "Learn stable gait embeddings from velocity signals"
```

You can connect an OpenAI-compatible model either through environment variables or directly through CLI flags:

```bash
python -m gait_research_platform.agents.agent_loop \
  --base-config gait_research_platform/configs/experiments/contrastive.yaml \
  --api-key "YOUR_OPENAI_TOKEN" \
  --base-url "https://api.openai.com/v1" \
  --model "gpt-4o-mini" \
  plan --goal "Learn stable gait embeddings from velocity signals" --use-llm
```

```bash
python -m gait_research_platform.agents.agent_loop \
  --base-config gait_research_platform/configs/experiments/contrastive.yaml \
  run --config gait_research_platform/configs/experiments/contrastive.yaml --approve
```

```bash
python -m gait_research_platform.agents.agent_loop \
  --base-config gait_research_platform/configs/experiments/contrastive.yaml \
  review --experiment-id YOUR_EXPERIMENT_ID
```

## Result and error artifacts

Every run creates a result directory with an auditable artifact surface:

- `config.yaml`
- `logs.txt`
- `metrics.json`
- `summary.json`
- `error.json`
- `plots/`
- `artifacts/`

Structured experiment results follow this shape:

```json
{
  "experiment_id": "20260310_123456_abcd1234",
  "status": "success",
  "result_dir": "...",
  "metrics": {
    "final_loss": 0.42,
    "num_sequences": 6,
    "embedding_dim": 64
  },
  "summary": {
    "experiment_id": "20260310_123456_abcd1234",
    "status": "success"
  },
  "error": null
}
```

Failed runs do not crash the agent boundary. They return a structured error payload:

```json
{
  "experiment_id": "20260310_123500_deadbeef",
  "status": "failed",
  "result_dir": "...",
  "metrics": null,
  "summary": {
    "experiment_id": "20260310_123500_deadbeef",
    "status": "failed"
  },
  "error": {
    "type": "FileNotFoundError",
    "message": "Pose file missing for video 'sample_00'. No pose extractor configured. Add parquet pose files or register a PoseExtractor.",
    "traceback": null,
    "stage": "signal"
  }
}
```

Set `DEBUG_AGENT=true` to include traceback details in `error.json` and returned error payloads.

## Default env layout

- pose parquet: `gait_research_platform/data/poses/*.parquet`
- cached signals: `gait_research_platform/data/signals/*.parquet`
- exported embeddings: `gait_research_platform/data/embeddings/*.parquet`
- experiment outputs: `gait_research_platform/results/{experiment_id}/`

## Extending the platform

- Add new signals by subclassing `Signal` and registering with `@register_signal(...)`
- Add new models by subclassing `RepresentationModel`
- Add new experiments by subclassing `Experiment`
- Add new analyses by subclassing `AnalysisTask`
- Add a real `PoseExtractor` and register it in the pose extractor registry
