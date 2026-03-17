# Frontend Design Spec

## Purpose

This document defines the source of truth for the `frontend/research_console` application shell and the hidden `/dev` reference surface.

The product is a chat-first agent console, not a generic dashboard and not a free-form chatbot. The public surface is the single chat route at `/`. The hidden `/dev` route is an internal reference library for controlled visual modules and backend tool contracts.

The base design language for all `hf-playground` frontend surfaces is inherited from `hf-analytics/clinician_side`. New pages should treat that language as the default product standard unless there is an explicit reason to diverge.

## Product Model

The research console follows this pattern:

- agent-centric orchestration
- controlled rendering contracts
- schema-based display surfaces
- evidence-aware framing
- hidden internal reference tooling

The agent interprets user intent and returns a response through the existing chat interface. The frontend uses predefined rendering contracts for modules and supporting metadata. The `/dev` library documents those contracts without becoming a second product surface.

## Core UX Principles

### 1. Chat-first entry

- The primary product home is the research console.
- The conversation thread is the only public entry point.
- The homepage must stay simple, direct, and end-user-facing.

### 2. Controlled module rendering

- The frontend must not accept arbitrary generated UI.
- The agent may choose modules, not author React or HTML.
- Every module type must map to a prebuilt component.

### 3. Evidence-aware output

- Important analytical output must carry provenance.
- Module contracts should preserve metric definition, review status, and supporting references.
- Long formulas, IDs, paths, and JSON payloads must remain width-safe.

### 4. Stable operational shell

- The shell should feel like a professional research application, not a marketing page.
- The public chat surface and the hidden `/dev` surface must share the same tokens, spacing, type scale, and panel language.
- Dynamic content must scroll inside fixed containers rather than stretching the page shell.

### 5. Shared primitives over page-local styling

- Shared shell, panel, badge, and metadata primitives should be reused across the homepage and `/dev`.
- `/dev` must reuse the same visual language as the public chat route rather than introducing preview-only styling.

## Public Surface

The public application surface is intentionally narrow:

- route: `/`
- function: chat with the agent
- styling: neutral research tone with olive primary accents
- layout: fixed shell with internal message scrolling
- navigation: no public link to `/dev`

The public UI should not expose mock galleries, dashboard leftovers, or developer preview content.

## Hidden Developer Surface

The `/dev` route is a hidden internal reference library. It exists for implementation validation and design-system continuity, not for end users.

The `/dev` route must:

- stay manually accessible only
- present both frontend visual modules and backend agent tools
- be data-driven through a shared typed registry
- remain non-executable and non-networked
- use the same tokens and shell language as `/`

## View Library Architecture

The `/dev` library is organized into two sections:

1. `Visual Modules`
   - typed examples based on the `VisualModule` union
   - rendered through the same `ModuleRenderer` used by product surfaces
2. `Agent Tools`
   - static contract previews that mirror `hound_forward/agent_tools/executor.py`
   - example input and output payloads for reference only

The page should support:

- section switching
- search
- category filtering
- tag filtering
- detail selection
- width-safe rendering of structured payloads

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

The module registry used by `/dev` must reuse these contracts directly rather than inventing a second preview schema.

## Tool Contract Library

The tool library should mirror the executor-backed registry in `hound_forward/agent_tools/executor.py`.

Each tool entry should expose:

- tool name
- purpose
- input kind
- output kind
- output artifact name
- frontend-safe example input payload
- frontend-safe example output payload
- source module path

The tool library is a reference view, not a live execution console.

## Evidence And Stability Requirements

Every clinically relevant or research-critical module should preserve enough context to answer:

- what metric is this
- what formula or definition produced it
- what source run, session, or asset supports it
- what review state or confidence applies

## Styling Direction

- Use the `hf-analytics clinician_side` token model as the default source of truth
- Keep the HSL token system aligned with `background`, `foreground`, `card`, `muted`, `border`, `primary`, and `ring`
- Use Inter for sans text and JetBrains Mono for code-like payloads
- Keep a neutral research visual tone
- Use olive green as the primary active accent
- Prefer dense but readable panels over oversized decorative cards
- Prefer low-radius cards, light borders, and light shadows over glass effects or oversized radii
- Reuse the shared layout-stability utilities from `hf-analytics`, especially `ui-stable-*`

The previous serif-heavy hero scaffold is retired and should not be reintroduced.

## Implementation Notes

- Keep module examples in a shared typed registry
- Mirror tool metadata from the backend executor contract
- Reuse existing renderers and shared primitives instead of introducing preview-only forks
- Avoid page-local hardcoded preview composition
- Keep `/dev` hidden and non-executable

## Review Checklist

- Does `/` remain a clean end-user chat surface?
- Does `/dev` stay hidden from the public UI?
- Are modules rendered from the `VisualModule` contract rather than a separate preview shape?
- Are tool entries aligned with `hound_forward/agent_tools/executor.py`?
- Do search, filters, and selection work without layout breakage?
- Do long formulas, paths, IDs, JSON payloads, and notes stay inside their containers?
