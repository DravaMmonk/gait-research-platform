# Gait Research Platform MVP

Research-oriented platform for gait motion representation experiments. The MVP ships a configuration-driven pipeline, a velocity-based signal builder, a temporal CNN embedding model, a contrastive training experiment, embedding visualization, and a basic AI agent layer.

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

Set environment variables:

```bash
export OPENAI_API_KEY=...
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_MODEL=gpt-4o-mini
```

Use the Python API:

```python
from gait_research_platform.agents.experiment_agent import ExperimentAgent
from gait_research_platform.core.config_loader import load_config

base_config = load_config("gait_research_platform/configs/experiments/contrastive.yaml")
agent = ExperimentAgent(base_config)

configs = agent.plan(goal="Explore larger embeddings for velocity-based gait representation")
saved = agent.save_generated_plan(configs[0], name="velocity_embedding_search")
result = agent.run(configs[0])
review = agent.review({
    "experiment_id": result["experiment_id"],
    "status": "success",
    "metrics": result["metrics"],
})
print(saved, review)
```

The agent boundary is intentionally narrow in the MVP:

- it can generate YAML-compatible configs
- it can run experiments
- it can read results and propose next experiments
- it does not edit source code

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
