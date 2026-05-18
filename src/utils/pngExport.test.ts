import { describe, it, expect, vi, beforeEach } from 'vitest'
import { exportAsPng } from './pngExport'

const mockPixelMap = {
  palette: ['#000000', '#ffffff'],
  grid: [
    ['#000000', '#ffffff'],
    ['#ffffff', '#000000'],
  ],
  label: 'Test',
}

function mockBrowserApis() {
  const mockClick = vi.fn()
  vi.stubGlobal('OffscreenCanvas', vi.fn((w: number, h: number) => ({
    width: w,
    height: h,
    getContext: vi.fn(() => ({ fillStyle: '', fillRect: vi.fn() })),
    convertToBlob: vi.fn(() => Promise.resolve(new Blob())),
  })))

  const origURL = globalThis.URL
  vi.stubGlobal('URL', {
    ...origURL,
    createObjectURL: vi.fn(() => 'blob:test'),
    revokeObjectURL: vi.fn(),
  })

  const origCreateElement = document.createElement.bind(document)
  vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
    const el = origCreateElement(tag)
    if (tag === 'a') {
      el.click = mockClick
    }
    return el
  })

  return { mockClick }
}

function tick(): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, 0))
}

describe('exportAsPng', () => {
  beforeEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('creates an OffscreenCanvas and calls convertToBlob', async () => {
    mockBrowserApis()

    vi.spyOn(document.body, 'appendChild').mockImplementation((el: Node) => el)
    vi.spyOn(document.body, 'removeChild').mockImplementation((el: Node) => el)

    exportAsPng(mockPixelMap, 'Wizard', 'Test Hero')
    await tick()

    const MockOC = (globalThis as any).OffscreenCanvas
    expect(MockOC).toHaveBeenCalledWith(32, 32)
    expect(MockOC.mock.results[0].value.convertToBlob).toHaveBeenCalledWith({ type: 'image/png' })
  })

  it('does not throw for valid input', () => {
    mockBrowserApis()

    vi.spyOn(document.body, 'appendChild').mockImplementation((el: Node) => el)
    vi.spyOn(document.body, 'removeChild').mockImplementation((el: Node) => el)

    expect(() => {
      exportAsPng(mockPixelMap, 'Knight', 'Sir Test')
    }).not.toThrow()
  })
})
