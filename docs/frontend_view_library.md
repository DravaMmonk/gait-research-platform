# Frontend View Library

## Purpose

The hidden `/dev` route in `frontend/research_console` is an internal view library for two things:

- controlled frontend visual modules
- backend agent tool contracts

It is not a second product surface and it does not execute live workflows.

The page follows the same design standard as the public console and the broader `hf-playground` frontend. That standard is inherited from `hf-analytics/clinician_side`, including its token structure, card language, badge treatment, and layout-stability rules.

## Design Rationale

The public route at `/` should stay focused on the end-user chat workflow. Development references still need a place to validate rendering contracts, visual consistency, and tool metadata. The hidden `/dev` route satisfies that need without leaking preview content into the public shell.

The route uses the same visual language as the public chat surface:

- shared tokens from `app/globals.css`
- the same panel, badge, border, and typography rules
- fixed shell with internal scrolling
- the `hf-analytics clinician_side` card and header rhythm

## Data Model

The `/dev` route is driven by a typed registry in `frontend/research_console/lib/view-library.ts`.

It contains two entry families:

1. `ModuleLibraryEntry`
   - reuses the existing `VisualModule` union
   - keeps a module example close to the production rendering contract
2. `ToolLibraryEntry`
   - mirrors the tool registry from `hound_forward/agent_tools/executor.py`
   - exposes purpose, input kind, output kind, artifact name, and static example payloads

This structure keeps the page data-driven and avoids page-local mock assembly.

## Rendering Structure

The `/dev` route is split into a sidebar and a detail pane.

The sidebar provides:

- section switching between modules and tools
- search
- category filtering
- tag filtering
- entry selection

The detail pane renders:

- module examples through `ModuleRenderer`
- tool examples through `ToolExampleRenderer`
- shared metadata and JSON primitives through `view-library-primitives.tsx`

## Reuse Strategy

The view library intentionally reuses existing rendering code where possible:

- `ModuleRenderer` remains the single renderer for visual modules
- shared metadata, tags, and code blocks are handled by common view-library primitives
- no preview-only fork of the module components is introduced

This keeps the reference surface close to the product implementation and reduces drift.

## Hidden Route Policy

The `/dev` route should remain:

- hidden from the homepage
- free of public navigation links
- static and non-executable
- suitable for design and implementation review only
