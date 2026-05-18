# Story 2.1: LLM Provider Abstraction Layer

Status: review

## Story

As a developer,
I want a pluggable LLM provider abstraction with implementations for Anthropic, OpenAI, OpenAI-Compatible, and DeepSeek,
So that the app can generate pixel maps from any supported provider through a unified interface.

## Acceptance Criteria

1. **Given** the provider abstraction is designed, **When** I inspect the `LLMProvider` interface, **Then** it defines a `generate(request: PixelGenRequest): Promise<Result<PixelMapResponse, AppError>>` method, **And** `PixelGenRequest` includes `prompt`, `apiUrl`, `model`, `apiKey`, **And** `PixelMapResponse` matches the schema `{ palette: string[], grid: string[][], label: string }`, **And** `AppError` includes `message`, `code`, and optional `status` fields.

2. **Given** the AnthropicProvider receives a request, **When** `generate()` is called, **Then** it sends POST to `{apiUrl}/v1/messages` with `x-api-key` header, **And** the request body uses the Messages API format, **And** on success, it parses the JSON content block and returns `{ ok: true, data: PixelMapResponse }`.

3. **Given** the OpenAIProvider receives a request, **When** `generate()` is called, **Then** it sends POST to `{apiUrl}/v1/chat/completions` with `Bearer` auth header, **And** the request body uses Chat Completions format, **And** on success, it parses the response content and returns the parsed pixel map.

4. **Given** the OpenAICompatibleProvider receives a request, **When** `generate()` is called, **Then** it follows the Chat Completions format with `Bearer` auth, **And** defaults to `meta-llama/Llama-3.3-70B-Instruct-Turbo` model via Together AI.

5. **Given** the DeepSeekProvider receives a request, **When** `generate()` is called, **Then** it sends POST to `{apiUrl}/v1/chat/completions` with `Bearer` auth header, **And** defaults to `deepseek-v4-flash` model.

6. **Given** any provider encounters an API error, **When** the response is non-2xx, **Then** it returns `{ ok: false, error: AppError }` with the status code and error details, **And** network failures are caught and returned as typed errors.

7. **Given** the `llmClient` receives a provider type and config, **When** it dispatches to the appropriate provider, **Then** it instantiates the correct provider class and calls `generate()`.

## Tasks / Subtasks

- [x] Add TypeScript types for LLM provider layer
  - [x] Add `PixelGenRequest` interface to `src/types/pixelmap.ts`
  - [x] Add `PixelMapResponse` interface to `src/types/pixelmap.ts`
  - [x] Add `AppError` interface to `src/types/pixelmap.ts`
  - [x] Add `Result<T, E>` union type to `src/types/pixelmap.ts`
- [x] Create `LLMProvider` interface in `src/services/providers.ts`
  - [x] `generate(request: PixelGenRequest): Promise<Result<PixelMapResponse, AppError>>`
- [x] Create `AnthropicProvider` in `src/services/AnthropicProvider.ts`
  - [x] POST to `{apiUrl}/v1/messages` with `x-api-key` header
  - [x] Messages API format (system, messages array)
  - [x] Parse JSON from content block
  - [x] Error handling for non-2xx and network failures
- [x] Create `OpenAIProvider` in `src/services/OpenAIProvider.ts`
  - [x] POST to `{apiUrl}/v1/chat/completions` with `Bearer` auth
  - [x] Chat Completions format (system prompt in messages array)
  - [x] Parse response content
  - [x] Error handling for non-2xx and network failures
- [x] Create `OpenAICompatibleProvider` in `src/services/OpenAICompatibleProvider.ts`
  - [x] Same API as OpenAI (extend/dry with base class)
  - [x] Default model: `meta-llama/Llama-3.3-70B-Instruct-Turbo`
- [x] Create `DeepSeekProvider` in `src/services/DeepSeekProvider.ts`
  - [x] Same Chat Completions format as OpenAI
  - [x] Default model: `deepseek-v4-flash`
- [x] Create `llmClient` in `src/services/llmClient.ts`
  - [x] `generate(providerType: LLMProviderType, request: PixelGenRequest): Promise<Result<PixelMapResponse, AppError>>`
  - [x] Map provider type to correct provider instance
  - [x] Re-export typed error handling
- [x] Write tests for all provider implementations
  - [x] Mock `fetch` for each provider's API format
  - [x] Test success response parsing
  - [x] Test non-2xx error handling
  - [x] Test network failure handling
  - [x] Test `llmClient` dispatch logic

## Dev Notes

### Type Definitions (add to `src/types/pixelmap.ts`)

```typescript
export interface PixelGenRequest {
  prompt: string
  apiUrl: string
  model: string
  apiKey: string
}

export interface PixelMapResponse {
  palette: string[]
  grid: string[][]
  label: string
}

export interface AppError {
  message: string
  code: string
  status?: number
}

export type Result<T, E = AppError> =
  | { ok: true; data: T }
  | { ok: false; error: E }
```

