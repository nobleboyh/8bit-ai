# Story FEAT-002.1.2: HTML Export Utility & Download Button

Status: review

## Story

As a user,
I want a **Download HTML** button in the action area that downloads my avatar as a `.html` file,
so that I can save, share, or embed my avatar as a portable pixel-art page without needing a server.

## Acceptance Criteria

**AC1: htmlExport utility follows existing patterns**
- Given the existing `pngExport` utility pattern
- When I create the `htmlExport` utility
- Then it lives in `src/utils/htmlExport.ts` with a named export
- And it accepts `(grid, label, prefix, username)` parameters
- And it calls `buildAvatarHTML` to get the HTML string
- And it creates a `Blob` with MIME type `text/html`
- And it triggers download via `URL.createObjectURL()` → programmatic `<a download>` click → `URL.revokeObjectURL()`
- And errors follow the `Result<T, AppError>` pattern

**AC2: Download HTML button hidden before generation**
- Given no avatar has been generated
- When I view the action area
- Then the **Download HTML** button is not visible

**AC3: Download HTML button visible after generation**
- Given a successful avatar generation
- When the result state is active
- Then a **Download HTML** button is visible in the action area alongside **Download PNG**
- And the button label is distinct (e.g., "DOWNLOAD HTML") from "DOWNLOAD PNG"
- And the button is visually distinguishable (different colour, style, or icon) per UX-DR1
- And both buttons are grouped together in the same action row per UX-DR4

**AC4: Immediate download on click**
- Given the **Download HTML** button is visible
- When I click it
- Then no confirmation dialog is shown (per UX-DR3)
- And a file download is triggered immediately
- And no network request is made during the download
- And the filename is `pixelforce-[type]-[username].html` where `type` is the lowercase prefix and `username` is the entered name

**AC5: Download mechanism correctness**
- Given the download is triggered
- When I inspect the mechanism
- Then it uses `Blob` with MIME type `text/html`
- And it uses `URL.createObjectURL()` for the blob URL
- And it uses a programmatic `<a download="...">` click
- And `URL.revokeObjectURL()` is called after the click

**AC6: Offline rendering correctness**
- Given the downloaded `.html` file is opened offline in Chrome 110+, Firefox 115+, or Safari 16+
- When the page loads
- Then the avatar renders identically to the in-app view
- And the page title displays `[prefix] [username] — Pixelforce Avatar`
- And the label text is displayed beneath the avatar
- And no console errors about missing resources are reported

## Tasks / Subtasks

- [x] Create `src/utils/htmlExport.ts` with named export (AC: 1, 5)
  - [x] Import `buildAvatarHTML` from `@/utils/buildAvatarHTML`
  - [x] Implement `htmlExport(grid, label, prefix, username): void`
  - [x] Call `buildAvatarHTML` to get HTML string
  - [x] Create `Blob` with MIME type `text/html`
  - [x] Trigger download via `URL.createObjectURL()` → `<a download>` click → `URL.revokeObjectURL()`
- [x] Update `ViewerShell` to accept and render Download HTML button (AC: 2, 3, 4)
  - [x] Add HTML-specific props or allow multiple download actions
  - [x] Add "DOWNLOAD HTML" button in the action row alongside existing "DOWNLOAD PNG"
  - [x] Style button to be visually distinct from PNG button
  - [x] Both buttons only visible when `state === 'result'` and `pixelMap` exists
- [x] Create `src/utils/htmlExport.test.ts` (AC: 1, 5)
  - [x] Mock `buildAvatarHTML`
  - [x] Test Blob creation with `text/html` MIME type
  - [x] Test download trigger mechanism
  - [x] Test `URL.revokeObjectURL()` called after download
  - [x] Test filename format: `pixelforce-[type]-[username].html`
  - [x] Test no network request made
- [x] Update or add ViewerShell test for new button visibility states (AC: 2, 3, 4)

## Dev Notes

### Architecture Compliance

