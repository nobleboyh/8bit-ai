import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LoadingIndicator } from './LoadingIndicator'

describe('LoadingIndicator', () => {
  it('renders GENERATING... text', () => {
    render(<LoadingIndicator />)
    expect(screen.getByText('GENERATING...')).toBeTruthy()
  })

  it('has role="status" with appropriate label', () => {
    render(<LoadingIndicator />)
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Generating avatar')
  })

  it('renders pixel element', () => {
    const { container } = render(<LoadingIndicator />)
    const pixelDiv = container.querySelector('div > div')
    expect(pixelDiv).toBeTruthy()
  })
})
