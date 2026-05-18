# Story 2.3: Avatar Rendering, Loading Indicator & PNG Export

Status: review

## Story

As a user,
I want to see my pixel avatar rendered on screen and download it as a PNG,
So that I can use it as a profile picture or game asset.

## Acceptance Criteria

1. **Given** a valid pixel map is available, **When** the result state is active, **Then** the avatar grid renders as coloured `<div>` cells in a CSS Grid layout, **And** each cell's background colour matches the hex value from the LLM response, **And** the grid is scaled to a visible size (e.g. 256×256 px), **And** the label from the response is displayed beneath the grid in Press Start 2P font, **And** the avatar is inside a container with black background, 4px border, and 8px 8px offset shadow, **And** metadata text shows pixel size and palette info.

2. **Given** the avatar is displayed, **When** I click "DOWNLOAD PNG", **Then** a PNG file is downloaded with filename `pixelforce-[type]-[username].png`, **And** the download is entirely client-side via canvas.toBlob, **And** no network request is made during export.

3. **Given** the avatar is displayed, **When** I click "RE-FORGE", **Then** the generation flow restarts from the prompt input, **And** controls are re-enabled for a new generation.

4. **Given** no avatar has been generated, **When** I view the avatar section, **Then** only the empty state is visible, **And** the download and re-forge buttons are not shown.

5. **Given** the loading state is active, **When** the pixel-loader renders, **Then** a 48×48px accent-coloured square blinks at 0.6s step-end interval, **And** "GENERATING..." text pulses at 1.5s step-end interval.

## Tasks / Subtasks

- [x] Create `AvatarGrid` component in `src/components/AvatarGrid/`
  - [x] Renders pixel grid as CSS Grid of coloured `<div>` cells
  - [x] Each cell is 1×1 logical unit, grid scaled to visible size (~256×256px)
  - [x] Cell background matches hex colour from `pixelMap.grid`
  - [x] Label from `pixelMap.label` displayed beneath grid in Press Start 2P
  - [x] Avatar container: black background, 4px border, 8px 8px offset `--shadow`
  - [x] Metadata: "16×16 · N colours in palette" text in `--muted`
  - [x] `image-rendering: pixelated` on container
- [x] Create `LoadingIndicator` component in `src/components/LoadingIndicator/`
  - [x] 48×48px accent-coloured square blinking at 0.6s step-end
  - [x] "GENERATING..." text pulsing at 1.5s step-end
  - [x] Centered in viewer container
- [x] Create `DownloadButton` component in `src/components/DownloadButton/`
  - [x] "DOWNLOAD PNG" button with `.btn-primary` styling
  - [x] Triggers client-side PNG export
  - [x] Disabled when no pixel map available
- [x] Create PNG export utility in `src/utils/pngExport.ts`
  - [x] `exportAsPng(pixelMap: PixelMapResponse, type: string, name: string): void`
  - [x] Draw grid onto OffscreenCanvas
  - [x] `canvas.toBlob()` → `URL.createObjectURL()` → programmatic `<a download>` click
  - [x] Filename: `pixelforce-[type]-[username].png`
  - [x] No network request during export
- [x] Update `ViewerShell` to render result state and action buttons
  - [x] UPDATE: Render `AvatarGrid` in result state
  - [x] UPDATE: Show "DOWNLOAD PNG" + "RE-FORGE" buttons in result state
  - [x] UPDATE: Show `LoadingIndicator` in loading state
  - [x] UPDATE: `onReForge` callback to reset generation state
- [x] Update `App.tsx` to wire re-forge and pass type/name for PNG export
  - [x] UPDATE: Pass `selectedType` and name to download function
  - [x] UPDATE: Wire `onReForge` to reset `usePixelGeneration` state
  - [x] UPDATE: Pass `onDownload` callback to `ViewerShell`
