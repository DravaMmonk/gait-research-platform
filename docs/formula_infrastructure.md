# Formula Infrastructure

## Intent

This stage prepares the platform to host an AI-assisted formula factory without implementing formula proposal quality, DSL parsing, or human workflow logic yet.

## Prepared Infrastructure

- formula definition metadata
- formula proposal metadata
- formula evaluation metadata
- formula review metadata
- staged execution plans on runs
- review verdict enums and evidence bundle contracts
- research tool runner integration

## Compute Boundary

`research_tools` is the approved compute toolkit boundary for reusable research capabilities.

Its contract remains:

- local file input
- JSON artifact output
- explicit config only
- no platform runtime coupling

The platform wraps this toolkit through a tool runner adapter rather than duplicating gait compute logic.

## What Is Ready

- schema and repository contracts for formula lifecycle records
- API scaffold for create/list/get style infrastructure operations
- worker/runtime support for staged execution plans
- formula evaluation run kind support

## What Is Not Implemented Yet

- formula DSL
- AI proposal quality logic
- automatic formula scoring
- full review interface
- clinician-facing validation flows

## Migration Direction

Future formula work should:

1. build on the existing formula records
2. reuse `research_tools` where possible
3. route execution through staged runs
4. keep human validation as a first-class audit surface
5. standardize symbolic search on PySR as the core engine while preserving module isolation from orchestration and persistence concerns
