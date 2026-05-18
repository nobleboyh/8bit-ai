import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DownloadButton } from './DownloadButton'

const mockExportAsPng = vi.fn()
vi.mock('@/utils/pngExport', () => ({
  exportAsPng: (...args: unknown[]) => mockExportAsPng(...args),
}))

const mockPixelMap = {
  palette: ['#000'],
  grid: [['#000']],
  label: 'Test',
}

describe('DownloadButton', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders DOWNLOAD PNG button', () => {
    render(<DownloadButton pixelMap={mockPixelMap} type="Wizard" name="hero" />)
    expect(screen.getByText('DOWNLOAD PNG')).toBeTruthy()
  })

  it('is disabled when pixelMap is null', () => {
    render(<DownloadButton pixelMap={null} type="Wizard" name="hero" />)
    expect(screen.getByLabelText('Download PNG')).toBeDisabled()
  })

  it('is enabled when pixelMap is provided', () => {
    render(<DownloadButton pixelMap={mockPixelMap} type="Wizard" name="hero" />)
    expect(screen.getByLabelText('Download PNG')).not.toBeDisabled()
  })

  it('calls exportAsPng on click', () => {
    render(<DownloadButton pixelMap={mockPixelMap} type="Knight" name="Sir Test" />)
    fireEvent.click(screen.getByLabelText('Download PNG'))
    expect(mockExportAsPng).toHaveBeenCalledWith(mockPixelMap, 'Knight', 'Sir Test')
  })

  it('does not call exportAsPng when pixelMap is null', () => {
    render(<DownloadButton pixelMap={null} type="Wizard" name="hero" />)
    fireEvent.click(screen.getByLabelText('Download PNG'))
    expect(mockExportAsPng).not.toHaveBeenCalled()
  })
})
