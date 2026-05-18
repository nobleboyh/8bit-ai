# Story 1.4: Layout Shell, Control Panel & Viewer Shell

Status: done

## Story

As a user,
I want to see the app layout with the prompt input, example chips, and empty viewer state,
So that I understand the workflow and can enter my character concept.

## Acceptance Criteria

1. **Given** the app loads, **When** I view the page, **Then** the header displays "PIXELFORGE" title and "8-BIT AVATAR GENERATOR" subtitle in Press Start 2P, **And** there are 3 numbered sections: "01 // CONFIG", "02 // PROMPT", "03 // AVATAR", **And** each section has a 3px solid border with 24px padding.

2. **Given** the prompt section is visible, **When** I see the textarea, **Then** it has placeholder text suggesting an avatar description, **And** the "FORGE" button is prominent with `.btn-primary` styling, **And** 6 example chips are displayed: Wizard, Knight, Robot, Astronaut, Ninja, Elf, **When** I click an example chip, **Then** the textarea is filled with the corresponding prompt text.

3. **Given** the viewer section is visible and no avatar has been generated, **When** I see the viewer, **Then** the empty state shows a pixel icon (U+25A3) and "ENTER A PROMPT & FORGE YOUR PIXEL" text, **And** the viewer has min-height of 320px on desktop.

4. **Given** the viewport is ≤600px wide, **When** the page renders, **Then** section padding reduces to 16px, **And** action rows stack vertically, **And** viewer min-height is 240px.

5. **Given** the viewport is ≤360px wide, **When** the page renders, **Then** section padding reduces to 8px, **And** chip text sizes are smaller.

## Tasks / Subtasks

- [x] Create `App.tsx` layout shell
  - [x] Header with "PIXELFORGE" title and "8-BIT AVATAR GENERATOR" subtitle
  - [x] Three numbered sections: "01 // CONFIG", "02 // PROMPT", "03 // AVATAR"
  - [x] Section container with 3px solid border, 24px padding, `--border` colour
  - [x] Container max-width 720px, centered
  - [x] Section gap: 24px
  - [x] ThemeToggle mounted in header area
  - [x] Wire up ApiKeyInput + ProviderSelect in CONFIG section
- [x] Create `ControlPanel` component
  - [x] File: `src/components/ControlPanel/ControlPanel.tsx`
  - [x] CSS module: `src/components/ControlPanel/ControlPanel.module.css`
  - [x] Test: `src/components/ControlPanel/ControlPanel.test.tsx`
  - [x] Textarea with placeholder: "Describe your character... e.g. A wise old wizard with a sparkling staff"
  - [x] "FORGE" button with `.btn-primary` styling
  - [x] Disabled state for FORGE button (opacity 0.4, not-allowed)
  - [x] FORGE button disabled when textarea empty or API key missing
  - [x] Cmd/Ctrl+Enter keyboard shortcut triggers generate
  - [x] 6 example chips: Wizard, Knight, Robot, Astronaut, Ninja, Elf
  - [x] Chip hover: accent border + text highlight
  - [x] Chip click fills textarea with preset prompt text
  - [x] Action rows: `.generate-row`, `.examples-row` for layout
  - [x] Generate row: textarea + FORGE button side by side on desktop
- [x] Create example chip presets
  - [x] Wizard: "A wise old wizard with a long flowing beard, wearing deep blue robes adorned with golden crescent moons, holding a sparkling staff"
  - [x] Knight: "A valiant knight in shining silver armor with a crimson cape, wielding a broadsword, standing ready for battle"
  - [x] Robot: "A sleek chrome robot with glowing blue optic sensors, exposed circuitry, and mechanical joints"
  - [x] Astronaut: "A modern astronaut in a white space suit with a gold-visored helmet, floating against a starfield"
  - [x] Ninja: "A shadowy ninja in dark grey attire, face partially covered, poised in a stealthy combat stance"
  - [x] Elf: "A mystical forest elf with pointed ears wearing earthy green and brown leather, bow slung across back"
- [x] Create empty viewer state
  - [x] Viewer container with min-height 320px (desktop)
  - [x] Black background, 4px border, 8px 8px offset shadow (`--shadow`)
  - [x] Centered empty state: large pixel icon U+25A3 in `--muted` colour
  - [x] Instructional text: "ENTER A PROMPT & FORGE YOUR PIXEL" in `--font-display`, `--muted` colour
  - [x] `image-rendering: pixelated` on container
- [x] Implement responsive design
  - [x] `@media (max-width: 600px)`: section padding → 16px, action rows stack vertical, viewer min-height → 240px
  - [x] `@media (max-width: 360px)`: section padding → 8px, smaller chip text
  - [x] Use `clamp()` for fluid font sizing
- [x] Write tests
  - [x] ControlPanel: renders textarea, FORGE button, 6 chips
  - [x] ControlPanel: clicking chip fills textarea
  - [x] ControlPanel: FORGE button disabled when textarea empty
  - [x] ControlPanel: Cmd/Ctrl+Enter triggers generate callback
  - [x] Viewer: shows empty state with icon and instructional text
  - [x] Section containers: correct border, padding, gap styles

## Dev Notes

### State Flow Architecture

