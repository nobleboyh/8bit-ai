---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
workflowType: 'architecture'
lastStep: 8
status: 'complete'
completedAt: '2026-05-18'
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-8bit-ai-2026-05-18/prd.md
project_name: '8bit-ai'
user_name: 'Itobeo'
date: '2026-05-18'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
- FR-1/FR-2: API Key Entry — masked input with show/hide, sessionStorage-only persistence
- FR-3/FR-4/FR-5/FR-6: LLM Pixel Generation — 6 prefix types, multi-provider (Anthropic, OpenAI, OpenAI-Compatible), strict JSON schema enforcement, loading indicator
- FR-7/FR-8: Avatar Rendering — CSS Grid of coloured divs, label display
- FR-9: PNG Export — offscreen canvas toBlob() download
- FR-10: Theme Toggle — dark/light, localStorage persistence

**Non-Functional Requirements:**
- NFR-1: API key never leaves browser
- NFR-2: No user data stored/logged
- NFR-3: Single-file .html, no server
- NFR-4: Human-readable error handling
- NFR-5: Chrome 110+, Firefox 115+, Safari 16+
- NFR-6: Design fidelity (Press Start 2P, scanline overlay, matching reference)

**Scale & Complexity:**
- Primary domain: Client-side web (single-file HTML with build step)
- Complexity level: Low
- Estimated architectural components: 6 (API Key Manager, LLM Provider Abstraction, Pixel Map Parser/Validator, Avatar Renderer, PNG Exporter, Theme System)

### Technical Constraints & Dependencies

- Single-file output constraint (build → inline → one .html)
- Direct browser-to-LLM fetch() calls (no proxy, CORS considerations)
- Multi-provider auth formats: x-api-key (Anthropic), Bearer (OpenAI, Together)
- LLM response is JSON — must validate against pixel map schema before rendering
- Canvas API dependency for PNG export
- CSS Grid for pixel rendering (no canvas display required)

### Key Architecture Decision

**Tech Stack:** Vite 6 + React 18 + TypeScript
- Build output inlined to single `.html` via `vite-plugin-singlefile`
- React gives component model, hooks-based state, and maintainability
- TypeScript ensures type safety for LLM JSON schemas
- HMR for fast development, zero-config production build

## Starter Template Evaluation

### Primary Technology Domain

Client-side web application — single-file HTML with build-time inlining.

### Selected Starter: Vite + React + TypeScript (`react-ts` template)

**Initialization Command:**