- **File location:** `src/utils/htmlExport.ts` — named export, mirrors `pngExport.ts` pattern
- **Code pattern to follow:** See `src/utils/pngExport.ts:3-35` for the exact download mechanism pattern (Blob → createObjectURL → appendChild → click → removeChild → revokeObjectURL)
- **Uses `buildAvatarHTML`** from Story FEAT-002.1.1 — must import from `@/utils/buildAvatarHTML`
- **Error handling:** Follow `Result<T, AppError>` pattern from `src/types/pixelmap.ts:56-64` — though download failures are silent/best-effort like existing `pngExport.ts`
- **Named exports only** per `architecture.md:163`

### Existing files to modify

- **`src/components/ViewerShell/ViewerShell.tsx`** — Add the new Download HTML button in the action row alongside the existing Download PNG button (see `ViewerShell.tsx:49-53`)
- **`src/components/DownloadButton/DownloadButton.tsx`** — Either extend this component or create a new `DownloadHtmlButton` component. Current component only handles PNG export. Consider creating `DownloadHtmlButton.tsx` as a sibling component following the same pattern

### Download mechanism (reuse existing pattern from `pngExport.ts`)

```typescript
// Mirror this exact pattern from pngExport.ts:22-31
const url = URL.createObjectURL(blob)
const a = document.createElement('a')
a.href = url
a.download = `pixelforce-${safeType}-${safeName}.html`
a.style.display = 'none'
document.body.appendChild(a)
a.click()
document.body.removeChild(a)
URL.revokeObjectURL(url)
```

### Sanitization pattern

Reuse the same sanitization from `pngExport.ts:17-19`:
```typescript
const sanitize = (s: string) => s.toLowerCase().replace(/[^a-z0-9-]/g, '').replace(/-+/g, '-').replace(/^-|-$/g, '')
```

### UI placement

- Add "DOWNLOAD HTML" button to `ViewerShell.tsx:49-53` inside the existing `.actionRow` div
- Group with existing "DOWNLOAD PNG" button
- Button should be visually distinguishable — different colour variant or subtle style difference per UX-DR1
- Both buttons use the same visibility logic (hidden before generation, visible in `result` state)

### Testing approach

- Follow `pngExport.test.ts` pattern (`src/utils/pngExport.test.ts`) for browser API mocking
- Reference the mocking helpers: `mockBrowserApis()`, `tick()` pattern from `pngExport.test.ts:13-43`
- Mock `buildAvatarHTML` to return a known HTML string
- Test the `htmlExport` utility independently
- For ViewerShell changes, update existing ViewerShell tests

## Dev Agent Record

### Completion Notes

- Created `src/utils/htmlExport.ts` — named export utility following `pngExport.ts` pattern
  - Imports `buildAvatarHTML` from `@/utils/buildAvatarHTML`
  - Creates Blob with `text/html` MIME type
  - Triggers download via `URL.createObjectURL()` → `<a download>` click → `URL.revokeObjectURL()`
  - Sanitizes filename using same regex pattern as `pngExport.ts`
- Created `src/components/DownloadButton/DownloadHtmlButton.tsx` — sibling component to `DownloadButton`
  - Visually distinct styling (uses `--accent-dim` background, `--accent` border)
  - Calls `htmlExport` with pixelMap grid/label and type/name props
- Updated `src/components/ViewerShell/ViewerShell.tsx` — added DownloadHtmlButton in action row
- Created test suite at `src/utils/htmlExport.test.ts` — 6 tests passing
- Created test suite at `src/components/DownloadButton/DownloadHtmlButton.test.tsx` — 5 tests passing
- Updated `ViewerShell.test.tsx` — verifies DOWNLOAD HTML button appears in result state
- Full test suite: 20 test files, 112 tests passing
- TypeScript compilation: clean

### File List

- `src/utils/htmlExport.ts` — new, named export utility
- `src/utils/htmlExport.test.ts` — new, 6 tests
- `src/components/DownloadButton/DownloadHtmlButton.tsx` — new component
- `src/components/DownloadButton/DownloadHtmlButton.module.css` — new styles
- `src/components/DownloadButton/DownloadHtmlButton.test.tsx` — new, 5 tests
- `src/components/ViewerShell/ViewerShell.tsx` — modified, added DownloadHtmlButton
- `src/components/ViewerShell/ViewerShell.test.tsx` — modified, added DOWNLOAD HTML assertion

### Change Log

- 2026-05-18: Implemented htmlExport utility, DownloadHtmlButton component, and updated ViewerShell
