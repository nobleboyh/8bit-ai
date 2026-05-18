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
    render(<DownloadHtmlButton pixelMap={mockPixelMap} type="Wizard" name="hero" />)
    expect(screen.getByText('DOWNLOAD HTML')).toBeTruthy()
  })

  it('is disabled when pixelMap is null', () => {
    render(<DownloadHtmlButton pixelMap={null} type="Wizard" name="hero" />)
    expect(screen.getByLabelText('Download HTML')).toBeDisabled()
  })

  it('is enabled when pixelMap is provided', () => {
    render(<DownloadHtmlButton pixelMap={mockPixelMap} type="Wizard" name="hero" />)
    expect(screen.getByLabelText('Download HTML')).not.toBeDisabled()
  })

  it('calls htmlExport on click', () => {
    render(<DownloadHtmlButton pixelMap={mockPixelMap} type="Knight" name="Sir Test" />)
    fireEvent.click(screen.getByLabelText('Download HTML'))
    expect(mockHtmlExport).toHaveBeenCalledWith(mockPixelMap.grid, mockPixelMap.label, 'Knight', 'Sir Test')
  })

  it('does not call htmlExport when pixelMap is null', () => {
    render(<DownloadHtmlButton pixelMap={null} type="Wizard" name="hero" />)
    fireEvent.click(screen.getByLabelText('Download HTML'))
    expect(mockHtmlExport).not.toHaveBeenCalled()
  })
})
