# Story 1.3: API Key Input & Provider Configuration

Status: ready-for-dev

## Story

As a user,
I want to enter my API key securely and configure my LLM provider,
So that I can authenticate with the LLM API while keeping my key private.

## Acceptance Criteria

1. **Given** the config section is visible, **When** I see the API key field, **Then** it is `type="password"` by default, **And** there is a toggle button labelled "SHOW", **When** I click "SHOW", **Then** the input switches to `type="text"` and the button reads "HIDE", **And** clicking "HIDE" returns the input to `type="password"`.

2. **Given** I enter an API key, **When** I refresh the page in the same tab, **Then** the key persists from `sessionStorage`, **When** I close and reopen the tab, **Then** the key field is empty (sessionStorage cleared).

3. **Given** the provider dropdown, **When** I open it, **Then** I see 4 options: Anthropic, OpenAI, OpenAI-Compatible, DeepSeek, **When** I select "Anthropic", **Then** the API URL field fills with Anthropic's Messages API URL, **And** the model field fills with `claude-sonnet-4-20250514`, **When** I select "OpenAI", **Then** the API URL fills with `https://api.openai.com`, **And** the model fills with `gpt-4o`, **When** I select "OpenAI-Compatible", **Then** the API URL fills with the Together AI endpoint, **And** the model fills with `meta-llama/Llama-3.3-70B-Instruct-Turbo`, **When** I select "DeepSeek", **Then** the API URL fills with DeepSeek's endpoint, **And** the model fills with `deepseek-v4-flash`.

4. **Given** I modify the API URL or model fields, **When** the provider changes, **Then** the manual edits are preserved (user overrides presets).

5. **Given** I enter config values and click Generate, **When** the generation completes, **Then** provider, API URL, model, and API key are saved to `localStorage`, **And** the "Settings saved locally" notice is visible, **When** I reload the page, **Then** all config fields are restored from `localStorage`.

6. **Given** the custom select is closed, **When** I click the trigger, **Then** the dropdown opens, **And** the selected option displays with accent background, **And** options show hover highlight.

## Tasks / Subtasks

- [ ] Create `types/pixelmap.ts` with core type definitions
  - [ ] Define `LLMProviderType` union: `'anthropic' | 'openai' | 'openai-compatible' | 'deepseek'`
  - [ ] Define `ProviderConfig` interface: `{ type: LLMProviderType; apiUrl: string; model: string; apiKey: string }`
  - [ ] Define provider presets map with URL, model defaults
- [ ] Create `useApiKey` hook in `src/hooks/useApiKey.ts`
  - [ ] Manage key state with sessionStorage read/write
  - [ ] Expose `apiKey`, `setApiKey`, `clearKey`
  - [ ] Key must never be written to localStorage
- [ ] Create `ApiKeyInput` component
  - [ ] File: `src/components/ApiKeyInput/ApiKeyInput.tsx`
  - [ ] CSS module: `src/components/ApiKeyInput/ApiKeyInput.module.css`
  - [ ] Test: `src/components/ApiKeyInput/ApiKeyInput.test.tsx`
  - [ ] Password-type input with show/hide toggle button
  - [ ] Toggle button text: "SHOW" / "HIDE"
  - [ ] 44px minimum touch target
  - [ ] Accent-coloured focus border
  - [ ] Monospace font stack for the input
- [ ] Create `ProviderSelect` custom dropdown component
  - [ ] File: `src/components/ProviderSelect/ProviderSelect.tsx`
  - [ ] CSS module: `src/components/ProviderSelect/ProviderSelect.module.css`
  - [ ] Test: `src/components/ProviderSelect/ProviderSelect.test.tsx`
  - [ ] Trigger button shows current value + arrow indicator
  - [ ] Dropdown opens/closes on trigger click
  - [ ] 4 options: Anthropic, OpenAI, OpenAI-Compatible, DeepSeek
  - [ ] Selected option highlighted with accent background
  - [ ] Hover state on options (accent tint)
  - [ ] Clicking an option closes dropdown and selects it
  - [ ] Keyboard navigation: Enter to toggle, Arrow keys to navigate, Enter to select, Escape to close
- [ ] Create provider config form in App.tsx
  - [ ] Provider dropdown changes auto-fill API URL and model
  - [ ] API URL and model fields are editable text inputs
  - [ ] Manual edits preserved when provider changes (user overrides)
  - [ ] "Settings saved locally" toast/notice on config save
  - [ ] Config persistence: save to localStorage on successful generate
  - [ ] Restore config from localStorage on page load
