import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeToggle } from './ThemeToggle'

describe('ThemeToggle', () => {
  it('renders DARK label in light mode', () => {
    render(<ThemeToggle theme="light" onToggle={vi.fn()} />)
    expect(screen.getByRole('button')).toHaveTextContent('DARK')
  })

  it('renders LIGHT label in dark mode', () => {
    render(<ThemeToggle theme="dark" onToggle={vi.fn()} />)
    expect(screen.getByRole('button')).toHaveTextContent('LIGHT')
  })

  it('calls onToggle on click', () => {
    const onToggle = vi.fn()
    render(<ThemeToggle theme="light" onToggle={onToggle} />)
    fireEvent.click(screen.getByRole('button'))
    expect(onToggle).toHaveBeenCalledTimes(1)
  })

  it('has accessible label', () => {
    render(<ThemeToggle theme="light" onToggle={vi.fn()} />)
    expect(screen.getByRole('button')).toHaveAttribute('aria-label')
  })
})