```bash
npm create vite@latest pixelforge -- --template react-ts
cd pixelforge
npm install
npm install -D vite-plugin-singlefile
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
- TypeScript (strict mode), React 18+/19, targeting ES2020+
- Node.js 20.19+ required for development

**Styling Solution:**
- Vanilla CSS (inlined by vite-plugin-singlefile at build time)
- CSS custom properties for theme tokens (dark/light)

**Build Tooling:**
- Vite (esbuild for transforms, Rollup for bundling)
- `@vitejs/plugin-react` for JSX transform and Fast Refresh
- `vite-plugin-singlefile@2.3.3` — inlines all JS/CSS into one `.html`

**Code Organization:**
- `src/components/` — React components (ApiKeyInput, AvatarGrid, ControlPanel, ThemeToggle, DownloadButton)
- `src/hooks/` — Custom React hooks (usePixelGeneration, useTheme)
- `src/services/` — LLM provider abstraction (llmClient, providers)
- `src/types/` — TypeScript type definitions (pixelmap.ts)
- `src/App.tsx` — Root component orchestrating layout
- `src/main.tsx` — Entry point

**Development Experience:**
- `npm run dev` — HMR dev server at localhost:5173
- `npm run build` — TypeScript check + Vite build → single `dist/index.html`
- Test via Vitest + React Testing Library

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- React hooks + Context API for state management (no external library)
- Strategy pattern for multi-provider LLM abstraction
- Typed error union for error handling
- Vitest for unit/integration testing

**Deferred Decisions (Post-MVP):**
- Response caching in sessionStorage (re-download without re-generate)

### Frontend Architecture

- **State management:** React hooks (`useState`, `useContext`, custom hooks)
- **Component tree:** App → ControlPanel (prefix selector, name input, generate btn), ApiKeyInput (masked input, provider select), AvatarGrid (CSS grid render), DownloadButton, ThemeToggle
- **File colocation:** Component, its CSS module, and test co-located in `src/components/[name]/`

### API & Communication Patterns

- **LLM provider abstraction:** Strategy pattern via a common interface:
  ```typescript
  interface LLMProvider {
    generate(request: PixelGenRequest): Promise<PixelMapResponse>
  }
  ```
- Implementations: `AnthropicProvider`, `OpenAIProvider`, `OpenAICompatibleProvider`, `DeepSeekProvider`
- **Error handling:** Typed union `Result<T, AppError>` pattern — `{ ok: true, data: T } | { ok: false, error: AppError }`
- Auth header format per provider: `x-api-key` (Anthropic), `Bearer` (OpenAI/OpenAI-compatible/DeepSeek)

### Authentication & Security

- BYOK — no user auth system
- Key lives in memory + sessionStorage only; explicitly block localStorage writes
- No server-side component (NFR-1, NFR-2)

### Infrastructure & Deployment

- Build output: single `dist/index.html` via vite-plugin-singlefile
- Deploy to any static host (GitHub Pages, Netlify, etc.) or open directly in browser
- No CI/CD needed for MVP — manual `npm run build` sufficient

## Implementation Patterns & Consistency Rules

### Naming Patterns

| Category | Convention | Example |
|----------|-----------|---------|
| React components | PascalCase, `.tsx` | `ApiKeyInput.tsx`, `AvatarGrid.tsx` |
| Custom hooks | camelCase with `use` prefix | `usePixelGeneration.ts`, `useTheme.ts` |
| Services/files | camelCase | `llmClient.ts`, `providers.ts` |
| Types/interfaces | PascalCase | `PixelMap`, `LLMProvider`, `AppError` |
| CSS modules | PascalCase, `.module.css` | `ApiKeyInput.module.css` |
| Test files | co-located, `.test.tsx` | `ApiKeyInput.test.tsx` |

### Structure Patterns

- **Tests:** Co-located `*.test.tsx` next to source file
- **Exports:** Named exports only (no `export default`)
- **Imports:** Absolute via `@/` alias → `@/components/ApiKeyInput`

### Process Patterns

**Error handling:**
```typescript
type Result<T, E = AppError> =
  | { ok: true; data: T }
  | { ok: false; error: E }
```

**Component pattern:**
- Props typed via exported interface
- CSS module imported directly
- Callbacks passed down from parent (no prop drilling beyond 2 levels → context)

**State flow:**
- `App.tsx` owns: `apiKey`, `pixelMap`, `loading`, `error`, `theme`
- Child components receive props + callbacks
- Custom hooks encapsulate side effects (fetch, localStorage, sessionStorage)

**CSS conventions:**
- Custom properties for theme tokens: `--bg`, `--text`, `--accent`, `--border`, `--font-mono`
- `.module.css` per component
- Scanline overlay via `::after` pseudo-element (NFR-6)

**LLM response validation:**
- Parse `JSON.parse()` → validate against `PixelMap` schema at runtime → render or show error
- Missing/invalid fields produce specific error message, not generic crash

### All AI Agents MUST

- Use the `Result<T, E>` pattern for all async operations
- Import via `@/` path aliases
- Use named exports only
- Co-locate tests with source files
- Theme via CSS custom properties, not hardcoded colours

## Project Structure & Boundaries

### Complete Project Directory Structure

```
pixelforge/
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── vite.config.ts
├── .gitignore
├── public/
│   └── favicon.svg
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── App.module.css
│   ├── components/
│   │   ├── ApiKeyInput/
│   │   │   ├── ApiKeyInput.tsx
│   │   │   ├── ApiKeyInput.module.css
│   │   │   └── ApiKeyInput.test.tsx
│   │   ├── ProviderSelect/
│   │   │   ├── ProviderSelect.tsx
│   │   │   ├── ProviderSelect.module.css
│   │   │   └── ProviderSelect.test.tsx
│   │   ├── ControlPanel/
│   │   │   ├── ControlPanel.tsx
│   │   │   ├── ControlPanel.module.css
│   │   │   └── ControlPanel.test.tsx
│   │   ├── AvatarGrid/
│   │   │   ├── AvatarGrid.tsx
│   │   │   ├── AvatarGrid.module.css
│   │   │   └── AvatarGrid.test.tsx
│   │   ├── LoadingIndicator/
│   │   │   ├── LoadingIndicator.tsx
│   │   │   └── LoadingIndicator.module.css
│   │   ├── DownloadButton/
│   │   │   ├── DownloadButton.tsx
│   │   │   └── DownloadButton.test.tsx
│   │   ├── ThemeToggle/
│   │   │   ├── ThemeToggle.tsx
│   │   │   └── ThemeToggle.test.tsx
│   │   └── ErrorDisplay/
│   │       ├── ErrorDisplay.tsx
│   │       └── ErrorDisplay.module.css
│   ├── hooks/
│   │   ├── usePixelGeneration.ts
│   │   ├── useApiKey.ts
│   │   └── useTheme.ts
│   ├── services/
│   │   ├── llmClient.ts
│   │   ├── providers.ts
│   │   ├── AnthropicProvider.ts
│   │   ├── DeepSeekProvider.ts
│   │   ├── OpenAIProvider.ts
│   │   └── OpenAICompatibleProvider.ts
│   ├── types/
│   │   └── pixelmap.ts
│   └── utils/
│       ├── pngExport.ts
│       └── validation.ts
└── dist/
    └── index.html
