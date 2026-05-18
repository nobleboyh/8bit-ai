# Story 1.1: Project Scaffold & Build Tooling

Status: done

## Story

As a developer,
I want the project scaffolded with Vite 6 + React 18 + TypeScript and configured to build into a single `.html` file,
So that I can develop with HMR and produce a portable single-file output.

## Acceptance Criteria

1. **Given** the project directory does not exist, **When** I run `npm create vite@latest pixelforge -- --template react-ts`, **Then** a new project is created with Vite, React, and TypeScript configured, **And** `npm install` resolves all dependencies without errors.

2. **Given** a Vite+React project exists, **When** I install `vite-plugin-singlefile` as a dev dependency, **Then** `npm install -D vite-plugin-singlefile` succeeds.

3. **Given** vite.config.ts has the singlefile plugin configured, **When** I run `npm run build`, **Then** `dist/index.html` is produced as a single file with all JS and CSS inlined, **And** opening `dist/index.html` in a browser renders the starter page.

4. **Given** the project is scaffolded, **When** I inspect `tsconfig.json` or `vite.config.ts`, **Then** `@/` path alias is configured pointing to `src/`, **And** the directory structure matches: `src/components/`, `src/hooks/`, `src/services/`, `src/types/`, `src/utils/`.

5. **Given** TypeScript strict mode is enabled, **When** I run `npx tsc --noEmit`, **Then** no compilation errors are reported.

## Tasks / Subtasks

- [x] Scaffold project with Vite 6 + React 18 + TypeScript
  - [x] Run `npm create vite@latest pixelforge -- --template react-ts`
  - [x] Run `npm install` to resolve dependencies
  - [x] Verify `npm run dev` starts HMR server
- [x] Configure single-file build
  - [x] Install `npm install -D vite-plugin-singlefile@2.3.3`
  - [x] Configure `vite.config.ts` with `vite-plugin-singlefile` plugin
  - [x] Verify `npm run build` produces single `dist/index.html`
- [x] Configure `@/` path alias
  - [x] Update `vite.config.ts` with resolve alias: `@` → `./src`
  - [x] Update `tsconfig.json` / `tsconfig.app.json` with paths: `{"@/*": ["./src/*"]}`
- [x] Create directory structure
  - [x] Create `src/components/`
  - [x] Create `src/hooks/`
  - [x] Create `src/services/`
  - [x] Create `src/types/`
  - [x] Create `src/utils/`
  - [x] Add placeholder `.gitkeep` files if needed
- [x] Enable TypeScript strict mode
  - [x] Set `"strict": true` in `tsconfig.json` / `tsconfig.app.json`
  - [x] Verify `npx tsc --noEmit` passes
- [x] Set up testing framework
  - [x] Install Vitest: `npm install -D vitest`
  - [x] Install React Testing Library: `npm install -D @testing-library/react @testing-library/jest-dom jsdom`
  - [x] Configure Vitest in `vite.config.ts` with jsdom environment
  - [x] Add test script to `package.json`: `"test": "vitest run"`
- [x] Clean up starter template boilerplate
  - [x] Remove default App.css content
  - [x] Remove default Vite/React logos and assets
  - [x] Update `index.html` title to "PixelForge — 8-Bit Avatar Generator"

## Dev Notes

### Architecture Requirements

- **Tech stack**: Vite 6 + React 18 + TypeScript (strict mode), targeting ES2020+
- **Build**: `vite-plugin-singlefile@2.3.3` inlines all JS/CSS into `dist/index.html`
- **Path alias**: `@/` resolves to `src/` — all imports use `@/` prefix, no relative imports beyond `../`
- **Styling**: Vanilla CSS with CSS modules (`.module.css` per component); CSS custom properties for theme tokens
- **Testing**: Vitest + React Testing Library; tests co-located with source files as `*.test.tsx`
- **Exports**: Named exports only — no `export default` anywhere
- **Error handling**: Typed union `Result<T, E>` pattern — `{ ok: true; data: T } | { ok: false; error: E }`
- **Components**: PascalCase `.tsx`, co-located with `.module.css` and `.test.tsx` in `src/components/[Name]/`

### File Structure

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
│   ├── hooks/
│   ├── services/
│   ├── types/
│   └── utils/
└── dist/
    └── index.html
```

### vite.config.ts Configuration

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteSingleFile } from 'vite-plugin-singlefile'
import path from 'path'

export default defineConfig({
  plugins: [react(), viteSingleFile()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
```

### Dependencies

- **Runtime**: `react`, `react-dom` (from Vite template)
- **Dev**: `typescript`, `@vitejs/plugin-react`, `vite`, `vite-plugin-singlefile@2.3.3`, `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`

### Project Structure Notes

- Directory structure must match the architecture spec — missing directories will cause incorrect file placement in later stories
- The `dist/` directory is gitignored (Vite default)
- Do NOT install any state management libraries — use React hooks + Context API only

## File List

- `package.json` — Project manifest with Vite 6, React 18, TypeScript, testing deps
- `vite.config.ts` — Vite config with React plugin, singlefile plugin, `@/` alias
- `vitest.config.ts` — Vitest config with jsdom environment, globals, `@/` alias
- `tsconfig.json` — Root TS config referencing app + node configs
- `tsconfig.app.json` — App TS config with strict mode, `@/*` paths
- `tsconfig.node.json` — Node TS config for vite.config.ts
- `index.html` — Entry HTML with Google Fonts link, updated title
- `src/main.tsx` — React entry point
- `src/App.tsx` — Root component (basic scaffold)
- `src/App.module.css` — Root CSS module (basic scaffold)
- `src/vite-env.d.ts` — Vite type declarations
- `src/test-setup.ts` — Test setup importing jest-dom matchers
- `public/favicon.svg` — Favicon SVG
- `.gitignore` — Git ignore rules

## Change Log

- 2026-05-18: Scaffolded project with Vite 6 + React 18 + TypeScript, single-file build config, `@/` path alias, directory structure, strict mode, Vitest + React Testing Library setup

## Dev Agent Record

**Implementation Notes:**
- Created project files manually within existing workspace directory
- Vite 6 + React 18 + TypeScript strict mode
- Single-file build via vite-plugin-singlefile
- `@/` path alias configured in vite + vitest configs and tsconfig
- Separate vitest.config.ts to avoid Vite/Vitest type conflicts
- Named exports pattern established in all components

## References

- [Architecture: Decision Document](architecture.md#L53-L58) — Tech stack and single-file decision
- [Architecture: Starter Template](architecture.md#L65-L102) — Scaffold details and initial config
- [Architecture: Project Structure](architecture.md#L206-L268) — Full directory tree
- [Architecture: Implementation Patterns](architecture.md#L148-L201) — Naming, exports, error handling
- [Architecture: Build Tooling](architecture.md#L86-L89) — vite-plugin-singlefile@2.3.3
- [Epics: Story 1.1](epics.md#L116-L145) — Acceptance criteria
- [PRD: AR-1, AR-2, AR-6, AR-7, AR-8, AR-9, AR-10](prd.md#L48-L59) — Additional requirements
