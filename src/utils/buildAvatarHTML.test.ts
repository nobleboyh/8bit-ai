import { describe, it, expect } from 'vitest'
import { buildAvatarHTML } from './buildAvatarHTML'

const TWO_BY_TWO = [
  ['#ff0000', '#00ff00'],
  ['#0000ff', '#ff00ff'],
]

const THREE_BY_THREE = [
  ['#000000', '#ffffff', '#000000'],
  ['#ffffff', '#ff0000', '#ffffff'],
  ['#000000', '#ffffff', '#000000'],
]

describe('buildAvatarHTML', () => {
  it('returns a string starting with <!DOCTYPE html>', () => {
    const html = buildAvatarHTML(TWO_BY_TWO, 'Test Avatar', 'Wizard', 'Hero')
    expect(html.startsWith('<!DOCTYPE html>')).toBe(true)
  })

  it('returns a string containing <html lang="en">', () => {
    const html = buildAvatarHTML(TWO_BY_TWO, 'Test Avatar', 'Wizard', 'Hero')
    expect(html).toContain('<html lang="en">')
  })

  it('includes <meta charset="UTF-8">', () => {
    const html = buildAvatarHTML(TWO_BY_TWO, 'Test Avatar', 'Wizard', 'Hero')
    expect(html).toContain('<meta charset="UTF-8">')
  })

  it('includes <meta name="viewport">', () => {
    const html = buildAvatarHTML(TWO_BY_TWO, 'Test Avatar', 'Wizard', 'Hero')
    expect(html).toContain('<meta name="viewport"')
  })

  it('includes title with prefix and username', () => {
    const html = buildAvatarHTML(TWO_BY_TWO, 'Test Avatar', 'Wizard', 'Hero')
    expect(html).toContain('<title>Wizard Hero — Pixelforce Avatar</title>')
  })

  it('contains no <script> tags', () => {
    const html = buildAvatarHTML(TWO_BY_TWO, 'Test Avatar', 'Wizard', 'Hero')
    expect(html).not.toContain('<script')
  })

  it('contains no <link> tags referencing external URLs', () => {
    const html = buildAvatarHTML(TWO_BY_TWO, 'Test Avatar', 'Wizard', 'Hero')
    expect(html).not.toMatch(/<link[^>]*href=["']https?:\/\//)
  })

  it('contains no <img> tags referencing external URLs', () => {
    const html = buildAvatarHTML(TWO_BY_TWO, 'Test Avatar', 'Wizard', 'Hero')
    expect(html).not.toMatch(/<img[^>]*src=["']https?:\/\//)
  })

  it('has a single <style> block inside <head>', () => {
    const html = buildAvatarHTML(TWO_BY_TWO, 'Test Avatar', 'Wizard', 'Hero')
    const styleMatch = html.match(/<style>[\s\S]*?<\/style>/)
    expect(styleMatch).not.toBeNull()
    const allStyles = html.match(/<style>/g)
    expect(allStyles).toHaveLength(1)
  })

  it('is deterministic — same inputs produce identical output', () => {
    const html1 = buildAvatarHTML(TWO_BY_TWO, 'Test Avatar', 'Wizard', 'Hero')
    const html2 = buildAvatarHTML(TWO_BY_TWO, 'Test Avatar', 'Wizard', 'Hero')
    expect(html1).toBe(html2)
  })

  it('does not contain API key patterns', () => {
    const html = buildAvatarHTML(TWO_BY_TWO, 'Test Avatar', 'Wizard', 'Hero')
    expect(html).not.toMatch(/sk-/)
    expect(html).not.toMatch(/r8_/)
    expect(html).not.toMatch(/sk-ant-/)
  })

  it('renders each grid cell with inline style="background:#RRGGBB"', () => {
    const html = buildAvatarHTML(TWO_BY_TWO, 'Test Avatar', 'Wizard', 'Hero')
    expect(html).toContain('style="background:#ff0000"')
    expect(html).toContain('style="background:#00ff00"')
    expect(html).toContain('style="background:#0000ff"')
    expect(html).toContain('style="background:#ff00ff"')
  })

  it('does not use class attribute for cell background colour', () => {
    const html = buildAvatarHTML(TWO_BY_TWO, 'Test Avatar', 'Wizard', 'Hero')
    const cellDivs = html.match(/<div[^>]*style="background:[^"]*"[^>]*>/g)
    expect(cellDivs).not.toBeNull()
    if (cellDivs) {
      for (const div of cellDivs) {
        expect(div).not.toContain('class=')
      }
    }
  })

  it('uses correct grid dimensions: N cells per row', () => {
    const html = buildAvatarHTML(THREE_BY_THREE, 'Test', 'Wizard', 'Hero')
    const gridContainer = html.match(/grid-template-columns:\s*repeat\(3,\s*1fr\)/)
    expect(gridContainer).not.toBeNull()
  })

  it('has total cells matching grid.length * grid[0].length', () => {
    const html = buildAvatarHTML(TWO_BY_TWO, 'Test', 'Wizard', 'Hero')
    const cellCount = (html.match(/style="background:/g) || []).length
    expect(cellCount).toBe(4)
  })

  it('displays label text beneath the grid', () => {
    const html = buildAvatarHTML(TWO_BY_TWO, 'My Cool Avatar', 'Wizard', 'Hero')
    expect(html).toContain('My Cool Avatar')
    const labelPos = html.indexOf('My Cool Avatar')
    const lastCellEnd = html.lastIndexOf('</div>', html.indexOf('class="label"'))
    expect(labelPos).toBeGreaterThan(lastCellEnd)
  })

  it('is under 50 KB for a 32x32 grid', () => {
    const size = 32
    const grid: string[][] = Array.from({ length: size }, () =>
      Array.from({ length: size }, () => '#ff0000'),
    )
    const html = buildAvatarHTML(grid, 'Large Avatar', 'Knight', 'BigTest')
    const bytes = new TextEncoder().encode(html).length
    expect(bytes).toBeLessThan(50 * 1024)
  })

  it('uses display: grid for layout', () => {
    const html = buildAvatarHTML(TWO_BY_TWO, 'Test', 'Wizard', 'Hero')
    expect(html).toContain('display: grid')
  })
})
