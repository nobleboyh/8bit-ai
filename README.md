# PixelForge — 8-Bit Avatar Generator

Generate retro 8-bit pixel avatars using LLMs (Anthropic, OpenAI, OpenAI-Compatible, DeepSeek). Fully client-side — your API key never leaves your browser.

## Layout

```
┌──────────────────────────────────────────────┐
│  PIXELFORGE                      [DARK/LIGHT]│
│  8-BIT AVATAR GENERATOR                      │
├──────────────────────────────────────────────┤
│  01 // CONFIG                                │
│  ┌────────────────────────────────────────┐  │
│  │ Provider    [Anthropic  ▼]             │  │
│  │ API URL     [________________]         │  │
│  │ Model       [________________]         │  │
│  │ API Key     [********] [SHOW]          │  │
│  └────────────────────────────────────────┘  │
├──────────────────────────────────────────────┤
│  02 // PROMPT                                │
│  ┌─────────────────────────────────┐         │
│  │ Describe your character...      │ [FORGE] │
│  └─────────────────────────────────┘         │
│  [Wizard] [Knight] [Robot] [Astronaut]       │
│  [Ninja]  [Elf]                              │
├──────────────────────────────────────────────┤
│  03 // AVATAR                                │
│  ┌──────────────────────────────────────┐    │
│  │          ▣                           │    │
│  │   ENTER A PROMPT & FORGE YOUR PIXEL  │    │
│  └──────────────────────────────────────┘    │
└──────────────────────────────────────────────┘
```

## How to Run

```bash
# Install dependencies
npm install

# Start dev server with HMR
npm run dev

# Run tests
npm test

# Build single-file distribution
npm run build
```

Open `dist/index.html` in any modern browser after building, or visit the URL shown by `npm run dev`.

## How to Use

1. **Configure** — Select your LLM provider, enter your API URL and model, then paste your API key.
2. **Prompt** — Type a character description or click an example chip (Wizard, Knight, Robot, Astronaut, Ninja, Elf). Press **FORGE** or **Cmd/Ctrl+Enter** to generate.
3. **Avatar** — Your pixel avatar renders here. (Coming in Epic 2.)

### Supported Providers

| Provider | API URL | Default Model |
|----------|---------|---------------|
| Anthropic | `https://api.anthropic.com` | `claude-sonnet-4-20250514` |
| OpenAI | `https://api.openai.com` | `gpt-4o` |
| OpenAI-Compatible | `https://api.together.xyz` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` |
| DeepSeek | `https://api.deepseek.com` | `deepseek-v4-flash` |

### Theme Toggle

Click **DARK** / **LIGHT** in the header to switch themes. Your preference is saved to localStorage.

### Build Output

`npm run build` produces a single `dist/index.html` with all JS and CSS inlined — no server required.

## Tech Stack

- **Vite 6** + **React 18** + **TypeScript** (strict mode)
- **CSS Modules** with CSS custom properties for theming
- **Vitest** + **React Testing Library** for testing
- **vite-plugin-singlefile** for portable single-file builds

## Project Structure

```
src/
├── components/
│   ├── ApiKeyInput/       # Masked API key input
│   ├── ControlPanel/      # Prompt textarea + forge button + chips
│   ├── ProviderSelect/    # Custom provider dropdown
│   ├── ThemeToggle/       # Dark/light toggle
│   └── ViewerShell/       # Avatar viewer container
├── hooks/
│   ├── useApiKey.ts       # sessionStorage-backed API key
│   ├── useProviderConfig.ts # Provider config with localStorage
│   └── useTheme.ts        # Theme state + persistence
├── types/
│   └── pixelmap.ts        # Type definitions + provider presets
├── App.tsx                # Root layout + state orchestration
├── App.module.css         # Global styles + design tokens
└── main.tsx               # Entry point
```
