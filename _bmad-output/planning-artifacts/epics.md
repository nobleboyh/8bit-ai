---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-8bit-ai-2026-05-18/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - docs/FEAT-001/FEAT-001-requirement.md
  - docs/FEAT-001/pixelforge-avatar-generator.html
---

# 8bit-ai - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for 8bit-ai (PixelForge — 8-Bit Avatar Generator), decomposing the requirements from the PRD, UX Design, and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

```
FR-1: Masked API key input — User can enter and show/hide their API key in a password-type input.
FR-2: Session-only key storage — API key persists only in sessionStorage during the session, never localStorage or cookies.
FR-3: Prefix type selector — User selects exactly one of six prefix types (Wizard, Knight, Robot, Astronaut, Ninja, Elf) before generating.
FR-4: LLM prompt contract — System prompt enforces strict JSON pixel-map schema with palette, grid (16×16 or 32×32), and label fields.
FR-5: Multi-provider LLM support — User can select from Anthropic, OpenAI, OpenAI-Compatible, and DeepSeek; provider selection updates API URL and model defaults.
FR-6: Loading indicator — Blinking pixel block with "GENERATING..." label shown during LLM call; Generate button disabled while loading.
FR-7: CSS grid render — Pixel grid renders as coloured <div> cells arranged in CSS Grid, scaled to visible size (e.g. 256×256 px total).
FR-8: Label display — The label value from the LLM JSON response is displayed beneath the avatar grid.
FR-9: Client-side PNG download — Download button exports avatar grid as PNG via canvas.toBlob(); filename pattern: pixelforce-[type]-[username].png.
FR-10: Dark/light theme toggle — User can toggle between dark and light themes; preference persists in localStorage; default is light.
```

### NonFunctional Requirements

```
NFR-1: Security — API key never leaves the browser; no server-side component. Key is sessionStorage at most, never localStorage.
NFR-2: Privacy — No user images, prompts, or usernames are stored or logged anywhere client-side.
NFR-3: Portability — Works by opening the .html file directly in a modern browser (no server, no build step).
NFR-4: Error handling — Malformed JSON, API errors, and network failures show a human-readable error in the UI.
NFR-5: Compatibility — Chrome 110+, Firefox 115+, Safari 16+.
NFR-6: Design fidelity — Visual design matches the reference pixelforce-avatar-generator.html — colour palette, fonts (Press Start 2P, monospace), layout, spacing, scanline overlay.
```

### Additional Requirements

```
AR-1: Starter template — Scaffold with Vite 6 + React 18 + TypeScript via `npm create vite@latest --template react-ts`.
AR-2: Build inlining — Use vite-plugin-singlefile@2.3.3 to inline all JS and CSS into a single dist/index.html.
AR-3: State management — React hooks (useState, useContext) and custom hooks; no external state library.
AR-4: Strategy pattern — Multi-provider LLM abstraction via common interface (LLMProvider), with separate implementations for Anthropic, OpenAI, OpenAI-Compatible, DeepSeek.
AR-5: Error handling pattern — Typed union Result<T, E> pattern: { ok: true, data: T } | { ok: false, error: AppError }.
AR-6: Component structure — Components in src/components/[Name]/, hooks in src/hooks/, services in src/services/, types in src/types/, utils in src/utils/.
AR-7: TypeScript strict — Strong typing with PixelMap schema types; runtime validation of LLM JSON responses.
AR-8: CSS modules — Per-component .module.css files; theme via CSS custom properties (--bg, --text, --accent, etc.).
AR-9: Named exports only — No default exports; imports via @/ path aliases.
AR-10: Testing — Vitest + React Testing Library for unit/integration tests; tests co-located with source files.
AR-11: Auth header format — Anthropic uses x-api-key header; OpenAI/OpenAI-Compatible/DeepSeek use Bearer token.
AR-12: API URL and model fields — Pre-fill per provider selection; user can override URL and model.
```

### UX Design Requirements