- [ ] Write tests
  - [ ] ApiKeyInput: renders as type=password by default
  - [ ] ApiKeyInput: toggle switches type between password/text
  - [ ] ApiKeyInput: show/hide button text changes correctly
  - [ ] ProviderSelect: renders trigger with current value
  - [ ] ProviderSelect: opens dropdown on click
  - [ ] ProviderSelect: selecting option updates value and closes dropdown
  - [ ] ProviderSelect: all 4 options present
  - [ ] Provider config: selecting provider fills URL + model defaults
  - [ ] Provider config: manual overrides preserved after provider change
  - [ ] Config persistence: saved to localStorage, restored on reload

## Dev Notes

### Provider Presets Config

```typescript
interface ProviderPreset {
  type: LLMProviderType;
  label: string;
  apiUrl: string;
  model: string;
}

const PROVIDER_PRESETS: ProviderPreset[] = [
  {
    type: 'anthropic',
    label: 'Anthropic',
    apiUrl: 'https://api.anthropic.com',
    model: 'claude-sonnet-4-20250514',
  },
  {
    type: 'openai',
    label: 'OpenAI',
    apiUrl: 'https://api.openai.com',
    model: 'gpt-4o',
  },
  {
    type: 'openai-compatible',
    label: 'OpenAI-Compatible',
    apiUrl: 'https://api.together.xyz',
    model: 'meta-llama/Llama-3.3-70B-Instruct-Turbo',
  },
  {
    type: 'deepseek',
    label: 'DeepSeek',
    apiUrl: 'https://api.deepseek.com',
    model: 'deepseek-v4-flash',
  },
]
```

### Session Storage Rules

- API key stored in `sessionStorage` under key `pixelforge-api-key`
- API key NEVER stored in `localStorage` — explicitly verify this in tests
- `sessionStorage` cleared on tab close, survives page refresh within tab
- `localStorage.getItem('pixelforge-api-key')` must always return `null`

### LocalStorage Config Keys

- `pixelforge-provider` — provider type string
- `pixelforge-api-url` — API URL
- `pixelforge-model` — model name
- `pixelforge-api-key` — API key (ONLY saved after successful generate, alongside sessionStorage)

### Key Security Rules (from PRD)

- Key held in JS variable + sessionStorage only
- Never sent to any server except the configured LLM API
- Never written to localStorage, cookies, or logs
- No server-side component receives the key (NFR-1)

### Architecture Compliance

- `useApiKey` hook in `src/hooks/` — encapsulates sessionStorage logic
- Components in `src/components/ApiKeyInput/` and `src/components/ProviderSelect/`
- Each component has co-located `.module.css` and `.test.tsx`
- Named exports only; imports via `@/` path alias
- `Result<T, E>` error handling pattern not needed here (sync input validation)
- Props typed via exported interfaces
- CSS custom properties for all visual tokens — no hardcoded colours

### File Structure

```
src/
├── types/
│   └── pixelmap.ts              # LLMProviderType, ProviderConfig, ProviderPreset types
├── hooks/
│   └── useApiKey.ts             # sessionStorage-backed API key state
├── components/
│   ├── ApiKeyInput/
│   │   ├── ApiKeyInput.tsx
│   │   ├── ApiKeyInput.module.css
│   │   └── ApiKeyInput.test.tsx
│   └── ProviderSelect/
│       ├── ProviderSelect.tsx
│       ├── ProviderSelect.module.css
│       └── ProviderSelect.test.tsx
└── App.tsx                      # Manages config state, mounts ApiKeyInput + ProviderSelect
```

### Testing Requirements

- Vitest + React Testing Library
- Mock `sessionStorage` and `localStorage` for persistence tests
- Test custom dropdown: open/close, option selection, keyboard navigation
- Verify API key is NOT persisted to localStorage (negative test)
- Verify show/hide toggle toggles input type

## References

- [Epics: Story 1.3](epics.md#L178-L232) — Full acceptance criteria
- [Epics: FR-1, FR-2](epics.md#L22-L25) — API key requirements
- [Epics: UX-DR6, UX-DR15](epics.md#L70-L71) — Custom select, config persistence
- [Architecture: Auth/Security](architecture.md#L135-L139) — BYOK, no server-side
- [Architecture: Component Structure](architecture.md#L120-L121) — Component tree
- [Architecture: Naming Patterns](architecture.md#L151-L158) — Component file conventions
- [PRD: FR-1, FR-2](prd.md#L40-L55) — Masked input + session-only storage
- [PRD: FR-5](prd.md#L85-L93) — Multi-provider support
- [PRD: AR-11](prd.md#L58) — Auth header format
- [UX: Custom Components](ux-design-specification.md#L310-L351) — Custom select spec
- [UX: Effortless Interactions](ux-design-specification.md#L47-L53) — Provider presets, config persistence
