import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ViewerShell } from './ViewerShell'

const mockPixelMap = {
  palette: ['#000', '#fff'],
  grid: [['#000', '#fff']],
  label: 'Test Avatar',
}

describe('ViewerShell', () => {
  it('shows empty state with icon and instructional text', () => {
    render(<ViewerShell state="empty" />)
    expect(screen.getByText('ENTER A PROMPT & FORGE YOUR PIXEL')).toBeTruthy()
  })

  it('shows loading state with GENERATING text', () => {
    render(<ViewerShell state="loading" isGenerating={true} />)
    expect(screen.getByText('GENERATING...')).toBeTruthy()
  })

  it('shows loading state when isGenerating is true regardless of state', () => {
    render(<ViewerShell state="result" isGenerating={true} />)
    expect(screen.getByText('GENERATING...')).toBeTruthy()
  })

  it('shows error state with error message', () => {
    render(<ViewerShell state="error" error="Something went wrong" />)
    expect(screen.getByText('Something went wrong')).toBeTruthy()
  })

  it('shows result state with AvatarGrid label and action buttons', () => {
    render(
      <ViewerShell
        state="result"
        pixelMap={mockPixelMap}
        selectedType="Knight"
        prompt="Sir Test"
        onReForge={vi.fn()}
      />,
    )
    expect(screen.getByText('Test Avatar')).toBeTruthy()
    expect(screen.getByText('DOWNLOAD PNG')).toBeTruthy()
    expect(screen.getByText('DOWNLOAD HTML')).toBeTruthy()
    expect(screen.getByText('RE-FORGE')).toBeTruthy()
  })

  it('result state renders metadata', () => {
    render(
      <ViewerShell
        state="result"
        pixelMap={mockPixelMap}
        selectedType="Wizard"
        prompt="Hero"
        onReForge={vi.fn()}
      />,
    )
    expect(screen.getByText((content) => content.includes('colours'))).toBeTruthy()
  })
})
