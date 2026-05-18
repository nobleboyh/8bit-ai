# Pixel Avatar Generator — Agent Requirement

## Overview

Build a **single-file web application** (`pixelforce-avatar-generator.html`) that generates stylised 8-bit pixel avatars using a text-based LLM (not an image-generation model). The visual design and aesthetic **must match** the reference file `pixelforce-avatar-generator.html` located in the same folder. Read that file first before writing any code.

---

## Functional Requirements

### 1. API Key Handling
- The application **must not store, transmit, or persist** any API key on a server.
- The API key is entered by the user at runtime via an input field in the UI.
- The key is held only in browser memory (JS variable or `sessionStorage`) for the duration of the session.
- The key is **never** written to `localStorage`, cookies, logs, or any backend.

### 2. Avatar Generation — LLM-Only (No Image Model)
- Avatars are rendered entirely using **HTML + CSS** (e.g. CSS grid of coloured `<div>` cells, inline styles, or SVG).
- The LLM is prompted to return a **structured pixel map**: a 2D grid of hex colour codes or named colours representing each pixel cell.
- The application parses the LLM response and renders the grid on screen — no image URL, no base64 blob, no canvas drawing API required (canvas may be used only for the PNG export step described below).
- The LLM model to use: any standard chat-completion model (e.g. `claude-sonnet-4-20250514` via the Anthropic API, or equivalent). Do **not** call any image-generation endpoint.

#### LLM Prompt Contract
The system prompt must instruct the model to reply **only** with a JSON object in the following schema and nothing else:

```json
{
  "palette": ["#RRGGBB", ...],
  "grid": [
    ["#RRGGBB", "#RRGGBB", ...],
    ...
  ],
  "label": "Wizard Hoang"
}
```

- `grid` must be a square 2D array (recommend 16 × 16 or 32 × 32).
- Every cell value must be a valid 6-digit hex colour string.
- `label` is a short display name shown beneath the avatar.

### 3. Avatar Prefix / Type
The user selects **one** prefix type from the following fixed list before generating:

| Value | Display Label |
|-------|--------------|
| `wizard` | 🧙 Wizard |
| `knight` | ⚔️ Knight |
| `robot` | 🤖 Robot |
| `astronaut` | 🚀 Astronaut |
| `ninja` | 🥷 Ninja |
| `elf` | 🧝 Elf |

The selected prefix is injected into the user prompt sent to the LLM, e.g.:  
`"Generate a pixel avatar for a [Wizard] character named [username]."`

### 4. Download — Client-Side Only
- Provide a **Download PNG** button.
- Export is performed entirely in the browser: draw the rendered CSS grid onto an HTML5 `<canvas>`, then trigger `canvas.toBlob()` → `URL.createObjectURL()` → programmatic `<a download>` click.
- The server **never** receives, stores, or processes user avatars.
- The downloaded filename should follow the pattern: `pixelforce-[type]-[username].png`

---

## UI / UX Requirements

- Follow the visual design of the reference file `pixelforce-avatar-generator.html` exactly (colour palette, fonts, layout, spacing, component styles).
- The page is a **single HTML file** with all CSS and JS inlined — no external build step, no npm, no bundler.
- External CDN resources (fonts, icon sets) are allowed.
- UI flow:
  1. User enters their **API key** (masked input).
  2. User enters a **username / character name**.
  3. User selects a **prefix type** from the list above.
  4. User clicks **Generate**.
  5. A loading indicator is shown while the LLM call is in-flight.
  6. The rendered pixel avatar appears with its label.
  7. User clicks **Download PNG** to save locally.

---

## Non-Functional Requirements

| Concern | Requirement |
|---------|-------------|
| Security | API key never leaves the browser; no server-side component |
| Privacy | No user images or usernames are stored or logged anywhere |
| Portability | Works by opening the `.html` file directly in a modern browser (no server required) |
| Error handling | Show a human-readable error message if the LLM returns malformed JSON or the API call fails |
| Compatibility | Chrome 110+, Firefox 115+, Safari 16+ |

---

## Files

| File | Role |
|------|------|
| `pixelforce-avatar-generator.html` | **Output** — the complete single-file application |
| `pixelforce-avatar-generator.html` (reference, same name in same folder) | **Input** — read this first to extract the design system |

> ⚠️ The reference file and the output file share the same name. Read the reference file to understand the design, then **overwrite / replace** it with the fully functional implementation.

---

## Implementation Checklist

- [ ] Read and analyse the reference `pixelforce-avatar-generator.html` for design tokens (colours, fonts, spacing, components)
- [ ] Scaffold the single-file HTML structure
- [ ] Implement API key input (masked, session-only)
- [ ] Implement username input and prefix selector (6 options)
- [ ] Write the LLM system prompt enforcing the JSON pixel-map schema
- [ ] Implement the `fetch` call to the Anthropic Messages API (or equivalent)
- [ ] Parse and validate the JSON response; show errors gracefully
- [ ] Render the pixel grid from the colour array using CSS (divs or SVG)
- [ ] Implement client-side PNG export via `<canvas>` + `toBlob()`
- [ ] Apply the reference design system throughout
- [ ] Test all 6 prefix types end-to-end