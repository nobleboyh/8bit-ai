import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ProviderSelect } from './ProviderSelect'

describe('ProviderSelect', () => {
  it('renders trigger with current value label', () => {
    render(<ProviderSelect value="anthropic" onChange={vi.fn()} />)
    expect(screen.getByText('Anthropic')).toBeTruthy()
  })

  it('opens dropdown on trigger click', () => {
    render(<ProviderSelect value="anthropic" onChange={vi.fn()} />)
    const trigger = screen.getByRole('button')
    fireEvent.click(trigger)
    expect(screen.getByRole('listbox')).toBeTruthy()
  })

  it('shows all 4 options when open', () => {
    render(<ProviderSelect value="anthropic" onChange={vi.fn()} />)
    fireEvent.click(screen.getByRole('button'))
    const options = screen.getAllByRole('option')
    expect(options).toHaveLength(4)
    expect(options[0]).toHaveTextContent('Anthropic')
    expect(options[1]).toHaveTextContent('OpenAI')
    expect(options[2]).toHaveTextContent('OpenAI-Compatible')
    expect(options[3]).toHaveTextContent('DeepSeek')
  })

  it('selects option and closes dropdown on click', () => {
    const onChange = vi.fn()
    render(<ProviderSelect value="anthropic" onChange={onChange} />)
    fireEvent.click(screen.getByRole('button'))
    fireEvent.click(screen.getByText('DeepSeek'))
    expect(onChange).toHaveBeenCalledWith('deepseek')
  })

  it('closes dropdown when selecting an option', () => {
    const onChange = vi.fn()
    render(<ProviderSelect value="anthropic" onChange={onChange} />)
    fireEvent.click(screen.getByRole('button'))
    fireEvent.click(screen.getByText('OpenAI'))
    expect(screen.queryByRole('listbox')).toBeNull()
  })
})
