# Pixel Avatar Generator — HTML Download Feature Requirement

## Overview

Extend the existing `pixelforce-avatar-generator.html` application with an additional **Download HTML** option, allowing users to save their generated 8-bit avatar as a self-contained `.html` file that can be opened in any browser without any server, API key, or external dependency.

---

## Functional Requirement

### Download as HTML (Client-Side Only)

- Add a **Download HTML** button alongside the existing **Download PNG** button.
- When clicked, the application constructs a **self-contained HTML string** in memory representing the current rendered avatar.
- The file is delivered via the same client-side mechanism as PNG export: `Blob` → `URL.createObjectURL()` → programmatic `<a download>` click.
- The server **never** receives, stores, or processes the exported file.
- The downloaded filename must follow the pattern: `pixelforce-[type]-[username].html`

---

## Exported HTML File Specification

The exported `.html` file must be:

| Constraint | Detail |
|------------|--------|
| **Self-contained** | No external scripts, no CDN links, no API calls — fully offline-renderable |
| **No API key** | The user's API key must **never** appear anywhere in the exported file |
| **No runtime dependencies** | Pure HTML + inline CSS only; no JavaScript required to render the avatar |
| **Pixel-accurate** | The avatar grid must render identically to what the user sees in the app |

### Required Contents of the Exported File

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>[prefix] [username] — Pixelforce Avatar</title>
  <style>
    /* Inline styles only — reproduce the avatar grid and label styles from the app */
  </style>
</head>
<body>
  <!-- Avatar grid: a table or div grid of coloured cells matching the pixel map -->
  <!-- Avatar label: the character name displayed beneath the grid -->
  <!-- Optional: a small "Made with Pixelforce" footer — no link required -->
</body>
</html>
```

#### Grid Rendering in the Export

- Each pixel cell is rendered as a `<div>` (or `<td>`) with its background colour set via an **inline `style` attribute** (e.g. `style="background:#A3F2C1"`).
- No CSS classes referencing external stylesheets.
- Grid layout is achieved with CSS Grid or an HTML `<table>` — both are acceptable; choose whichever produces smaller, cleaner output.
- The grid dimensions in the export must exactly match the grid dimensions used in the app (e.g. 16 × 16 or 32 × 32).

---

## UI / UX Requirements

- The **Download HTML** button must be visually distinct from the **Download PNG** button (different label, optionally different icon or style) so users understand they are two separate formats.
- Both download buttons are only visible/enabled **after** a successful avatar generation.
- The button placement should feel natural alongside the existing Download PNG button — group them together in the action area.
- No additional user input or confirmation dialog is required; clicking the button triggers the download immediately.

---

## Non-Functional Requirements

| Concern | Requirement |
|---------|-------------|
| Privacy | API key is stripped from the export; no user data persists server-side |
| Portability | Exported file opens correctly in Chrome 110+, Firefox 115+, Safari 16+ with no internet connection |
| File size | Export should be lightweight — avoid embedding base64 images; use raw CSS colour values instead |
| Correctness | Exported grid colours must exactly match the in-app rendered avatar |

---

## Implementation Checklist

- [ ] Add a **Download HTML** button to the action area (visible only after generation)
- [ ] Implement `buildAvatarHTML(grid, label, prefix, username)` — a pure function that returns the full HTML string
- [ ] Inline all required CSS within the `<style>` block; use no external references
- [ ] Render each pixel cell using inline `style="background:#RRGGBB"` attributes
- [ ] Ensure the API key is **absent** from the generated HTML string
- [ ] Trigger download via `Blob` → `URL.createObjectURL()` → `<a download="pixelforce-[type]-[username].html">`
- [ ] Verify the exported file renders correctly when opened offline in all three target browsers
- [ ] Confirm the exported file contains no `<script>` tags or external resource references