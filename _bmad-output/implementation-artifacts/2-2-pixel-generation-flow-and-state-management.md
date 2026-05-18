# Story 2.2: Pixel Generation Flow & State Management

Status: ready-for-dev

## Story

As a user,
I want to select a character type, enter a name, click Generate, and see the pixel avatar appear after the LLM processes my request,
So that I can create custom 8-bit avatars from my imagination.

## Acceptance Criteria

1. **Given** the prompt section is visible, **When** I see the prefix type selector, **Then** 6 options are selectable: Wizard, Knight, Robot, Astronaut, Ninja, Elf, **And** exactly one is selected at any time.

2. **Given** the ControlPanel shows character type chips, **When** I click a chip, **Then** that type becomes the selected prefix, **And** it is visually highlighted compared to unselected chips, **And** the textarea gets pre-filled with that type's example prompt.

3. **Given** I have entered my API key, selected a type, and entered a character name, **When** I click the "FORGE" button, **Then** the button becomes disabled (0.4 opacity, not-allowed cursor), **And** the viewer switches to loading state showing the pixel-loader animation, **And** the loading state includes a blinking accent-coloured square and "GENERATING..." text, **And** Cmd/Ctrl+Enter from the prompt textarea triggers the same flow.

4. **Given** the LLM call is in-flight, **When** `generate()` is invoked, **Then** the system prompt instructs the LLM to respond with valid JSON only, **And** the prompt follows the pattern: "Generate a pixel avatar for a [Type] character named [Name].", **And** the response must match the schema: `{ palette: string[], grid: string[][], label: string }`.

5. **Given** the LLM responds with valid JSON, **When** the response is parsed and validated, **Then** the viewer switches from loading to result state, **And** the error display is hidden, **And** the avatar data is available for rendering.

6. **Given** the LLM responds with malformed JSON or missing fields, **When** validation fails, **Then** a human-readable error is shown in the red-bordered error box, **And** the error message is specific (e.g., "Missing required field: grid").

7. **Given** the API call fails (network error, auth failure, timeout), **When** the error occurs, **Then** a specific error message is shown (e.g., "API 401: Invalid API key"), **And** controls are re-enabled for another attempt.

## Tasks / Subtasks

- [ ] Create `usePixelGeneration` hook in `src/hooks/usePixelGeneration.ts`
  - [ ] State: `pixelMap`, `isGenerating`, `error`, `selectedType`
  - [ ] `generate(prompt: string)` function that calls `llmClient.generate()`
  - [ ] On success: set `pixelMap`, clear `error`, set `isGenerating = false`
  - [ ] On parse failure: set descriptive error message
  - [ ] On API error: set error with status code and message
  - [ ] `reset()` function to clear state for re-forge
  - [ ] `setSelectedType()` for prefix selection
- [ ] Update `ControlPanel` to support prefix type selection
  - [ ] UPDATE: Add `selectedType` prop and `onTypeSelect` callback
  - [ ] UPDATE: Selected chip has accent-coloured border and text
  - [ ] UPDATE: Clicking chip sets type AND pre-fills textarea with example prompt
  - [ ] Chip labels: Wizard, Knight, Robot, Astronaut, Ninja, Elf
  - [ ] Each chip has a default example prompt for its type
- [ ] Update `App.tsx` to wire up generation flow
  - [ ] UPDATE: Use `usePixelGeneration` hook
  - [ ] UPDATE: `handleGenerate` calls `generate()` with constructed prompt
  - [ ] UPDATE: Construct prompt: "Generate a pixel avatar for a [Type] character named [Name]."
  - [ ] UPDATE: Pass `isGenerating`, `pixelMap`, `error` to `ViewerShell`
  - [ ] UPDATE: Pass `selectedType` and `onTypeSelect` to `ControlPanel`