### System Prompt for All Providers

Every provider must send this system prompt to enforce JSON-only responses:

```
You are a pixel avatar generator. Respond ONLY with valid JSON matching this schema:
{
  "palette": ["#RRGGBB", ...],
  "grid": [["#RRGGBB", ...], ...],
  "label": "character name"
}
The grid must be 16x16, every cell a valid 6-digit hex color. Use a reduced 64-color NES-inspired palette. The label is the display name shown beneath the avatar.
```

### Anthropic Messages API Format

```typescript
const body = {
  model: request.model,
  max_tokens: 4096,
  system: SYSTEM_PROMPT,
  messages: [{ role: 'user', content: request.prompt }],
}
```

Response: `response.content[0].text` contains the JSON string.

### OpenAI / OpenAI-Compatible / DeepSeek Chat Completions Format

```typescript
const body = {
  model: request.model,
  max_tokens: 4096,
  messages: [
    { role: 'system', content: SYSTEM_PROMPT },
    { role: 'user', content: request.prompt },
  ],
}
```

Response: `response.choices[0].message.content` contains the JSON string.

### Error Handling Pattern

```typescript
async generate(request: PixelGenRequest): Promise<Result<PixelMapResponse, AppError>> {
  try {
    const response = await fetch(url, { ... })
    if (!response.ok) {
      return { ok: false, error: { message: `API ${response.status}: ${statusText}`, code: 'API_ERROR', status: response.status } }
    }
    const data = await response.json()
    const parsed = parsePixelMap(data) // validate against schema
    if (!parsed.ok) return parsed
    return { ok: true, data: parsed.data }
  } catch (err) {
    return { ok: false, error: { message: `Network error: ${err instanceof Error ? err.message : 'Unknown'}`, code: 'NETWORK_ERROR' } }
  }
}
```

### Architecture Compliance

- `Result<T, E>` pattern for all async operations — no thrown exceptions
- Strategy pattern via `LLMProvider` interface — `llmClient` dispatches by type
- Named exports only (no `export default`)
- Imports via `@/` path alias
- All types in `src/types/pixelmap.ts`
- Each provider in its own file under `src/services/`
- Tests co-located next to source files
- `LLMProviderType` union type already exists in `src/types/pixelmap.ts`

### File Structure

```
src/
├── types/
│   └── pixelmap.ts                  # UPDATE: Add PixelGenRequest, PixelMapResponse, AppError, Result
├── services/
│   ├── llmClient.ts                 # NEW: Dispatch layer, maps provider type → provider instance
│   ├── providers.ts                 # NEW: LLMProvider interface definition
│   ├── AnthropicProvider.ts         # NEW: Anthropic Messages API implementation
│   ├── OpenAIProvider.ts            # NEW: OpenAI Chat Completions implementation
│   ├── OpenAICompatibleProvider.ts  # NEW: OpenAI-Compatible (Together AI) implementation
│   └── DeepSeekProvider.ts          # NEW: DeepSeek Chat Completions implementation
```

### Testing Requirements

- Vitest for test runner
- Mock `global.fetch` using `vi.fn()` for each provider test
- Test each provider independently with mocked responses
- Test `llmClient` dispatch: verify correct provider is instantiated per type
- Test response parsing: valid JSON, malformed JSON, missing fields
- Test error handling: 401, 500, network timeout, network failure
- No React Testing Library needed — pure service-layer tests

## File List

- `src/types/pixelmap.ts` — UPDATE: Add `PixelGenRequest`, `PixelMapResponse`, `AppError`, `Result<T,E>`
- `src/services/providers.ts` — NEW: `LLMProvider` interface
- `src/services/llmClient.ts` — NEW: Provider dispatch, `generate()` entry point
- `src/services/AnthropicProvider.ts` — NEW: Anthropic API implementation
- `src/services/OpenAIProvider.ts` — NEW: OpenAI API implementation
- `src/services/OpenAICompatibleProvider.ts` — NEW: Together AI implementation
- `src/services/DeepSeekProvider.ts` — NEW: DeepSeek API implementation

## Change Log

- 2026-05-18: Created LLM provider abstraction layer with Strategy pattern, 4 provider implementations, and llmClient dispatch

## References

- [Epics: Story 2.1](epics.md#L277-L321) — Full acceptance criteria
- [Architecture: API & Communication Patterns](architecture.md#L125-L133) — LLMProvider interface, Result pattern
- [Architecture: Project Structure](architecture.md#L254-L267) — services/ directory layout
- [PRD: FR-5](prd.md#L85-L93) — Multi-provider LLM support
- [PRD: FR-4](prd.md#L68-L83) — LLM prompt contract
- [PRD: NFR-4](prd.md#L156) — Error handling requirement
