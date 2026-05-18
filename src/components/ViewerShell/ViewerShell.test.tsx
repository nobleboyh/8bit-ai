import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ViewerShell } from './ViewerShell'

describe('ViewerShell', () => {
  it('shows empty state with icon and instructional text', () => {
    render(<ViewerShell state="empty" />)
    expect(screen.getByText('ENTER A PROMPT & FORGE YOUR PIXEL')).toBeTruthy()
  })

  it('renders nothing for non-empty states', () => {
    const { container } = render(<ViewerShell state="loading" />)
    expect(container.innerHTML).toBe('')
  })
})
