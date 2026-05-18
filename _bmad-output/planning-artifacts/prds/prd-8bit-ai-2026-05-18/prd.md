---
title: PixelForge — 8-Bit Avatar Generator
status: final
created: 2026-05-18
updated: 2026-05-18
---

# PRD: PixelForge — 8-Bit Avatar Generator (FEAT-001)
*Hobby project — single-file web app.*

## 0. Document Purpose
This PRD captures the requirements for the PixelForge 8-Bit Avatar Generator, a single-file HTML application that generates stylised pixel avatars using an LLM (text-based, not image model). It is for the sole builder/maintainer. Features are grouped with functional requirements nested; assumptions are tagged inline.

## 1. Vision
PixelForge lets anyone create a retro 8-bit pixel avatar from a character name and type — wizard, knight, robot, astronaut, ninja, or elf — using only their own LLM API key. No server, no image model, no sign-up. The LLM generates a structured pixel map, the browser renders it as CSS grid cells, and the user downloads the result as a PNG. Everything happens client-side; nothing is stored or transmitted except the one prompt to the LLM API of their choice.

## 2. Target User

### 2.1 Primary Persona
You — someone who wants a quick, nostalgic avatar for a profile picture, a game asset placeholder, or just for fun. Comfortable bringing your own API key.

### 2.2 Jobs To Be Done
- Generate a retro pixel avatar from a character concept.
- Download it as a PNG for reuse elsewhere.
- Experiment with different avatar types and names quickly.
- Keep API keys private — no server, no persistence.

## 3. Glossary
- **Pixel map** — A JSON object containing a `palette` (array of hex colours), `grid` (square 2D array of hex colour strings), and `label` (display name).
- **Prefix type** — One of six avatar categories: Wizard, Knight, Robot, Astronaut, Ninja, Elf.
- **BYOK** — Bring Your Own Key; the user provides their own LLM API key at runtime.

## 4. Features

### 4.1 API Key Entry
**Description:** The user enters their LLM API key into a masked input field. The key is held in a JavaScript variable for the duration of the session. It is never sent anywhere except the chosen LLM API endpoint as part of a chat completion request. The key is never written to `localStorage`, cookies, logs, or any backend. Optionally stored in `sessionStorage` so it survives page refresh within the same tab, but cleared on tab close. Realizes UJ (generate avatar).

**Functional Requirements:**

#### FR-1: Masked API key input
User can enter and show/hide their API key in a password-type input. The key is accessible in memory for API calls.

**Consequences (testable):**
- Input is `type="password"` by default; toggle button switches to `type="text"`.
- Key value is readable via `input.value` in JS.

**Out of Scope:** Key validation (no schema-check before API call).

#### FR-2: Session-only key storage
Key persists only in `sessionStorage` during the session — not in `localStorage`, not in cookies, not transmitted to any server other than the configured LLM API.

**Consequences (testable):**
- `localStorage.getItem('pixelforge-key')` returns `null` after any write attempt.
- After tab close, key is gone.

### 4.2 LLM Pixel Generation
**Description:** The core feature. The user selects a prefix type (Wizard, Knight, Robot, Astronaut, Ninja, Elf), enters a character name, and clicks Generate. The app sends a chat completion request to the selected LLM provider with a system prompt that enforces a strict JSON pixel-map schema. The LLM responds with a 16×16 or 32×32 grid of hex colour codes. The app parses this JSON and renders it as coloured `<div>` cells on screen. Realizes UJ (generate avatar).

**Functional Requirements:**

#### FR-3: Prefix type selector
User selects exactly one of six prefix types before generating: Wizard, Knight, Robot, Astronaut, Ninja, Elf. The selected prefix is injected into the prompt sent to the LLM.

**Consequences (testable):**
- Exactly one option is selected at any time.
- Selection is reflected in the LLM prompt (e.g. "Generate a pixel avatar for a Wizard character named Alice").

#### FR-4: LLM prompt contract
The system prompt instructs the LLM to respond **only** with a JSON object matching this schema:

```json
{
  "palette": ["#RRGGBB", ...],
  "grid": [["#RRGGBB", ...], ...],
  "label": "character name"
}
```

The `grid` must be square (16×16 or 32×32), every cell a valid 6-digit hex colour. The `label` is the display name shown beneath the avatar.

**Consequences (testable):**
- LLM response is parsed and validated against the schema.
- Malformed JSON or missing fields trigger a human-readable error — not a blank screen or JS crash.

#### FR-5: Multi-provider LLM support
User can select from at least these providers: Anthropic (Messages API), OpenAI (Chat Completions), OpenAI-Compatible (any endpoint), DeepSeek (Chat Completions). Provider selection updates the API URL and model defaults.

[ASSUMPTION: Anthropic uses `claude-sonnet-4-20250514`; OpenAI uses `gpt-4o`; OpenAI-Compatible defaults to Together AI `meta-llama/Llama-3.3-70B-Instruct-Turbo`; DeepSeek uses `deepseek-v4-flash`. User can override URL and model.]

**Consequences (testable):**
- Provider dropdown with 4+ options.
- API URL and model fields pre-fill per provider selection.
- Each provider's auth header format is handled correctly (Anthropic: `x-api-key`, OpenAI/DeepSeek: `Bearer`).