```
UX-DR1: Design system tokens — Implement CSS custom properties for both dark and light themes (--bg, --surface, --fg, --muted, --border, --accent, --accent-dim, --danger, --success, --scanline, --shadow) scoped to [data-theme] selectors.
UX-DR2: Typography — Press Start 2P from Google Fonts for all UI text (headings, labels, buttons, chips); Courier New monospace stack for input fields and error messages. Size scale: 9px-28px using clamp() for fluid scaling.
UX-DR3: Scanline overlay — repeating-linear-gradient on body background creating CRT scanline effect; colour varies per theme with semi-transparent scanline token.
UX-DR4: Pixel-loader animation — Single accent-coloured 48×48px square with blink keyframe (0.6s step-end infinite); paired with "GENERATING..." text using pulse-text animation (1.5s step-end infinite).
UX-DR5: Avatar viewer state machine — Four mutually exclusive states: empty (icon + instructional text), loading (pixel-loader), result (canvas + metadata + action buttons), error (red-bordered error box). Switched via .hidden class.
UX-DR6: Custom select dropdown — Styled dropdown replacing native <select> with trigger button (current value + arrow indicator) and options list; open/close toggle, option hover (accent tint), selected state (accent background).
UX-DR7: Example chips — Six one-click prompt presets (Wizard, Knight, Robot, Astronaut, Ninja, Elf) styled as bordered chips with hover accent highlight; click fills textarea.
UX-DR8: Button interaction states — Hover (--accent-dim background, accent border, #000 text), active (translate 2px 2px), disabled (0.4 opacity, not-allowed cursor, no transform).
UX-DR9: Section layout — Numbered sections (01 CONFIG, 02 PROMPT, 03 AVATAR) with 3px solid border, 24px padding; container max-width 720px; gap scale: 8px/10px/14px/24px.
UX-DR10: Responsive design — Breakpoint at ≤600px (16px padding, vertical action rows, 240px viewer min-height) and ≤360px (8px section padding, tighter chips).
UX-DR11: Keyboard shortcut — Cmd/Ctrl+Enter triggers generate from prompt textarea.
UX-DR12: Accessibility — Accent-coloured focus borders on all inputs/buttons; minimum 44px touch targets; semantic HTML structure; keyboard-navigable controls.
UX-DR13: Avatar display container — Black background, 4px border, 8px 8px offset shadow mimicking NES sprite rendering; image-rendering: pixelated.
UX-DR14: Action rows — Flexbox layout helpers (action-row, api-row, generate-row, examples-row) that stack vertically on mobile.
UX-DR15: Config persistence — Provider, API URL, model, and API key saved to localStorage on successful generate; restored on page load with "Settings saved locally" notice.
UX-DR16: Empty state — Large pixel icon (U+25A3) + "ENTER A PROMPT & FORGE YOUR PIXEL" instructional text centred in viewer.
```

## Epic List

### Epic 1: Project Foundation & User Setup
Users can configure the app — enter their API key, select a provider, toggle the theme, and see the retro-styled layout ready for generation.
**FRs covered:** FR-1 (masked API key), FR-2 (sessionStorage), FR-10 (theme toggle)
**UX-DRs covered:** UX-DR1–UX-DR15 (design system, typography, scanline overlay, layouts, custom select, chips, responsive, config persistence, button states)

### Epic 2: Avatar Generation, Rendering & Export
Users can generate, view, and download pixel avatars from an LLM.
**FRs covered:** FR-3 (prefix selector), FR-4 (prompt contract), FR-5 (multi-provider), FR-6 (loading), FR-7 (CSS grid render), FR-8 (label display), FR-9 (PNG download)
**NFRs covered:** NFR-4 (error handling)

### FR Coverage Map

| FR | Epic | Component/File |
|----|------|---------------|
| FR-1 | Epic 1 | ApiKeyInput + useApiKey |
| FR-2 | Epic 1 | useApiKey (sessionStorage) |
| FR-3 | Epic 2 | ControlPanel |
| FR-4 | Epic 2 | usePixelGeneration + services/llmClient |
| FR-5 | Epic 2 | services/providers.ts |
| FR-6 | Epic 2 | LoadingIndicator |
| FR-7 | Epic 2 | AvatarGrid |
| FR-8 | Epic 2 | AvatarGrid (label) |
| FR-9 | Epic 2 | DownloadButton + pngExport |
| FR-10 | Epic 1 | ThemeToggle + useTheme |

