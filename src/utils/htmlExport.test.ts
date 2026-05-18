import { describe, it, expect, vi, beforeEach } from 'vitest'
import { htmlExport } from './htmlExport'

const mockGrid = [
  ['#ff0000', '#00ff00'],
  ['#0000ff', '#ff00ff'],
]

vi.mock('@/utils/buildAvatarHTML', () => ({
  buildAvatarHTML: vi.fn(() => '<!DOCTYPE html><html lang="en"><body>mock</body></html>'),
}))

function mockBrowserApis() {
  const mockClick = vi.fn()
  const origURL = globalThis.URL
  vi.stubGlobal('URL', {
    ...origURL,
    createObjectURL: vi.fn(() => 'blob:test-html'),
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

describe('htmlExport', () => {
  beforeEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('creates a Blob with text/html MIME type', () => {
    mockBrowserApis()
    vi.spyOn(document.body, 'appendChild').mockImplementation((el: Node) => el)
    vi.spyOn(document.body, 'removeChild').mockImplementation((el: Node) => el)

    const BlobOrig = globalThis.Blob
    const blobSpy = vi.spyOn(globalThis, 'Blob' as any).mockImplementation(
      (parts: BlobPart[], options?: BlobPropertyBag) => new BlobOrig(parts, options),
    )

    htmlExport(mockGrid, 'Test Avatar', 'Wizard', 'Hero')

    expect(blobSpy).toHaveBeenCalledWith(
      [expect.stringContaining('<!DOCTYPE html>')],
      { type: 'text/html' },
    )
  })

  it('triggers download via URL.createObjectURL', () => {
    mockBrowserApis()
    vi.spyOn(document.body, 'appendChild').mockImplementation((el: Node) => el)
    vi.spyOn(document.body, 'removeChild').mockImplementation((el: Node) => el)

    htmlExport(mockGrid, 'Test Avatar', 'Wizard', 'Hero')

    expect(globalThis.URL.createObjectURL).toHaveBeenCalled()
  })

  it('uses correct filename format pixelforce-[type]-[username].html', () => {
    mockBrowserApis()
    const appendSpy = vi.spyOn(document.body, 'appendChild').mockImplementation((el: Node) => el)
    vi.spyOn(document.body, 'removeChild').mockImplementation((el: Node) => el)

    htmlExport(mockGrid, 'Test Avatar', 'Wizard', 'Hero')

    const anchorEl = appendSpy.mock.calls.find(([el]) => (el as HTMLAnchorElement).tagName === 'A')?.[0] as HTMLAnchorElement
    expect(anchorEl).toBeDefined()
    expect(anchorEl.download).toBe('pixelforce-wizard-hero.html')
  })

  it('calls URL.revokeObjectURL after download', () => {
    mockBrowserApis()
    vi.spyOn(document.body, 'appendChild').mockImplementation((el: Node) => el)
    vi.spyOn(document.body, 'removeChild').mockImplementation((el: Node) => el)

    htmlExport(mockGrid, 'Test Avatar', 'Wizard', 'Hero')

    expect(globalThis.URL.revokeObjectURL).toHaveBeenCalledWith('blob:test-html')
  })

  it('sanitizes special characters in filename, removing spaces and special chars', () => {
    mockBrowserApis()
    const appendSpy = vi.spyOn(document.body, 'appendChild').mockImplementation((el: Node) => el)
    vi.spyOn(document.body, 'removeChild').mockImplementation((el: Node) => el)

    htmlExport(mockGrid, 'Test Avatar', 'Wizard!!', 'Test Hero!!!')

    const anchorEl = appendSpy.mock.calls.find(([el]) => (el as HTMLAnchorElement).tagName === 'A')?.[0] as HTMLAnchorElement
    expect(anchorEl.download).toBe('pixelforce-wizard-testhero.html')
  })

  it('does not throw for valid input', () => {
    mockBrowserApis()
    vi.spyOn(document.body, 'appendChild').mockImplementation((el: Node) => el)
    vi.spyOn(document.body, 'removeChild').mockImplementation((el: Node) => el)

    expect(() => {
      htmlExport(mockGrid, 'Test Avatar', 'Knight', 'Sir Test')
    }).not.toThrow()
  })
})
