# Story FEAT-002.1.1: buildAvatarHTML Pure Function

Status: review

## Story

As a developer,
I want a pure function `buildAvatarHTML(grid, label, prefix, username)` that produces a complete, self-contained HTML string from pixel map data,
so that the export logic is testable, isolated from the DOM, and guaranteed free of API key leakage.

## Acceptance Criteria

**AC1: Valid HTML document structure**
- Given a valid pixel map with grid, label, prefix, and username
- When `buildAvatarHTML(grid, label, prefix, username)` is called
- Then it returns a string starting with `<!DOCTYPE html>` and containing `<html lang="en">`
- And the returned string includes `<meta charset="UTF-8">` and `<meta name="viewport">`
- And the `<title>` is `"[prefix] [username] — Pixelforce Avatar"`

**AC2: Self-contained (no external dependencies)**
- Given any valid inputs
- When the HTML string is generated
- Then it contains no `<script>` tags
- And it contains no `<link>` or `<img>` tags referencing external URLs
- And all CSS is inlined within a single `<style>` block inside `<head>`

**AC3: Pure function — deterministic output**
- Given the same grid, label, prefix, and username inputs
- When `buildAvatarHTML` is called twice with identical arguments
- Then both return values are identical strings

**AC4: No API key leakage**
- Given a call to `buildAvatarHTML`
- When I inspect the returned string for the user's API key value
- Then no match is found
- And no match is found for common API key patterns (`sk-`, `r8_`, `sk-ant-`)

**AC5: Pixel grid rendering with inline styles**
- Given a 16×16 or 32×32 pixel grid
- When the HTML is generated
- Then every grid cell in the avatar section has an inline `style="background:#RRGGBB"` attribute
- And no cell uses a `class` attribute for its background colour
- And the grid dimensions match `grid.length × grid[0].length`
- And each cell colour matches the corresponding hex value from the input grid

**AC6: Visual layout correctness**
- Given a fixed light background is used for the exported page
- When the HTML is rendered
- Then the avatar grid cells use the exact colours from the input grid
- And the label text is displayed beneath the avatar grid
- And no `class` attributes are used for styling grid cells
- And the grid layout (CSS Grid) produces a visually identical result to the in-app rendering

**AC7: File size constraint**
- Given a typical 32×32 avatar with palette
- When `buildAvatarHTML` generates the output
- Then the resulting HTML file size is under 50 KB

## Tasks / Subtasks

- [x] Create `src/utils/buildAvatarHTML.ts` with named export (AC: 1-7)
  - [x] Implement HTML template with `<!DOCTYPE html>`, meta tags, title
  - [x] Generate inline `<style>` block with CSS Grid styling for the avatar grid + label
  - [x] Render grid cells as `<div>` elements with inline `style="background:#RRGGBB"`
  - [x] Apply fixed light background (per decision log: no theme switching in export)
  - [x] Display label text beneath the grid
  - [x] Verify no `<script>` tags, no external `<link>`/`<img>` references
- [x] Create `src/utils/buildAvatarHTML.test.ts` (AC: 1-7)
  - [x] Test valid HTML document structure (DOCTYPE, html, meta, title)
  - [x] Test self-containment (no script/link/img external tags)
  - [x] Test pure function determinism (same inputs → same output)
  - [x] Test API key absence (grep for key value and common patterns)
  - [x] Test inline style rendering (every cell has `style="background:#..."`, no class for colour)
  - [x] Test grid dimension match
  - [x] Test file size under 50 KB for 32×32 grid
  - [x] Test light background and label display

## Dev Notes

### Architecture Compliance

- **File location:** `src/utils/buildAvatarHTML.ts` — named export, consistent with existing `pngExport.ts` pattern (see `architecture.md:265-268`)
- **No external state:** Function uses only its four parameters; no closure references to `apiKey`, `localStorage`, `App.tsx`, or any other state
- **Signature:** `buildAvatarHTML(grid: string[][], label: string, prefix: string, username: string): string`
- **Named export only:** Follow `src/types/pixelmap.ts:62-64` `Result<T,E>` pattern conventions
- **Import via `@/` path aliases** per `architecture.md:164`
- **CSS Grid** over `<table>` per decision log entry 3 — cleaner, smaller output
- **Fixed light background** per decision log entry 5 — most portable across browsers
- **No footer** — "Made with PixelForge" excluded per decision log entry 4

### Grid rendering details

The exported HTML uses CSS Grid layout with `div` cells. Each cell has inline `style="background:#RRGGBB"`. The grid container uses:
- `display: grid`
- `grid-template-columns: repeat(N, 1fr)` where N = `grid.length`
- No gap between cells (pixel-perfect)

The light background is `#f5e6c8` (matching the app's light theme warm parchment tone per `ux-design-specification.md:227-228`), or a simple `#ffffff` for maximum clarity.

### HTML template structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[prefix] [username] — Pixelforce Avatar</title>
  <style>
    /* Inline CSS for grid and label, no external references */
  </style>
</head>
<body>
  <!-- Grid of divs with inline style="background:#RRGGBB" -->
  <!-- Label text below grid -->
</body>
</html>
```

### Testing approach

- Co-locate `buildAvatarHTML.test.ts` next to source (per `architecture.md:162`)
- Use Vitest (existing in project)
- Pure function testing is straightforward — no DOM mocking needed (unlike `pngExport.test.ts` which requires browser API stubs)
- Test the returned string directly with string assertions (`includes()`, regex, etc.)
- Reference existing `pngExport.test.ts` for project test conventions

## Dev Agent Record

### Completion Notes

- Implemented `buildAvatarHTML` pure function at `src/utils/buildAvatarHTML.ts`
  - Generates complete self-contained HTML document from pixel map data
  - CSS Grid layout with inline `style="background:#RRGGBB"` per cell
  - No `<script>` tags, no external dependencies
  - Fixed light background `#f5e6c8`
  - Label text displayed beneath grid
  - HTML escaping for label/prefix/username to prevent injection
- Created comprehensive test suite at `src/utils/buildAvatarHTML.test.ts` — 18 tests passing
  - Validates HTML structure, self-containment, determinism, no API key patterns
  - Validates inline style rendering, grid dimensions, file size < 50 KB
- Updated story file: all tasks marked complete, status set to "review"

## File List

- `src/utils/buildAvatarHTML.ts` — new, named export pure function
- `src/utils/buildAvatarHTML.test.ts` — new, 18 tests

## Change Log

- 2026-05-18: Implemented buildAvatarHTML function and test suite