- [ ] Update `ViewerShell` to handle loading and error states
  - [ ] UPDATE: Accept `isGenerating`, `pixelMap`, `error` props
  - [ ] UPDATE: Show loading state when `isGenerating` is true
  - [ ] UPDATE: Show error state when `error` is set
  - [ ] UPDATE: Show result state when `pixelMap` is available
  - [ ] Loading state: pixel-loader animation + "GENERATING..." text
  - [ ] Error state: red-bordered box with error message
- [ ] Create `ErrorDisplay` component
  - [ ] File: `src/components/ErrorDisplay/ErrorDisplay.tsx`
  - [ ] CSS module: `src/components/ErrorDisplay/ErrorDisplay.module.css`
  - [ ] Red border, `--danger` colour scheme
  - [ ] Displays error message text
  - [ ] Dismiss button or re-enable on re-generate
- [ ] Write tests
  - [ ] `usePixelGeneration`: generates prompt format, handles success/error
  - [ ] `usePixelGeneration`: resets state correctly
  - [ ] `ControlPanel`: selected type chip is highlighted
  - [ ] `ControlPanel`: clicking chip selects type and fills textarea
  - [ ] `ErrorDisplay`: renders error message
  - [ ] `ViewerShell`: shows loading state with animation
  - [ ] `ViewerShell`: shows error state with error box

## Dev Notes

### Prompt Construction

```
"Generate a pixel avatar for a [Type] character named [Name]."
```

Where `[Type]` is the selected prefix (e.g., "Wizard") and `[Name]` is the textarea value. The system prompt (defined in Story 2.1) enforces JSON-only response.

### Example Prompts Per Type

- **Wizard**: "A wise old wizard with a long flowing beard, wearing deep blue robes adorned with golden crescent moons, holding a sparkling staff"
- **Knight**: "A valiant knight in shining silver armor with a crimson cape, wielding a broadsword, standing ready for battle"
- **Robot**: "A sleek chrome robot with glowing blue optic sensors, exposed circuitry, and mechanical joints"
- **Astronaut**: "A modern astronaut in a white space suit with a gold-visored helmet, floating against a starfield"
- **Ninja**: "A shadowy ninja in dark grey attire, face partially covered, poised in a stealthy combat stance"
- **Elf**: "A mystical forest elf with pointed ears wearing earthy green and brown leather, bow slung across back"

### usePixelGeneration Hook

```typescript
export function usePixelGeneration() {
  const [pixelMap, setPixelMap] = useState<PixelMapResponse | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedType, setSelectedType] = useState<string>('Wizard')

  const generate = useCallback(async (prompt: string, config: ProviderConfig & { apiKey: string }) => {
    setIsGenerating(true)
    setError(null)
    setPixelMap(null)

    const result = await llmClient.generate(config.type, {
      prompt,
      apiUrl: config.apiUrl,
      model: config.model,
      apiKey: config.apiKey,
    })

    if (result.ok) {
      setPixelMap(result.data)
    } else {
      setError(result.error.message)
      // Map AppError codes to user-friendly messages
      if (result.error.code === 'API_ERROR' && result.error.status === 401) {
        setError('Invalid API key. Please check your key and try again.')
      }
    }
    setIsGenerating(false)
  }, [])

  const reset = useCallback(() => {
    setPixelMap(null)
    setIsGenerating(false)
    setError(null)
  }, [])

  return { pixelMap, isGenerating, error, selectedType, setSelectedType, generate, reset }
}
```

### App.tsx Changes

- Add `usePixelGeneration` import
- Add state: `selectedType`, `pixelMap`, `error`
- `handleGenerate`:
  - Construct prompt: `Generate a pixel avatar for a ${selectedType} character named ${prompt}.`
  - Call `generate(fullPrompt, { providerType, apiUrl, model, apiKey })`
- Pass new props to `ControlPanel`: `selectedType`, `onTypeSelect`
- Pass new props to `ViewerShell`: `pixelMap`, `isGenerating`, `error`, `selectedType`
- Add `reset` callback for re-forge (wired in Story 2.3)

### ViewerShell State Transitions

```
empty → loading → result
                → error → empty (re-forge)
```