#### FR-6: Loading indicator
While the LLM call is in-flight, a loading animation is shown — a blinking pixel block with a "GENERATING..." label.

**Consequences (testable):**
- Loading state shown immediately on Generate click.
- Generate button is disabled during loading.
- Loading state replaced by result or error on completion.

### 4.3 Avatar Rendering
**Description:** The parsed pixel map is rendered as an HTML/CSS grid — each cell is a `<div>` with a background colour from the LLM response. No canvas, no image URL, no base64 blob required for display. The label is shown beneath the grid. Realizes UJ (view avatar).

**Functional Requirements:**

#### FR-7: CSS grid render
The pixel grid renders as coloured `<div>` cells arranged in a CSS Grid. Each cell is `1×1` in logical size; the grid is scaled up to a visible size (e.g. 256×256 px total).

**Consequences (testable):**
- Grid of coloured cells visible on screen.
- No image-generation API calls for rendering.
- Cells match the hex colours from the LLM response.

#### FR-8: Label display
The `label` value from the LLM JSON response is displayed beneath the avatar grid.

**Consequences (testable):**
- Text below the avatar matches the `label` field.
- Empty label defaults to the character name or prefix type.

### 4.4 PNG Export
**Description:** A Download PNG button draws the rendered grid onto an off-screen `<canvas>`, converts to PNG via `canvas.toBlob()`, and triggers a browser download. All client-side. Realizes UJ (download avatar).

**Functional Requirements:**

#### FR-9: Client-side PNG download
Download button exports the avatar grid as a PNG file. Filename follows the pattern: `pixelforce-[type]-[username].png`. Uses `canvas.toBlob()` → `URL.createObjectURL()` → programmatic `<a download>` click.

**Consequences (testable):**
- Clicking Download saves a `.png` file.
- No network request is made during export.
- Filename matches expected pattern.

### 4.5 Theme Toggle
**Description:** A dark/light theme toggle persists in `localStorage`. The UI follows the reference design's colour tokens for both themes. Realizes UJ (customise appearance).

**Functional Requirements:**

#### FR-10: Dark/light theme
User can toggle between dark and light themes. Preference persists in `localStorage`. Default is light.

**Consequences (testable):**
- Theme button toggles between DARK/LIGHT display.
- After refresh, theme persists.
- All UI elements respect theme variables.

## 5. Cross-Cutting NFRs

| ID | Concern | Requirement |
|----|---------|-------------|
| NFR-1 | Security | API key never leaves the browser; no server-side component. Key is `sessionStorage` at most, never `localStorage`. |
| NFR-2 | Privacy | No user images, prompts, or usernames are stored or logged anywhere client-side. |
| NFR-3 | Portability | Works by opening the `.html` file directly in a modern browser (no server, no build step). |
| NFR-4 | Error handling | Malformed JSON, API errors, and network failures show a human-readable error in the UI. |
| NFR-5 | Compatibility | Chrome 110+, Firefox 115+, Safari 16+. |
| NFR-6 | Design fidelity | Visual design matches the reference `pixelforce-avatar-generator.html` — colour palette, fonts (`Press Start 2P`, monospace), layout, spacing, scanline overlay. The output file overwrites the reference (same filename in the same folder). |

## 6. MVP Scope

### 6.1 In Scope
- Single HTML file with all CSS and JS inlined.
- API key entry with show/hide, session-only.
- Username / character name input.
- Prefix type selector (6 types).
- Multi-provider LLM support (Anthropic, OpenAI, OpenAI-Compatible).
- LLM prompt contract enforcing JSON pixel-map schema.
- CSS grid rendering of pixel map.
- Loading indicator.
- Client-side PNG download.
- Dark/light theme toggle with localStorage persistence.
- Error display for API failures and malformed responses.

### 6.2 Out of Scope for MVP
- Image-generation model support — LLM-only. [ASSUMPTION]
- Server-side components of any kind.
- Gallery / history of past avatars.
- Social sharing.
- User accounts or authentication.
- Custom colour palette editing.
- Animated avatars.

## 7. Success Metrics
**Primary:** The app generates a valid pixel avatar on the first LLM call for all 6 prefix types without errors.

**Secondary:** Download PNG produces a correctly formatted file. The page loads and works in all three target browsers without console errors.

## 8. Open Questions
1. Should the LLM response be cached in sessionStorage to allow re-download without re-generating?
2. What prompt temperature to use for the LLM to produce creative but structurally valid pixel maps?
3. Should the provider/model defaults offer more options (e.g. Google Gemini)?

## 9. Assumptions Index
- From §4.2 (FR-5): Anthropic default model = `claude-sonnet-4-20250514`; OpenAI = `gpt-4o`; OpenAI-Compatible = `meta-llama/Llama-3.3-70B-Instruct-Turbo` via Together AI; DeepSeek = `deepseek-v4-flash`.
- From §6.2: No image-generation model support — the app is LLM-only.
- From §4.2: Grid size of 32×32 is preferred over 16×16 for visual quality.
- The reference HTML design system (colours, fonts, layout, scanline effect) should be replicated exactly in the new single-file app.
