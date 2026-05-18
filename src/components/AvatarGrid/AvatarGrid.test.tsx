import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AvatarGrid } from './AvatarGrid'

const mockPixelMap = {
  palette: ['#000000', '#ffffff', '#ff0000'],
  grid: [
    ['#000000', '#ffffff'],
    ['#ff0000', '#000000'],
  ],
  label: 'Test Avatar',
}

describe('AvatarGrid', () => {
  it('renders correct number of cells', () => {
    const { container } = render(<AvatarGrid pixelMap={mockPixelMap} type="Wizard" />)
    const cells = container.querySelector('[style*="display: grid"]')?.children
    expect(cells).toHaveLength(4)
  })

  it('renders cells with matching background colours', () => {
    const { container } = render(<AvatarGrid pixelMap={mockPixelMap} type="Wizard" />)
    const cells = container.querySelector('[style*="display: grid"]')?.children
    expect(cells?.[0]).toHaveStyle({ backgroundColor: '#000000' })
    expect(cells?.[1]).toHaveStyle({ backgroundColor: '#ffffff' })
    expect(cells?.[2]).toHaveStyle({ backgroundColor: '#ff0000' })
  })

  it('displays label from pixelMap', () => {
    render(<AvatarGrid pixelMap={mockPixelMap} type="Wizard" />)
    expect(screen.getByText('Test Avatar')).toBeTruthy()
  })

  it('displays metadata with grid size and colour count', () => {
    render(<AvatarGrid pixelMap={mockPixelMap} type="Wizard" />)
    expect(screen.getByText(/2×2/)).toBeTruthy()
    expect(screen.getByText(/3 colours/)).toBeTruthy()
  })
})
