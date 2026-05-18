import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DownloadHtmlButton } from './DownloadHtmlButton'

const mockHtmlExport = vi.fn()
vi.mock('@/utils/htmlExport', () => ({
  htmlExport: (...args: unknown[]) => mockHtmlExport(...args),
}))

const mockPixelMap = {
  palette: ['#000'],
  grid: [['#000']],
  label: 'Test',
}

describe('DownloadHtmlButton', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders DOWNLOAD HTML button', () => {
    render(<DownloadHtmlButton pixelMap={mockPixelMap} prefix="Wizard" username="hero" />)
    expect(screen.getByText('DOWNLOAD HTML')).toBeTruthy()
  })

  it('renders nothing when pixelMap is null', () => {
    const { container } = render(<DownloadHtmlButton pixelMap={null} prefix="Wizard" username="hero" />)
    expect(container.innerHTML).toBe('')
  })

  it('has aria-label Download HTML', () => {
    render(<DownloadHtmlButton pixelMap={mockPixelMap} prefix="Wizard" username="hero" />)
    expect(screen.getByLabelText('Download HTML')).toBeTruthy()
  })

  it('calls htmlExport on click', () => {
    render(<DownloadHtmlButton pixelMap={mockPixelMap} prefix="Knight" username="Sir Test" />)
    fireEvent.click(screen.getByLabelText('Download HTML'))
    expect(mockHtmlExport).toHaveBeenCalledWith(mockPixelMap.grid, mockPixelMap.label, 'Knight', 'Sir Test')
  })

  it('does not render when pixelMap is null (no button to click)', () => {
    const { container } = render(<DownloadHtmlButton pixelMap={null} prefix="Wizard" username="hero" />)
    expect(container.innerHTML).toBe('')
  })
})