- [x] Write tests
  - [x] `AvatarGrid`: renders correct number of cells with matching colours
  - [x] `AvatarGrid`: displays label and metadata
  - [x] `AvatarGrid`: shows empty state when no pixel map
  - [x] `LoadingIndicator`: renders blinking square and pulsing text
  - [x] `DownloadButton`: triggers download with correct filename
  - [x] `DownloadButton`: disabled when no pixel map
  - [x] `pngExport`: generates blob and triggers download
  - [x] `ViewerShell`: result state shows avatar + buttons, loading shows indicator

## Dev Notes

### CSS Grid Rendering

```tsx
interface AvatarGridProps {
  pixelMap: PixelMapResponse
  type: string
}

export function AvatarGrid({ pixelMap, type }: AvatarGridProps) {
  const gridSize = pixelMap.grid.length // e.g., 16
  const cellCount = pixelMap.palette.length

  return (
    <div className={styles.container}>
      <div
        className={styles.grid}
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${gridSize}, 1fr)`,
          width: 256,
          height: 256,
        }}
      >
        {pixelMap.grid.flatMap((row, y) =>
          row.map((colour, x) => (
            <div
              key={`${y}-${x}`}
              style={{ backgroundColor: colour }}
            />
          ))
        )}
      </div>
      <p className={styles.label}>{pixelMap.label}</p>
      <p className={styles.metadata}>
        {gridSize}×{gridSize} · {cellCount} colours
      </p>
    </div>
  )
}
```

### Loading Indicator Animation

```css
.pixel {
  width: 48px;
  height: 48px;
  background-color: var(--accent);
  animation: blink 0.6s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.text {
  font-family: var(--font-display);
  font-size: 11px;
  color: var(--accent);
  animation: pulse 1.5s step-end infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
```

### PNG Export Utility

```typescript
export function exportAsPng(pixelMap: PixelMapResponse, type: string, name: string): void {
  const size = pixelMap.grid.length
  // Use a scale factor so the PNG looks crisp
  const scale = 16 // renders at `size * scale` pixels
  const canvas = new OffscreenCanvas(size * scale, size * scale)
  const ctx = canvas.getContext('2d')!

  pixelMap.grid.forEach((row, y) => {
    row.forEach((colour, x) => {
      ctx.fillStyle = colour
      ctx.fillRect(x * scale, y * scale, scale, scale)
    })
  })

  canvas.convertToBlob({ type: 'image/png' }).then((blob) => {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `pixelforce-${type.toLowerCase()}-${name.toLowerCase().replace(/\s+/g, '-')}.png`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  })
}
```

### ViewerShell Result State

```tsx
// In ViewerShell, when pixelMap is set and not loading:
<div className={styles['viewer-result']}>
  <AvatarGrid pixelMap={pixelMap} type={selectedType} />
  <div className={styles['action-row']}>
    <DownloadButton pixelMap={pixelMap} type={selectedType} name={prompt} />
    <button className={styles.btn} onClick={onReForge}>
      RE-FORGE
    </button>
  </div>
</div>
```

### Architecture Compliance

- CSS Grid for pixel rendering — no canvas for display (canvas only for export)
- `image-rendering: pixelated` for crisp pixel display
- PNG export uses `OffscreenCanvas.convertToBlob()` — entirely client-side, no network
- All components in `src/components/[Name]/` with co-located CSS module + tests
- Named exports only (no `export default`)
- Imports via `@/` path alias
- `Result<T, E>` pattern respected in service layer
- Loading animation uses pure CSS `@keyframes` with `step-end` timing for retro feel

### File Structure

```
src/
├── App.tsx                              # UPDATE: Wire re-forge, download, pass type/name
├── components/
│   ├── AvatarGrid/
│   │   ├── AvatarGrid.tsx              # NEW: CSS Grid pixel render component
│   │   ├── AvatarGrid.module.css       # NEW: Grid, label, metadata styles
│   │   └── AvatarGrid.test.tsx         # NEW: Grid render tests
│   ├── LoadingIndicator/
│   │   ├── LoadingIndicator.tsx        # NEW: Blinking pixel + pulsing text
│   │   ├── LoadingIndicator.module.css # NEW: Blink and pulse animations
│   │   └── LoadingIndicator.test.tsx   # NEW: Loading indicator tests
│   ├── DownloadButton/
│   │   ├── DownloadButton.tsx          # NEW: PNG download button
│   │   ├── DownloadButton.module.css   # NEW: Button styles
│   │   └── DownloadButton.test.tsx     # NEW: Download tests
│   └── ViewerShell/
│       ├── ViewerShell.tsx             # UPDATE: Result state with AvatarGrid + buttons
│       └── ViewerShell.module.css      # UPDATE: Result state styles
├── utils/
│   └── pngExport.ts                    # NEW: Canvas-based PNG export utility
```

### Testing Requirements

- Vitest + React Testing Library for component tests
- Vitest for utility tests
- Mock `OffscreenCanvas` and `canvas.convertToBlob` for PNG export tests
- Test `AvatarGrid`: renders `grid.length * grid.length` cells, each cell has correct `style.backgroundColor`
- Test `AvatarGrid`: label element present and matches `pixelMap.label`
- Test `LoadingIndicator`: pixel div has animation class, text contains "GENERATING..."
- Test `DownloadButton`: click triggers `exportAsPng` callback
- Test `DownloadButton`: disabled when `pixelMap` is null
- Test `pngExport`: calls `createObjectURL` and triggers download

## File List

- `src/components/AvatarGrid/AvatarGrid.tsx` — NEW: CSS Grid pixel render + label + metadata
- `src/components/AvatarGrid/AvatarGrid.module.css` — NEW: Grid container, label, metadata styles
- `src/components/AvatarGrid/AvatarGrid.test.tsx` — NEW: Grid render tests
- `src/components/LoadingIndicator/LoadingIndicator.tsx` — NEW: Blinking pixel square + pulsing text
- `src/components/LoadingIndicator/LoadingIndicator.module.css` — NEW: Blink/pulse keyframe animations
- `src/components/LoadingIndicator/LoadingIndicator.test.tsx` — NEW: Loading indicator tests
- `src/components/DownloadButton/DownloadButton.tsx` — NEW: PNG download button component
- `src/components/DownloadButton/DownloadButton.module.css` — NEW: Button styles
- `src/components/DownloadButton/DownloadButton.test.tsx` — NEW: Download button tests
- `src/utils/pngExport.ts` — NEW: OffscreenCanvas PNG export utility
- `src/components/ViewerShell/ViewerShell.tsx` — UPDATE: Result state with AvatarGrid + action buttons
- `src/components/ViewerShell/ViewerShell.module.css` — UPDATE: Result state styles
- `src/App.tsx` — UPDATE: Wire re-forge callback, pass type/name for export

## Change Log

- 2026-05-18: Created avatar CSS Grid rendering, loading indicator animation, PNG export utility, download/ re-forge buttons, and ViewerShell result state

## References

- [Epics: Story 2.3](epics.md#L365-L401) — Full acceptance criteria
- [Architecture: Requirements to Structure Mapping](architecture.md#L270-L279) — FR-7, FR-8, FR-9 mapping
- [Architecture: Project Structure](architecture.md#L234-L265) — AvatarGrid, LoadingIndicator, DownloadButton, pngExport locations
- [UX: Pixel Loader](ux-design-specification.md#L341-L343) — Blinking square animation spec
- [UX: Avatar Viewer States](ux-design-specification.md#L337-L339) — Result state design
- [UX: Button Hierarchy](ux-design-specification.md#L356-L359) — Primary vs secondary buttons
- [UX: Visual Design Foundation](ux-design-specification.md#L214-L234) — NES colour palette
- [PRD: FR-7](prd.md#L108-L114) — CSS grid render
- [PRD: FR-8](prd.md#L116-L121) — Label display
- [PRD: FR-9](prd.md#L128-L134) — Client-side PNG download
- [PRD: FR-6](prd.md#L96-L101) — Loading indicator