- **empty**: Pixel icon + "ENTER A PROMPT & FORGE YOUR PIXEL"
- **loading**: Pixel-loader animation + "GENERATING..."
- **result**: Avatar grid (rendered in Story 2.3)
- **error**: Red-bordered error box with message

### Architecture Compliance

- State management via React hooks — no external state library
- `Result<T, E>` pattern used via llmClient
- Error messages are human-readable, specific, and actionable
- All components in `src/components/[Name]/` with co-located CSS module + tests
- Named exports only (no `export default`)
- Imports via `@/` path alias
- Data flows down, callbacks flow up from `App.tsx`

### File Structure

```
src/
├── App.tsx                              # UPDATE: Wire up generation state, pass props to children
├── hooks/
│   └── usePixelGeneration.ts            # NEW: Generation state hook
├── components/
│   ├── ControlPanel/
│   │   ├── ControlPanel.tsx             # UPDATE: Add type selection, update props
│   │   └── ControlPanel.module.css      # UPDATE: Selected chip styles
│   ├── ViewerShell/
│   │   ├── ViewerShell.tsx              # UPDATE: Loading + error states
│   │   └── ViewerShell.module.css       # UPDATE: Loading + error state styles
│   └── ErrorDisplay/
│       ├── ErrorDisplay.tsx             # NEW: Error box component
│       ├── ErrorDisplay.module.css      # NEW: Error box styles
│       └── ErrorDisplay.test.tsx        # NEW: Error display tests
```

### Testing Requirements

- Vitest + React Testing Library
- Mock `llmClient.generate()` with vi.fn()
- Test `usePixelGeneration`: success updates pixelMap, API error sets error message, parse failure sets error
- Test `ControlPanel`: selected type chip has highlight class, clicking chip selects type + fills textarea
- Test `ViewerShell`: loading state shows pixel-loader animation div, error state shows ErrorDisplay
- Test `ErrorDisplay`: renders message text with `--danger` styling

## File List

- `src/hooks/usePixelGeneration.ts` — NEW: Generation state hook with generate/reset
- `src/components/ErrorDisplay/ErrorDisplay.tsx` — NEW: Error box component
- `src/components/ErrorDisplay/ErrorDisplay.module.css` — NEW: Error box styles
- `src/components/ErrorDisplay/ErrorDisplay.test.tsx` — NEW: Error display tests
- `src/components/ControlPanel/ControlPanel.tsx` — UPDATE: Add type selection props and visual feedback
- `src/components/ControlPanel/ControlPanel.module.css` — UPDATE: Selected chip state styles
- `src/components/ViewerShell/ViewerShell.tsx` — UPDATE: Loading + error state rendering
- `src/components/ViewerShell/ViewerShell.module.css` — UPDATE: Loading + error state styles
- `src/App.tsx` — UPDATE: Wire usePixelGeneration hook, pass props

## Change Log

- 2026-05-18: Created pixel generation flow with usePixelGeneration hook, ControlPanel type selection, ViewerShell loading/error states, ErrorDisplay component

## References

- [Epics: Story 2.2](epics.md#L323-L363) — Full acceptance criteria
- [Architecture: State Flow](architecture.md#L180-L183) — App.tsx owns all state
- [Architecture: Component Tree](architecture.md#L120) — Component hierarchy
- [UX: Avatar Viewer States](ux-design-specification.md#L337-L339) — Empty, loading, result, error
- [UX: Pixel Loader](ux-design-specification.md#L341-L343) — Blinking square animation
- [UX: Feedback Patterns](ux-design-specification.md#L362-L367) — All four viewer states
- [UX: Experience Mechanics](ux-design-specification.md#L207-L211) — Initiate → Action → Feedback → Complete
- [UX: Example Chips](ux-design-specification.md#L332-L336) — Chip interaction pattern
- [PRD: FR-3](prd.md#L61-L66) — Prefix type selector
- [PRD: FR-4](prd.md#L68-L83) — LLM prompt contract
- [PRD: FR-6](prd.md#L96-L101) — Loading indicator
- [PRD: NFR-4](prd.md#L156) — Error handling
