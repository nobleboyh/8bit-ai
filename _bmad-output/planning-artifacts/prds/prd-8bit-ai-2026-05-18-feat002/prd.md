---
title: PixelForge — HTML Download Export (FEAT-002)
status: final
created: 2026-05-18
updated: 2026-05-18
---

# PRD: PixelForge — HTML Download Export (FEAT-002)
*Hobby project — single-feature extension to the existing PixelForge avatar generator.*

## 0. Document Purpose
This PRD specifies a single feature extension to the PixelForge 8-bit avatar generator: exporting the generated avatar as a self-contained `.html` file that renders offline without any server, API key, or external dependencies. It is for the sole builder/maintainer. This doc builds on the existing FEAT-001 PRD and assumes the FEAT-001 implementation (LLM-based pixel generation, prefix types, username input, CSS grid rendering) is already in place.

## 1. Vision
A user who generates a pixel avatar in PixelForge can download it not only as a PNG image but also as a standalone `.html` file — a portable pixel-art page they can open in any browser, share with anyone, or embed as a digital signature. The exported file is pixel-accurate, entirely self-contained, and contains zero traces of the user's API key.

## 2. Target User

### 2.1 Primary Persona
Same as FEAT-001 — you or anyone who wants a shareable, offline-portable version of their generated pixel avatar.

### 2.2 Jobs To Be Done
- Export a generated avatar as a standalone `.html` file for sharing or offline viewing.
- Keep the API key private — no key leakage into the exported file.
- Produce a lightweight, pixel-accurate export that matches what the app shows.

## 3. Glossary
- **Pixel map** — A JSON object containing `palette` (array of hex colours), `grid` (square 2D array of hex colour strings), and `label` (display name). Produced by the LLM in FEAT-001.
- **Self-contained HTML** — A single `.html` file with all CSS inlined, no external scripts, no CDN references, no JavaScript required to render the avatar.
- **buildAvatarHTML** — The pure function that accepts `(grid, label, prefix, username)` and returns a complete HTML string for export.

## 4. Features

### 4.1 HTML Export
**Description:** A **Download HTML** button is added to the action area alongside the existing **Download PNG** button. When clicked, the app constructs a self-contained HTML string from the current avatar's pixel grid and triggers a browser download. The exported file renders the avatar grid using inline CSS colours with zero JavaScript — just pure HTML + CSS. The user's API key is deliberately stripped and must never appear in the output. Realizes UJ (export avatar as standalone HTML).

**Functional Requirements:**

#### FR-1: Download HTML button
The action area shows a **Download HTML** button alongside **Download PNG** after a successful avatar generation. The button is visually distinct from the PNG button (different label, optionally different style) so users understand the two formats are separate. Both buttons are visible only after generation.

**Consequences (testable):**
- A "DOWNLOAD HTML" button appears in the action row after avatar generation.
- The button is hidden (or disabled) before generation.
- The button label differs from "DOWNLOAD PNG".
- Clicking the button triggers an immediate download with no additional dialogs.

#### FR-2: buildAvatarHTML pure function
A pure function `buildAvatarHTML(grid, label, prefix, username)` returns a complete HTML string representing the current avatar. It takes no references to DOM state, API keys, or external data beyond its parameters.

