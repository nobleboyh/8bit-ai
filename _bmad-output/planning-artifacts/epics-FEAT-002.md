---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-8bit-ai-2026-05-18-feat002/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - docs/FEAT-002/FEAT-002-requirement.md
---

# 8bit-ai - FEAT-002 Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for FEAT-002 (PixelForge — HTML Download Export), decomposing the requirements from the PRD into implementable stories. All epics and stories carry the FEAT-002 prefix to distinguish them from FEAT-001 (Epic 1/2).

## Requirements Inventory

### Functional Requirements

```
FR-1: Download HTML button — The action area shows a "DOWNLOAD HTML" button alongside "DOWNLOAD PNG" after successful avatar generation. Button is visually distinct and hidden before generation.
FR-2: buildAvatarHTML pure function — A pure function buildAvatarHTML(grid, label, prefix, username) returns a complete HTML string with no closure references to apiKey, localStorage, or other external state.
FR-3: Self-contained HTML structure — Exported HTML includes <!DOCTYPE html>, <meta charset>, <meta viewport>, <title>, inline <style>, no <script> tags, no external <link> or <img> tags referencing URLs.
FR-4: Pixel grid rendering — Grid cells rendered as <div> with inline style="background:#RRGGBB" matching grid cell colours. No class attributes for styling cells. Grid dimensions match source grid.length × grid[0].length.
FR-5: API key absence — Generated HTML contains no trace of the user's API key. The buildAvatarHTML function never receives the API key.
FR-6: Client-side download mechanism — Download via Blob → URL.createObjectURL() → programmatic <a download> click → URL.revokeObjectURL(). No network request. Filename: pixelforce-[type]-[username].html.
FR-7: Grid colour correctness — Every exported cell colour exactly matches its corresponding in-app pixel colour from the same pixel-map grid data structure.
```

### NonFunctional Requirements

```
NFR-1: Privacy — API key is never included in the exported HTML; no user data beyond grid, label, prefix, and username.
NFR-2: Portability — Exported file renders correctly when opened offline in Chrome 110+, Firefox 115+, Safari 16+.
NFR-3: File size — Export is lightweight, using raw CSS colour values not base64-encoded images or embedded fonts.
NFR-4: Self-containment — Exported file has no <script> tags, no external resource references, no CDN links.
NFR-5: Correctness — Exported grid colours exactly match the in-app rendered avatar pixel for pixel.
```

### Additional Requirements

```
AR-1: Follow existing FEAT-001 conventions — named exports, component colocation, TypeScript strict, CSS modules, Result<T, E> error pattern.
AR-2: buildAvatarHTML lives in src/utils/ as a pure utility function, consistent with the existing codebase structure.
AR-3: Download HTML button added to the existing action area alongside the Download PNG button.
AR-4: The existing pngExport utility pattern should be mirrored for HTML export (htmlExport utility).
```

### UX Design Requirements

```
UX-DR1: Download HTML button is visually distinct from Download PNG button (different label, optionally different style/icon).
UX-DR2: Both download buttons are only visible/enabled after successful avatar generation.
UX-DR3: No additional dialogs or confirmation — clicking triggers immediate download.
UX-DR4: Button placement groups HTML download with PNG download in the same action row.
```

### FR Coverage Map

| FR | Epic | Component/File |
|----|------|---------------|
| FR-1 | FEAT-002 Epic 1 | AvatarResult / DownloadHtmlButton |
| FR-2 | FEAT-002 Epic 1 | src/utils/buildAvatarHTML |
| FR-3 | FEAT-002 Epic 1 | src/utils/buildAvatarHTML |
| FR-4 | FEAT-002 Epic 1 | src/utils/buildAvatarHTML |
| FR-5 | FEAT-002 Epic 1 | src/utils/buildAvatarHTML (by omission) |
| FR-6 | FEAT-002 Epic 1 | src/utils/htmlExport |
| FR-7 | FEAT-002 Epic 1 | src/utils/buildAvatarHTML + htmlExport |

## Epic List

### FEAT-002 Epic 1: HTML Download Export
Users can download their generated pixel avatar as a self-contained `.html` file that renders offline without any server, API key, or external dependencies.
**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7
**NFRs covered:** NFR-1, NFR-2, NFR-3, NFR-4, NFR-5

---

## FEAT-002 Epic 1: HTML Download Export

Users can download their generated pixel avatar as a self-contained `.html` file that renders offline without any server, API key, or external dependencies.
**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7
**NFRs covered:** NFR-1, NFR-2, NFR-3, NFR-4, NFR-5