## Epic 1: Project Foundation & User Setup

Users can configure the app — enter their API key, select a provider, toggle the theme, and see the retro-styled layout ready for generation.
**FRs covered:** FR-1, FR-2, FR-10
**UX-DRs covered:** UX-DR1–UX-DR15

### Story 1.1: Project Scaffold & Build Tooling

As a developer,
I want the project scaffolded with Vite 6 + React 18 + TypeScript and configured to build into a single `.html` file,
So that I can develop with HMR and produce a portable single-file output.

**Acceptance Criteria:**

**Given** the project directory does not exist
**When** I run `npm create vite@latest pixelforge -- --template react-ts`
**Then** a new project is created with Vite, React, and TypeScript configured
**And** `npm install` resolves all dependencies without errors

**Given** a Vite+React project exists
**When** I install `vite-plugin-singlefile` as a dev dependency
**Then** `npm install -D vite-plugin-singlefile` succeeds

**Given** vite.config.ts has the singlefile plugin configured
**When** I run `npm run build`
**Then** `dist/index.html` is produced as a single file with all JS and CSS inlined
**And** opening `dist/index.html` in a browser renders the starter page

**Given** the project is scaffolded
**When** I inspect `tsconfig.json` or `vite.config.ts`
**Then** `@/` path alias is configured pointing to `src/`
**And** the directory structure matches: `src/components/`, `src/hooks/`, `src/services/`, `src/types/`, `src/utils/`

**Given** TypeScript strict mode is enabled
**When** I run `npx tsc --noEmit`
**Then** no compilation errors are reported

### Story 1.2: Design System & Theme Toggle

As a user,
I want the app to have a retro NES-inspired visual theme with a dark/light toggle that persists,
So that the interface feels authentic and comfortable for my preference.

**Acceptance Criteria:**

**Given** the app loads for the first time
**When** the page renders
**Then** the `data-theme` attribute on `<html>` is set to `"light"` by default
**And** the body background uses the light theme `--bg` colour (`#f5e6c8`)
**And** the Press Start 2P font is loaded from Google Fonts and applied to `--font-display`

**Given** the light theme is active
**When** I click the theme toggle button
**Then** `data-theme` changes to `"dark"`
**And** all CSS custom properties switch to dark theme values (navy `--bg`, gold `--accent`)
**And** the toggle button text changes to "LIGHT"
**And** the preference is saved to `localStorage` under key `pixelforge-theme`

**Given** I previously selected dark theme
**When** I refresh the page
**Then** `data-theme` is `"dark"` on load due to localStorage restoration

**Given** any theme is active
**When** I view the page
**Then** a scanline overlay (`repeating-linear-gradient`) is visible on the body background
**And** all interactive elements (inputs, buttons, chips) have `--accent` coloured focus borders
**And** all interactive elements have minimum 44px touch target height

### Story 1.3: API Key Input & Provider Configuration

As a user,
I want to enter my API key securely and configure my LLM provider,
So that I can authenticate with the LLM API while keeping my key private.

**Acceptance Criteria:**

**Given** the config section is visible
**When** I see the API key field
**Then** it is `type="password"` by default
**And** there is a toggle button labelled "SHOW"
**When** I click "SHOW"
**Then** the input switches to `type="text"` and the button reads "HIDE"
**And** clicking "HIDE" returns the input to `type="password"`

**Given** I enter an API key
**When** I refresh the page in the same tab
**Then** the key persists from `sessionStorage`
**When** I close and reopen the tab
**Then** the key field is empty (sessionStorage cleared)

