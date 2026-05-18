import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ErrorDisplay } from './ErrorDisplay'

describe('ErrorDisplay', () => {
  it('renders error message', () => {
    render(<ErrorDisplay message="Something went wrong" />)
    expect(screen.getByText('Something went wrong')).toBeTruthy()
  })

  it('has role="alert"', () => {
    render(<ErrorDisplay message="Error" />)
    expect(screen.getByRole('alert')).toBeTruthy()
  })

  it('does not render dismiss button when onDismiss is not provided', () => {
    render(<ErrorDisplay message="Error" />)
    expect(screen.queryByLabelText('Dismiss error')).toBeNull()
  })

  it('renders dismiss button and calls onDismiss when clicked', () => {
    const onDismiss = vi.fn()
    render(<ErrorDisplay message="Error" onDismiss={onDismiss} />)
    const dismissBtn = screen.getByLabelText('Dismiss error')
    expect(dismissBtn).toBeTruthy()
    fireEvent.click(dismissBtn)
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })
})