**Consequences (testable):**
- Function is a pure transformation — same inputs always produce the same HTML string.
- Function uses only its four parameters; no closure references to `apiKey`, `localStorage`, or other state.
- Parameters:
  - `grid` — 2D array of hex colour strings (e.g. `[["#000000", "#A3F2C1", ...], ...]`) matching the pixel map grid.
  - `label` — String displayed beneath the avatar (from the pixel map's `label` field).
  - `prefix` — Avatar type string (e.g. `"Wizard"`, `"Knight"`, etc.).
  - `username` — Character name string entered by the user.

#### FR-3: Self-contained HTML structure
The exported HTML document follows this structure:
- `<!DOCTYPE html>` declaration
- `<html lang="en">` with `<meta charset="UTF-8">` and `<meta name="viewport">`
- `<title>` containing `[prefix] [username] — Pixelforce Avatar`
- Inline `<style>` block with all required CSS
- `<body>` containing the avatar grid and label

**Consequences (testable):**
- Exported file has no `<script>` tags.
- Exported file has no `<link>` or `<img>` tags referencing external URLs.
- Opened offline in Chrome 110+, Firefox 115+, Safari 16+, the avatar renders identically to the in-app view.

#### FR-4: Pixel grid rendering
The avatar grid is rendered as an HTML table or CSS Grid of `<div>` elements. Each cell has an inline `style="background:#RRGGBB"` attribute matching the corresponding grid cell colour. No CSS class names reference external stylesheets. Grid dimensions match the in-app grid (16×16 or 32×32).

**Consequences (testable):**
- Every grid cell has an inline `style` attribute with a valid 6-digit hex colour.
- No `class` attributes are used for styling grid cells.
- Grid structure (CSS Grid or `<table>`) produces an identical visual layout to the in-app render.
- Grid dimensions match the source `grid.length` × `grid[0].length`.

#### FR-5: API key absence
The generated HTML string contains no trace of the user's API key. The `buildAvatarHTML` function never receives the API key as input, and no code path includes it in the output.

**Consequences (testable):**
- Grep the generated HTML string for the API key value — returns empty.
- Grep for common API key patterns (`sk-`, `r8_`, etc.) in the exported file — returns only false positives from colour values.
- Review the `buildAvatarHTML` function signature and verify the key is not passed.

#### FR-6: Client-side download mechanism
Download uses the same client-side mechanism as PNG export: construct the HTML string → create a `Blob` with MIME type `text/html` → `URL.createObjectURL()` → programmatic `<a download>` click → `URL.revokeObjectURL()`.

**Consequences (testable):**
- No network request is made during export.
- Download filename follows the pattern: `pixelforce-[type]-[username].html`.
- The `type` parameter uses the lowercase prefix (e.g. `wizard`, `knight`).
- The `username` uses the username value entered by the user.

#### FR-7: Grid colour correctness
Every exported cell colour exactly matches its corresponding in-app pixel colour. The export reads colours from the same pixel-map grid data structure used for screen rendering.

**Consequences (testable):**
- For any generated avatar, comparing the in-app rendered colours to the exported HTML cell colours shows 100% match.
- The text is case-insensitive and leading `#` is normalized.

## 5. Cross-Cutting NFRs

| ID | Concern | Requirement |
|----|---------|-------------|
| NFR-1 | Privacy | API key is never included in the exported HTML; no user data written to the export beyond the grid, label, prefix, and username |
| NFR-2 | Portability | Exported file renders correctly when opened offline in Chrome 110+, Firefox 115+, Safari 16+ with no internet connection |
| NFR-3 | File size | Export is lightweight — uses raw CSS colour values, not base64-encoded images or embedded fonts |
| NFR-4 | Self-containment | Exported file has no `<script>` tags, no external resource references, no CDN links — fully offline-renderable |
| NFR-5 | Correctness | Exported grid colours exactly match the in-app rendered avatar pixel for pixel |

## 6. MVP Scope

### 6.1 In Scope
- **Download HTML** button in the action area alongside **Download PNG**.
- `buildAvatarHTML(grid, label, prefix, username)` pure function.
- Inline CSS within `<style>` block — no external dependencies.
- Pixel cells rendered as `<div>` elements with inline `style="background:#RRGGBB"` attributes.
- API key stripped from export automatically (never passed to builder function).
- Client-side download via `Blob` → `URL.createObjectURL()` → `<a download>`.
- Filename pattern: `pixelforce-[type]-[username].html`.
- No `<script>` tags or external resource references in the export.
- Visually distinct button from the **Download PNG** button.

### 6.2 Out of Scope for MVP
- Exporting to other formats (PDF, SVG, etc.). [ASSUMPTION: future consideration]
- Adding a preview of the HTML export before download. [ASSUMPTION: not needed — what you see is what you get]
- Embedding font files or web fonts in the export. [ASSUMPTION: system fonts are adequate]
- Adding social sharing metadata (Open Graph, Twitter Card) to the export. [ASSUMPTION: future consideration]
- Exporting animated avatars. [ASSUMPTION: no animation support exists yet]

## 7. Success Metrics
**Primary:** The exported `.html` file opens in Chrome, Firefox, and Safari (offline) and renders a pixel-identical copy of the in-app avatar.

**Secondary:** Grep-confirmed absence of the user's API key in the exported file. File size under 50 KB for a typical 32×32 avatar.

## 8. Open Questions
1. Should the export include a small "Made with PixelForge" footer text? The requirement suggests it's optional — confirming not needed for MVP.
2. Should the export use a CSS Grid or `<table>` approach? The requirement says either is fine — CSS Grid produces cleaner output.
3. Theme (dark/light) — should the exported HTML match the current app theme, or use a fixed light background for maximum portability?

## 9. Assumptions Index
- From §6.2: No other export formats needed for MVP — HTML-only.
- From §6.2: No export preview dialog needed.
- From §6.2: System fonts (monospace) are sufficient for the export label.
- From §8.2: CSS Grid is preferred over `<table>` for cleaner output.
- The pixel-map data structure from FEAT-001 (2D array of hex strings + palette + label) is the source of truth for export colours.
- The `prefix` (avatar type) and `username` values are available as JS variables at export time, matching the FEAT-001 implementation.