### FEAT-002 Story 1.1: buildAvatarHTML Pure Function

As a developer,
I want a pure function `buildAvatarHTML(grid, label, prefix, username)` that produces a complete, self-contained HTML string from pixel map data,
So that the export logic is testable, isolated from the DOM, and guaranteed free of API key leakage.

**Acceptance Criteria:**

**Given** a valid pixel map with grid, label, prefix, and username
**When** `buildAvatarHTML(grid, label, prefix, username)` is called
**Then** it returns a string starting with `<!DOCTYPE html>` and containing `<html lang="en">`
**And** the returned string includes `<meta charset="UTF-8">` and `<meta name="viewport">`
**And** the `<title>` is `"[prefix] [username] — Pixelforce Avatar"`
**And** all CSS is inlined within a single `<style>` block inside `<head>`
**And** the HTML string contains no `<script>` tags
**And** the HTML string contains no `<link>` or `<img>` tags referencing external URLs

**Given** the same grid, label, prefix, and username inputs
**When** `buildAvatarHTML` is called twice with identical arguments
**Then** both return values are identical strings — the function is pure

**Given** a call to `buildAvatarHTML`
**When** I inspect the returned string for the user's API key value
**Then** no match is found
**And** no match is found for common API key patterns (`sk-`, `r8_`, `sk-ant-`)

**Given** a 16×16 or 32×32 pixel grid
**When** the HTML is generated
**Then** every grid cell in the avatar section has an inline `style="background:#RRGGBB"` attribute
**And** no cell uses a `class` attribute for its background colour
**And** the grid dimensions match `grid.length × grid[0].length`
**And** each cell colour matches the corresponding hex value from the input grid

**Given** a fixed light background is used for the exported page
**When** the HTML is rendered
**Then** the avatar grid cells use the exact colours from the input grid
**And** the label text is displayed beneath the avatar grid
**And** no `class` attributes are used for styling grid cells

**Given** the export uses CSS Grid layout
**When** the HTML is rendered
**Then** the grid layout produces a visually identical result to the in-app rendering

**Given** a typical 32×32 avatar with palette
**When** `buildAvatarHTML` generates the output
**Then** the resulting HTML file size is under 50 KB

### FEAT-002 Story 1.2: HTML Export Utility & Download Button

As a user,
I want a **Download HTML** button in the action area that downloads my avatar as a `.html` file,
So that I can save, share, or embed my avatar as a portable pixel-art page without needing a server.

**Acceptance Criteria:**

**Given** the existing `pngExport` utility pattern
**When** I create the `htmlExport` utility
**Then** it lives in `src/utils/htmlExport.ts` with a named export
**And** it accepts `(grid, label, prefix, username)` parameters
**And** it calls `buildAvatarHTML` to get the HTML string
**And** it creates a `Blob` with MIME type `text/html`
**And** it triggers download via `URL.createObjectURL()` → programmatic `<a download="...">` click → `URL.revokeObjectURL()`
**And** errors follow the `Result<T, AppError>` pattern

**Given** no avatar has been generated
**When** I view the action area
**Then** the **Download HTML** button is not visible

**Given** a successful avatar generation
**When** the result state is active
**Then** a **Download HTML** button is visible in the action area alongside **Download PNG**
**And** the button label is distinct (e.g., "DOWNLOAD HTML") from "DOWNLOAD PNG"
**And** the button is visually distinguishable (different colour, style, or icon) per UX-DR1
**And** both buttons are grouped together in the same action row per UX-DR4

**Given** the **Download HTML** button is visible
**When** I click it
**Then** no confirmation dialog is shown (per UX-DR3)
**And** a file download is triggered immediately
**And** no network request is made during the download
**And** the filename is `pixelforce-[type]-[username].html` where `type` is the lowercase prefix and `username` is the entered name

**Given** the download is triggered
**When** I inspect the mechanism
**Then** it uses `Blob` with MIME type `text/html`
**And** it uses `URL.createObjectURL()` for the blob URL
**And** it uses a programmatic `<a download="...">` click
**And** `URL.revokeObjectURL()` is called after the click

**Given** the downloaded `.html` file is opened offline in Chrome 110+, Firefox 115+, or Safari 16+
**When** the page loads
**Then** the avatar renders identically to the in-app view
**And** the page title displays `[prefix] [username] — Pixelforce Avatar`
**And** the label text is displayed beneath the avatar
**And** no console errors about missing resources are reported
