import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ApiKeyInput } from './ApiKeyInput'

describe('ApiKeyInput', () => {
  it('renders as type=password by default', () => {
    render(<ApiKeyInput apiKey="" onChange={vi.fn()} />)
    const input = screen.getByLabelText('API Key')
    expect(input).toHaveAttribute('type', 'password')
  })

  it('shows SHOW button by default', () => {
    render(<ApiKeyInput apiKey="" onChange={vi.fn()} />)
    expect(screen.getByRole('button')).toHaveTextContent('SHOW')
  })

  it('toggles input type on button click', () => {
    render(<ApiKeyInput apiKey="" onChange={vi.fn()} />)
    const input = screen.getByLabelText('API Key')
    const button = screen.getByRole('button')

    fireEvent.click(button)
    expect(input).toHaveAttribute('type', 'text')
    expect(button).toHaveTextContent('HIDE')

    fireEvent.click(button)
    expect(input).toHaveAttribute('type', 'password')
    expect(button).toHaveTextContent('SHOW')
  })

  it('calls onChange when typing', () => {
    const onChange = vi.fn()
    render(<ApiKeyInput apiKey="" onChange={onChange} />)
    const input = screen.getByLabelText('API Key')
    fireEvent.change(input, { target: { value: 'sk-test' } })
    expect(onChange).toHaveBeenCalledWith('sk-test')
  })
})