```

### Requirements to Structure Mapping

| FR | Component/File | Responsibility |
|----|---------------|----------------|
| FR-1/FR-2 | ApiKeyInput + useApiKey | Masked input, sessionStorage |
| FR-3 | ControlPanel | Prefix selector, name input |
| FR-4/FR-5/FR-6 | usePixelGeneration + services/* | LLM call (4 providers), validation, loading |
| FR-7/FR-8 | AvatarGrid | CSS grid render, label |
| FR-9 | DownloadButton + pngExport | Canvas PNG export |
| FR-10 | ThemeToggle + useTheme | Dark/light toggle |

### Architectural Boundaries

- **External boundary:** Only LLM API endpoints (3 providers)
- **Component boundary:** All state flows through `App.tsx` → props down, callbacks up
- **Service boundary:** Strategy pattern — single `llmClient.ts` dispatches to provider implementation
- **Data boundary:** No persistence except sessionStorage (key) and localStorage (theme)

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:** Vite 6 + React 18 + TypeScript + vite-plugin-singlefile@2.3.3 are fully compatible. vite-plugin-singlefile supports Vite 5–8. Strategy pattern for providers is independent of build tooling.

**Pattern Consistency:** All naming conventions, state flow rules, and error handling patterns align with the React + TypeScript ecosystem. No contradictions.

**Structure Alignment:** Project structure maps 1:1 to architectural decisions. Each component has a defined directory, every FR has a file owner.

### Requirements Coverage Validation ✅

**Functional Requirements Coverage:** All 10 FRs from PRD are mapped to specific components and services (see mapping table in Project Structure section).

**Non-Functional Requirements Coverage:**
- NFR-1/2 (Security/Privacy): sessionStorage-only, no server, no logging
- NFR-3 (Portability): vite-plugin-singlefile produces one .html
- NFR-4 (Error handling): Result<T,E> pattern + ErrorDisplay component
- NFR-5 (Browser compat): Vite + React targets modern browsers
- NFR-6 (Design fidelity): CSS custom properties + Press Start 2P font + scanline overlay

### Implementation Readiness Validation ✅

**Decision Completeness:** All critical decisions documented with versions (Vite 6, React 18+, TypeScript strict, vite-plugin-singlefile@2.3.3).

**Structure Completeness:** Every source file defined with clear purpose and location. 15 source files across 6 directories.

**Pattern Completeness:** 5 pattern categories documented with concrete examples and anti-patterns.

### Gap Analysis Results

**Minor Gaps (Deferred to Post-MVP):**
- LLM response caching in sessionStorage (for re-download without re-generate)
- Prompt temperature tuning (default to 0.7, experiment later)
- ESLint/Biome configuration (Vite template includes basic TS checking)

### Architecture Completeness Checklist

**Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High — all 16 checklist items confirmed, no critical gaps

### Implementation Handoff

**First Implementation Priority:**
```bash
npm create vite@latest pixelforge -- --template react-ts
cd pixelforge
npm install
npm install -D vite-plugin-singlefile
```

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented
- Use implementation patterns consistently across all components
- Respect project structure and boundaries
- Refer to this document for all architectural questions
