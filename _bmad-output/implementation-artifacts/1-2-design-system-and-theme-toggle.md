# Story 1.2: Design System & Theme Toggle

Status: done

## Story

As a user,
I want the app to have a retro NES-inspired visual theme with a dark/light toggle that persists,
So that the interface feels authentic and comfortable for my preference.

## Acceptance Criteria

1. **Given** the app loads for the first time, **When** the page renders, **Then** the `data-theme` attribute on `<html>` is set to `"light"` by default, **And** the body background uses the light theme `--bg` colour (`#f5e6c8`), **And** the Press Start 2P font is loaded from Google Fonts and applied to `--font-display`.

2. **Given** the light theme is active, **When** I click the theme toggle button, **Then** `data-theme` changes to `"dark"`, **And** all CSS custom properties switch to dark theme values (navy `--bg`, gold `--accent`), **And** the toggle button text changes to "LIGHT", **And** the preference is saved to `localStorage` under key `pixelforge-theme`.

3. **Given** I previously selected dark theme, **When** I refresh the page, **Then** `data-theme` is `"dark"` on load due to localStorage restoration.

4. **Given** any theme is active, **When** I view the page, **Then** a scanline overlay (`repeating-linear-gradient`) is visible on the body background, **And** all interactive elements (inputs, buttons, chips) have `--accent` coloured focus borders, **And** all interactive elements have minimum 44px touch target height.

## Tasks / Subtasks

- [x] Create CSS custom properties for design tokens
  - [x] Define `:root` / `[data-theme="light"]` token values (parchment theme)
  - [x] Define `[data-theme="dark"]` token values (navy CRT theme)
  - [x] Define semantic token variables: `--bg`, `--surface`, `--fg`, `--muted`, `--border`, `--accent`, `--accent-dim`, `--danger`, `--success`, `--scanline`, `--shadow`, `--font-display`, `--font-body`
- [x] Set up Google Fonts
  - [x] Add `<link>` for Press Start 2P in `index.html`
  - [x] Define `--font-display: 'Press Start 2P', monospace` in CSS
  - [x] Define `--font-body: 'Courier New', 'IBM Plex Mono', ui-monospace, monospace`
- [x] Create `useTheme` hook in `src/hooks/useTheme.ts`
  - [x] Read `localStorage.getItem('pixelforge-theme')` on init; default to `"light"`
  - [x] Set `document.documentElement.dataset.theme` on change
  - [x] Persist to `localStorage.setItem('pixelforge-theme', theme)` on toggle
- [x] Create `ThemeToggle` component
  - [x] File: `src/components/ThemeToggle/ThemeToggle.tsx`
  - [x] CSS module: `src/components/ThemeToggle/ThemeToggle.module.css`
  - [x] Test: `src/components/ThemeToggle/ThemeToggle.test.tsx`
  - [x] Button displays current theme label ("DARK" in light mode, "LIGHT" in dark mode)
  - [x] Click toggles between themes
  - [x] Minimum 44px touch target
  - [x] Accent-coloured focus border
  - [x] Hover: accent-dim background + accent border
  - [x] Active: translate 2px 2px
- [x] Add scanline overlay
  - [x] Apply `repeating-linear-gradient` to body/`::after` pseudo-element
  - [x] Light theme: `rgba(0,0,0,0.025)`
  - [x] Dark theme: `rgba(255,255,255,0.015)`
- [x] Add global base styles in `src/App.module.css` or `src/index.css`
  - [x] Body: `--bg` background, `--fg` text, `--font-body` stack
  - [x] Headings/labels: `--font-display` stack, uppercase by convention
  - [x] Inputs/buttons: 2px solid `--border`, accent focus
  - [x] All interactive elements: minimum 44px height
- [x] Write tests
  - [x] ThemeToggle renders with correct initial label
  - [x] Click toggles theme and updates localStorage
  - [x] Theme persists across page reload
  - [x] Scanline overlay is present in both themes

## Dev Notes

### Design Token Values

**Light Theme (`[data-theme="light"]`)**
| Token | Value | Description |
|-------|-------|-------------|
| `--bg` | `#f5e6c8` | Warm parchment background |
| `--surface` | `#faf0dc` | Lighter cream for cards |
| `--fg` | `#2c1810` | Dark brown text |
| `--muted` | `#8b7355` | Brown muted text |
| `--border` | `#d4b896` | Warm tan borders |
| `--accent` | `#d97a3a` | Burnt orange accent |
| `--accent-dim` | `#e8a86a` | Hover/active state |
| `--danger` | `#c0392b` | Red error |
| `--success` | `#27ae60` | Green success |
| `--scanline` | `rgba(0,0,0,0.025)` | Subtle overlay |
| `--shadow` | `rgba(0,0,0,0.2)` | Drop shadow |

