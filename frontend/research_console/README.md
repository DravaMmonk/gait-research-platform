# Research Console Frontend

## Design Goals

The frontend keeps the Hound Forward research visual language while reducing page-level coupling:

- Inter for interface copy and JetBrains Mono for technical payloads
- olive primary accents, warm neutral surfaces, restrained radii, light borders, and soft shadows
- chat-first product structure on `/`
- hidden contract reference surface on `/dev`
- reusable primitives over page-specific class systems

## Architecture

The frontend is organized in four layers:

1. `app/`
   - route entry points and global theme tokens
   - minimal global CSS limited to base tokens and third-party styling seams
2. `components/ui/`
   - `shadcn/ui`-style low-level primitives
   - buttons, inputs, select, scroll area, badge, card, separator, and panel
3. `components/console/` and `components/dev/`
   - feature-level shells and product composition
   - session sidebar, chat frame, module renderer, and view library surfaces
4. `lib/` and `hooks/`
   - typed contracts, session helpers, persistence, network clients, and view registries

## Console Split

The Research Console is intentionally decomposed:

- `hooks/use-console-sessions.ts`
  owns session fetching, creation, archive state, persistence, and derived view state
- `components/console/console-sidebar.tsx`
  owns session navigation and archive controls
- `components/console/console-chat-frame.tsx`
  owns topbar, context strip, and loading shell
- `components/console/copilot-session-chat.tsx`
  owns the CopilotKit integration boundary
- `components/console/module-renderer.tsx`
  remains the single renderer for typed visual module contracts

## Styling Rules

- Do not add new page-local CSS classes for normal layout or component styling when the same result can be achieved with shared primitives and Tailwind utilities.
- Keep global CSS scoped to theme tokens, browser/base rules, and `CopilotKit` override selectors.
- Reuse `Panel`, `Badge`, `Button`, `Input`, `Select`, and `ScrollArea` before introducing new abstractions.
- Preserve width-safe rendering for all long-form content, IDs, code, formulas, and JSON payloads.
- Keep `/dev` visually aligned with `/` and avoid preview-only styling forks.