```
App.tsx (owns: apiKey, prompt, theme, config, error, loading)
├── Header
│   └── ThemeToggle (theme, toggleTheme)
├── Section "01 // CONFIG"
│   ├── ApiKeyInput (apiKey, setApiKey)
│   ├── ProviderSelect (provider, setProvider)
│   ├── Api URL input (apiUrl, setApiUrl)
│   └── Model input (model, setModel)
├── Section "02 // PROMPT"
│   └── ControlPanel (prompt, setPrompt, onGenerate, disabled, chips)
└── Section "03 // AVATAR"
    └── ViewerShell (state, pixelMap, loading, error)
```

- Config section mounts components created in Story 1.3
- ControlPanel takes `onGenerate` callback from App.tsx
- Viewer shell is an empty container with 4 mutually exclusive states (empty is current)
- Other viewer states (loading, result, error) created in Epic 2

### Component Props Interface

```typescript
// ControlPanel
interface ControlPanelProps {
  prompt: string;
  onPromptChange: (value: string) => void;
  onGenerate: () => void;
  isGenerating: boolean;
  hasApiKey: boolean;
}
```

### CSS Structuring for Sections

```css
.container {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px;
}

.section {
  border: 3px solid var(--border);
  padding: 24px;
  margin-bottom: 24px;
}

.section-label {
  font-family: var(--font-display);
  font-size: 10px;
  color: var(--muted);
  margin-bottom: 14px;
}
```

### Viewer Empty State

```html
<div class="viewer viewer-empty">
  <div class="viewer-icon">▣</div>
  <p class="viewer-text">ENTER A PROMPT & FORGE YOUR PIXEL</p>
</div>
```

```css
.viewer {
  background: #000;
  border: 4px solid var(--border);
  box-shadow: 8px 8px 0 var(--shadow);
  min-height: 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  image-rendering: pixelated;
}

.viewer-icon {
  font-size: 48px;
  color: var(--muted);
}
```

### Architecture Compliance

- State managed via React hooks + Context API — no external state libraries
- All components in `src/components/[Name]/` with co-located CSS module + tests
- Named exports only (no `export default`)
- Imports via `@/` path alias
- CSS custom properties for all visual tokens
- `data-theme` attribute drives theme switching via custom properties
- Responsive at 600px and 360px breakpoints

### File Structure

```
src/
├── App.tsx                              # Root component: layout, state orchestration
├── App.module.css                       # Layout styles: container, sections, header
├── components/
│   ├── ControlPanel/
│   │   ├── ControlPanel.tsx             # Textarea, forge button, example chips
│   │   ├── ControlPanel.module.css
│   │   └── ControlPanel.test.tsx
│   └── ... (ThemeToggle, ApiKeyInput, ProviderSelect from previous stories)
├── hooks/
│   └── ... (useTheme, useApiKey from previous stories)
├── types/
│   └── pixelmap.ts
```

### Testing Requirements

- Vitest + React Testing Library
- ControlPanel tests: render, chip click, button disabled state, keyboard shortcut
- Layout tests: sections render with correct labels
- Viewer empty state: icon and text present
- Responsive testing via jsdom viewport resize (if possible) or manual verification note

## File List

- `src/App.tsx` — Full layout shell with header, 3 sections, state orchestration
- `src/App.module.css` — Added header, title, subtitle, section, field styles; responsive breakpoints
- `src/components/ControlPanel/ControlPanel.tsx` — Textarea, FORGE button, 6 example chips
- `src/components/ControlPanel/ControlPanel.module.css` — Action row layout, chip/button styles, responsive
- `src/components/ControlPanel/ControlPanel.test.tsx` — ControlPanel tests (9)
- `src/components/ViewerShell/ViewerShell.tsx` — Empty viewer state component
- `src/components/ViewerShell/ViewerShell.module.css` — Viewer container, icon, responsive min-height
- `src/components/ViewerShell/ViewerShell.test.tsx` — ViewerShell tests (2)

## Change Log

- 2026-05-18: Implemented layout shell with header, 3 sections, ControlPanel with example chips and FORGE button, ViewerShell with empty state, responsive design for 600px and 360px breakpoints

## Dev Agent Record

**Implementation Notes:**
- App.tsx owns all state (apiKey, prompt, isGenerating, config)
- ControlPanel handles prompt input, chip selection, keyboard shortcut (Cmd/Ctrl+Enter)
- FORGE button disabled when textarea empty, API key missing, or generation in progress
- ViewerShell implements empty state with U+25A3 icon and instructional text
- Responsive: section padding 24px→16px→8px; viewer 320px→240px; action rows stack vertically
- All 11 tests (9 ControlPanel + 2 ViewerShell) passing

## References

- [Epics: Story 1.4](epics.md#L233-L269) — Full acceptance criteria
- [Epics: UX-DR5, UX-DR7, UX-DR8, UX-DR9, UX-DR10, UX-DR13, UX-DR16](epics.md#L65-L81) — UX requirements
- [Architecture: Component Tree](architecture.md#L120) — App.tsx orchestrates all components
- [Architecture: State Flow](architecture.md#L180-L183) — App.tsx owns all state
- [Architecture: Project Structure](architecture.md#L206-L268) — File organization
- [UX: Section Layout](ux-design-specification.md#L244-L249) — Spacing, borders, gaps
- [UX: Avatar Viewer States](ux-design-specification.md#L337-L339) — Empty state design
- [UX: Action Rows](ux-design-specification.md#L345-L348) — Layout helpers
- [UX: Responsive Breakpoints](ux-design-specification.md#L388-L392) — 600px and 360px
- [UX: Empty State](ux-design-specification.md#L363) — Instructional text
- [UX: Example Chips](ux-design-specification.md#L332-L336) — Chip component spec