**Dark Theme (`[data-theme="dark"]`)**
| Token | Value | Description |
|-------|-------|-------------|
| `--bg` | `#0f0e2e` | Deep navy CRT screen |
| `--surface` | `#1a1a3e` | Slightly lighter navy |
| `--fg` | `#e0e0e0` | Light grey text |
| `--muted` | `#8888aa` | Muted indigo |
| `--border` | `#3a3a6e` | Muted indigo |
| `--accent` | `#fcb84c` | Warm gold |
| `--accent-dim` | `#d4943a` | Hover/active state |
| `--danger` | `#e74c3c` | Red error |
| `--success` | `#2ecc71` | Green success |
| `--scanline` | `rgba(255,255,255,0.015)` | Subtle overlay |
| `--shadow` | `rgba(0,0,0,0.4)` | Drop shadow |

### Scanline Overlay CSS

```css
body::after {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    var(--scanline) 2px,
    var(--scanline) 4px
  );
  pointer-events: none;
  z-index: 9999;
}
```

### Button States CSS

```css
.btn {
  padding: 12px;
  border: 3px solid var(--border);
  background: var(--surface);
  color: var(--fg);
  font-family: var(--font-display);
  font-size: 11px;
  cursor: pointer;
  min-height: 44px;
}
.btn:hover {
  background: var(--accent-dim);
  border-color: var(--accent);
  color: #000;
}
.btn:active {
  transform: translate(2px, 2px);
}
.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}
.btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.btn-primary {
  background: var(--accent);
  color: #000;
  padding: 14px;
}
```

### Architecture Compliance

- Theme via `data-theme` attribute on `<html>` — not class-based
- All theme tokens via CSS custom properties — no hardcoded colours in components
- `useTheme` hook encapsulates localStorage read/write — components use `theme` value + `toggleTheme` callback
- Component in `src/components/ThemeToggle/` with co-located `.module.css` and `.test.tsx`
- Named exports only (no `export default`)
- Imports via `@/` path alias
- Focus-visible outlines for accessibility (WCAG Level A)

### File Structure

```
src/
├── hooks/
│   └── useTheme.ts          # Custom hook for theme state + localStorage
├── components/
│   └── ThemeToggle/
│       ├── ThemeToggle.tsx  # Toggle button component
│       ├── ThemeToggle.module.css
│       └── ThemeToggle.test.tsx
├── App.tsx                  # Mounts ThemeToggle, provides theme to children
├── App.module.css           # Global styles + theme tokens
└── index.css                # (optional) reset + base styles
```

### Testing Requirements

- Use Vitest + React Testing Library
- Mock `localStorage` for persistence tests
- Test `useTheme` hook directly: init, toggle, localStorage read/write, theme attribute on document
- Test `ThemeToggle` component: renders label, click fires toggle callback, button accessible by role
- Tests co-located in `src/components/ThemeToggle/ThemeToggle.test.tsx`

## File List

- `src/hooks/useTheme.ts` — Theme state hook with localStorage persistence
- `src/components/ThemeToggle/ThemeToggle.tsx` — Theme toggle button component
- `src/components/ThemeToggle/ThemeToggle.module.css` — Toggle button styles
- `src/components/ThemeToggle/ThemeToggle.test.tsx` — Toggle component tests (4)
- `src/App.module.css` — Updated with design tokens (light/dark), scanline overlay, base styles
- `src/App.tsx` — Updated to use useTheme hook and mount ThemeToggle
- `index.html` — Added Google Fonts link for Press Start 2P

## Change Log

- 2026-05-18: Implemented design system with CSS custom properties for light/dark themes, Press Start 2P Google Fonts, useTheme hook with localStorage persistence, ThemeToggle component, scanline overlay, and global base styles

## Dev Agent Record

**Implementation Notes:**
- Design tokens defined in `src/App.module.css` as CSS custom properties on `:root` / `[data-theme="light"]` and `[data-theme="dark"]`
- Scanline overlay implemented as `body::after` pseudo-element with `pointer-events: none`
- useTheme hook encapsulates localStorage read/write and `document.documentElement.dataset.theme` updates
- ThemeToggle has 44px min-height, hover/active/focus-visible states
- All 4 ThemeToggle tests passing

## References

- [UX: Design System Foundation](ux-design-specification.md#L147-L182) — Design tokens and theme approach
- [UX: Color System](ux-design-specification.md#L216-L234) — Dark/light palette values
- [UX: Typography](ux-design-specification.md#L236-L240) — Font stack and sizing
- [UX: Scanline Overlay](ux-design-specification.md#L3) — UX-DR3 scanline spec
- [UX: Button Patterns](ux-design-specification.md#L317-L320) — Button states and variants
- [Architecture: CSS Patterns](architecture.md#L185-L188) — Custom properties and scanline
- [Architecture: State Flow](architecture.md#L180-L183) — App.tsx owns theme state
- [Epics: Story 1.2](epics.md#L147-L176) — Full acceptance criteria
- [Epics: UX-DR1 to UX-DR4](epics.md#L65-L68) — Design system requirements
- [PRD: FR-10](prd.md#L141-L147) — Dark/light theme requirement