**Given** the provider dropdown
**When** I open it
**Then** I see 4 options: Anthropic, OpenAI, OpenAI-Compatible, DeepSeek
**When** I select "Anthropic"
**Then** the API URL field fills with Anthropic's Messages API URL
**And** the model field fills with `claude-sonnet-4-20250514`
**When** I select "OpenAI"
**Then** the API URL fills with `https://api.openai.com`
**And** the model fills with `gpt-4o`
**When** I select "OpenAI-Compatible"
**Then** the API URL fills with a Together AI endpoint
**And** the model fills with `meta-llama/Llama-3.3-70B-Instruct-Turbo`
**When** I select "DeepSeek"
**Then** the API URL fills with DeepSeek's endpoint
**And** the model fills with `deepseek-v4-flash`

**Given** I modify the API URL or model fields
**When** the provider changes
**Then** the manual edits are preserved (user overrides presets)

**Given** I enter config values and click Generate
**When** the generation completes
**Then** provider, API URL, model, and API key are saved to `localStorage`
**And** the "Settings saved locally" notice is visible
**When** I reload the page
**Then** all config fields are restored from `localStorage`

**Given** the custom select is closed
**When** I click the trigger
**Then** the dropdown opens
**And** the selected option displays with accent background
**And** options show hover highlight

### Story 1.4: Layout Shell, Control Panel & Viewer Shell

As a user,
I want to see the app layout with the prompt input, example chips, and empty viewer state,
So that I understand the workflow and can enter my character concept.

**Acceptance Criteria:**

**Given** the app loads
**When** I view the page
**Then** the header displays "PIXELFORGE" title and "8-BIT AVATAR GENERATOR" subtitle in Press Start 2P
**And** there are 3 numbered sections: "01 // CONFIG", "02 // PROMPT", "03 // AVATAR"
**And** each section has a 3px solid border with 24px padding

**Given** the prompt section is visible
**When** I see the textarea
**Then** it has placeholder text suggesting an avatar description
**And** the "FORGE" button is prominent with `.btn-primary` styling
**And** 6 example chips are displayed: Wizard, Knight, Robot, Astronaut, Ninja, Elf
**When** I click an example chip
**Then** the textarea is filled with the corresponding prompt text

**Given** the viewer section is visible and no avatar has been generated
**When** I see the viewer
**Then** the empty state shows a pixel icon (U+25A3) and "ENTER A PROMPT & FORGE YOUR PIXEL" text
**And** the viewer has min-height of 320px on desktop

**Given** the viewport is ≤600px wide
**When** the page renders
**Then** section padding reduces to 16px
**And** action rows stack vertically
**And** viewer min-height is 240px

**Given** the viewport is ≤360px wide
**When** the page renders
**Then** section padding reduces to 8px
**And** chip text sizes are smaller

## Epic 2: Avatar Generation, Rendering & Export

Users can generate, view, and download pixel avatars from an LLM.
**FRs covered:** FR-3, FR-4, FR-5, FR-6, FR-7, FR-8, FR-9
**NFRs covered:** NFR-4

### Story 2.1: LLM Provider Abstraction Layer

As a developer,
I want a pluggable LLM provider abstraction with implementations for Anthropic, OpenAI, OpenAI-Compatible, and DeepSeek,
So that the app can generate pixel maps from any supported provider through a unified interface.

**Acceptance Criteria:**

**Given** the provider abstraction is designed
**When** I inspect the `LLMProvider` interface
**Then** it defines a `generate(request: PixelGenRequest): Promise<Result<PixelMapResponse, AppError>>` method
**And** `PixelGenRequest` includes `prompt`, `apiUrl`, `model`, `apiKey`
**And** `PixelMapResponse` matches the schema `{ palette: string[], grid: string[][], label: string }`
**And** `AppError` includes `message`, `code`, and optional `status` fields

**Given** the AnthropicProvider receives a request
**When** `generate()` is called
**Then** it sends POST to `{apiUrl}/v1/messages` with `x-api-key` header
**And** the request body uses the Messages API format
**And** on success, it parses the JSON content block and returns `{ ok: true, data: PixelMapResponse }`

**Given** the OpenAIProvider receives a request
**When** `generate()` is called
**Then** it sends POST to `{apiUrl}/v1/chat/completions` with `Bearer` auth header
**And** the request body uses Chat Completions format
**And** on success, it parses the response content and returns the parsed pixel map

