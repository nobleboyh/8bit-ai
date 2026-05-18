# Story 1.1: Project Scaffold & Build Tooling

Status: ready-for-dev

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

- [ ] Scaffold project with Vite 6 + React 18 + TypeScript
  - [ ] Run `npm create vite@latest pixelforge -- --template react-ts`
  - [ ] Run `npm install` to resolve dependencies
  - [ ] Verify `npm run dev` starts HMR server
- [ ] Configure single-file build
  - [ ] Install `npm install -D vite-plugin-singlefile@2.3.3`
  - [ ] Configure `vite.config.ts` with `vite-plugin-singlefile` plugin
  - [ ] Verify `npm run build` produces single `dist/index.html`
- [ ] Configure `@/` path alias
  - [ ] Update `vite.config.ts` with resolve alias: `@` → `./src`
  - [ ] Update `tsconfig.json` / `tsconfig.app.json` with paths: `{"@/*": ["./src/*"]}`
- [ ] Create directory structure
  - [ ] Create `src/components/`
  - [ ] Create `src/hooks/`
  - [ ] Create `src/services/`
  - [ ] Create `src/types/`
  - [ ] Create `src/utils/`
  - [ ] Add placeholder `.gitkeep` files if needed
- [ ] Enable TypeScript strict mode
  - [ ] Set `"strict": true` in `tsconfig.json` / `tsconfig.app.json`
  - [ ] Verify `npx tsc --noEmit` passes
- [ ] Set up testing framework
  - [ ] Install Vitest: `npm install -D vitest`
  - [ ] Install React Testing Library: `npm install -D @testing-library/react @testing-library/jest-dom jsdom`
  - [ ] Configure Vitest in `vite.config.ts` with jsdom environment
  - [ ] Add test script to `package.json`: `"test": "vitest run"`
- [ ] Clean up starter template boilerplate
  - [ ] Remove default App.css content
  - [ ] Remove default Vite/React logos and assets
  - [ ] Update `index.html` title to "PixelForge — 8-Bit Avatar Generator"

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

## References

- [Architecture: Decision Document](architecture.md#L53-L58) — Tech stack and single-file decision
- [Architecture: Starter Template](architecture.md#L65-L102) — Scaffold details and initial config
- [Architecture: Project Structure](architecture.md#L206-L268) — Full directory tree
- [Architecture: Implementation Patterns](architecture.md#L148-L201) — Naming, exports, error handling
- [Architecture: Build Tooling](architecture.md#L86-L89) — vite-plugin-singlefile@2.3.3
- [Epics: Story 1.1](epics.md#L116-L145) — Acceptance criteria
- [PRD: AR-1, AR-2, AR-6, AR-7, AR-8, AR-9, AR-10](prd.md#L48-L59) — Additional requirements
