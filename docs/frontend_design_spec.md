# Frontend Design Spec

## Purpose

This document defines the source of truth for the `frontend/research_console` redesign.

The console is a chat-first research workspace, not a generic dashboard and not a free-form chatbot. The agent is the main interaction surface, but every result must render through predefined visual modules with stable evidence-aware framing.

## Product Model

The research console follows this pattern:

- agent-centric orchestration
- predefined visual modules
- schema-based rendering
- user-overridable view intent
- evidence-aware display

The agent interprets intent, selects data and presentation modules, and returns a structured response. The frontend renders that response without inventing new layout primitives.

## Core UX Principles

### 1. Chat-first entry

- The primary product home is the research console.
- The conversation thread is the main workspace entry.
- Text responses are only one part of the result surface.

### 2. Controlled module rendering

- The frontend must not accept arbitrary generated UI.
- The agent may choose modules, not author React or HTML.
- Every module type must map to a prebuilt component.

### 3. Evidence-aware output

- Important analytical output must carry provenance.
- Views should expose metric definition, data quality, and review status.
- Evidence must remain visible without forcing users to open a separate audit workflow.

### 4. Stable operational shell

- Use a persistent sidebar and top context bar.
- Keep the main workspace width-stable under long text, formulas, and IDs.
- Dynamic result content must scroll inside its own containers.

### 5. Shared primitives over page-local styling

- All pages reuse the same shell, panel, badge, and metadata primitives.
- Operational pages such as `Experiments`, `Runs`, `Metrics`, and `Datasets` are secondary workspaces inside the same console system.

## Shell Architecture

The shell has three permanent layers:

1. Left sidebar
   - top-level navigation
   - workspace identity
   - console mode summary
2. Top context bar
   - page title
   - short task-oriented description
3. Work surface
   - conversation
   - module result area
   - inspector rail

The shell should feel closer to an engineering or research console than to a landing page.

## Research Console Layout

The main console page contains:

- conversation thread
- structured assistant summary
- fixed view mode tabs
- rendered module stack
- prompt composer
- evidence inspector rail
- tool trace panel
- suggested follow-ups

Fixed view modes:

- `Summary`
- `Chart`
- `Table`
- `Evidence`
- `Video`
- `Formula`

These view modes are user-facing controls over already-returned structured content, not separate ad hoc fetch paths.

## Visual Module Registry

The first controlled module set is:

- `summary_card`
- `trend_chart`
- `metric_table`
- `evidence_panel`
- `formula_explanation_card`
- `video_panel`
- `comparison_cards`

Each module must:

- use a stable payload schema
- declare its supported default view mode
- render inside shared panel primitives
- tolerate long content safely

## Rendering Rules

- `summary_card` and `comparison_cards` belong to summary-oriented views
- `trend_chart` belongs to chart views
- `metric_table` belongs to table views
- `evidence_panel` belongs to evidence views
- `video_panel` belongs to video views
- `formula_explanation_card` belongs to formula views

The frontend may filter the returned module list by active view mode, but it must not mutate module semantics.

## Natural Language Overrides

The system should support both:

- implicit display selection by agent reasoning
- explicit user override through prompt language

Supported examples:

- `show as table`
- `table only`
- `show raw values`
- `open video first`
- `show evidence`
- `plot this`

The frontend should also expose fixed controls so users do not need to learn prompt syntax to switch views.

## Evidence Requirements

Every clinically relevant or research-critical view should expose enough context to answer:

- what metric is this
- what formula or definition produced it
- what time range is covered
- what is the data quality state
- has it been clinician reviewed
- what source run, session, or asset supports it

The inspector rail is the default place for shared evidence context. Module-local evidence details may supplement it.

## Styling Direction

- Use a modern sans stack
- Keep a neutral research visual tone
- Use green as the primary active accent
- Use ember selectively for emphasis, not as the default interface color
- Prefer dense but readable panels over oversized decorative cards

The previous serif-heavy hero scaffold is retired and should not be reintroduced.

## Implementation Notes

- Reuse `recharts` for chart modules
- Keep frontend module selection schema-aligned with backend response types
- Keep mock fixtures typed and close to the API contract
- Avoid page-local hardcoded data structures that bypass the shared response model

## Review Checklist

- Does the console feel like a research workspace rather than a dashboard showcase?
- Can the agent return text plus structured modules in one result surface?
- Are modules selected from a fixed registry rather than generated ad hoc?
- Is evidence context visible and traceable?
- Do long formulas, paths, IDs, and notes stay inside their containers?
- Do `Experiments`, `Runs`, `Metrics`, and `Datasets` still look like part of the same product?