**Given** the OpenAICompatibleProvider receives a request
**When** `generate()` is called
**Then** it follows the Chat Completions format with `Bearer` auth
**And** defaults to `meta-llama/Llama-3.3-70B-Instruct-Turbo` model via Together AI

**Given** the DeepSeekProvider receives a request
**When** `generate()` is called
**Then** it sends POST to `{apiUrl}/v1/chat/completions` with `Bearer` auth header
**And** defaults to `deepseek-v4-flash` model

**Given** any provider encounters an API error
**When** the response is non-2xx
**Then** it returns `{ ok: false, error: AppError }` with the status code and error details
**And** network failures are caught and returned as typed errors

**Given** the `llmClient` receives a provider type and config
**When** it dispatches to the appropriate provider
**Then** it instantiates the correct provider class and calls `generate()`

### Story 2.2: Pixel Generation Flow & State Management

As a user,
I want to select a character type, enter a name, click Generate, and see the pixel avatar appear after the LLM processes my request,
So that I can create custom 8-bit avatars from my imagination.

**Acceptance Criteria:**

**Given** the prompt section is visible
**When** I see the prefix type selector
**Then** 6 options are selectable: Wizard, Knight, Robot, Astronaut, Ninja, Elf
**And** exactly one is selected at any time

**Given** I have entered my API key, selected a type, and entered a character name
**When** I click the "FORGE" button
**Then** the button becomes disabled (0.4 opacity, not-allowed cursor)
**And** the viewer switches to loading state showing the pixel-loader animation
**And** the loading state includes a blinking accent-coloured square and "GENERATING..." text
**And** Cmd/Ctrl+Enter from the prompt textarea triggers the same flow

**Given** the LLM call is in-flight
**When** `generate()` is invoked
**Then** the system prompt instructs the LLM to respond with valid JSON only
**And** the prompt follows the pattern: "Generate a pixel avatar for a [Type] character named [Name]."
**And** the response must match the schema: `{ palette: string[], grid: string[][], label: string }`

**Given** the LLM responds with valid JSON
**When** the response is parsed and validated
**Then** the viewer switches from loading to result state
**And** the error display is hidden
**And** the avatar data is available for rendering

**Given** the LLM responds with malformed JSON or missing fields
**When** validation fails
**Then** a human-readable error is shown in the red-bordered error box
**And** the error message is specific (e.g., "Missing required field: grid")

**Given** the API call fails (network error, auth failure, timeout)
**When** the error occurs
**Then** a specific error message is shown (e.g., "API 401: Invalid API key")
**And** controls are re-enabled for another attempt

### Story 2.3: Avatar Rendering, Loading Indicator & PNG Export

As a user,
I want to see my pixel avatar rendered on screen and download it as a PNG,
So that I can use it as a profile picture or game asset.

**Acceptance Criteria:**

**Given** a valid pixel map is available
**When** the result state is active
**Then** the avatar grid renders as coloured `<div>` cells in a CSS Grid layout
**And** each cell's background colour matches the hex value from the LLM response
**And** the grid is scaled to a visible size (e.g. 256×256 px)
**And** the label from the response is displayed beneath the grid in Press Start 2P font
**And** the avatar is inside a container with black background, 4px border, and 8px 8px offset shadow
**And** metadata text shows pixel size and palette info

**Given** the avatar is displayed
**When** I click "DOWNLOAD PNG"
**Then** a PNG file is downloaded with filename `pixelforce-[type]-[username].png`
**And** the download is entirely client-side via canvas.toBlob
**And** no network request is made during export

**Given** the avatar is displayed
**When** I click "RE-FORGE"
**Then** the generation flow restarts from the prompt input
**And** controls are re-enabled for a new generation

**Given** no avatar has been generated
**When** I view the avatar section
**Then** only the empty state is visible
**And** the download and re-forge buttons are not shown

**Given** the loading state is active
**When** the pixel-loader renders
**Then** a 48×48px accent-coloured square blinks at 0.6s step-end interval
**And** "GENERATING..." text pulses at 1.5s step-end interval

