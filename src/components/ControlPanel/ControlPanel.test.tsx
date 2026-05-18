import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ControlPanel } from './ControlPanel'

describe('ControlPanel', () => {
  const defaultProps = {
    prompt: '',
    onPromptChange: vi.fn(),
    onGenerate: vi.fn(),
    isGenerating: false,
    hasApiKey: true,
  }

  it('renders textarea, FORGE button, and 6 chips', () => {
    render(<ControlPanel {...defaultProps} />)
    expect(screen.getByLabelText('Character prompt')).toBeTruthy()
    expect(screen.getByLabelText('Generate avatar')).toBeTruthy()
    const chips = screen.getAllByRole('button').filter((b) => b.getAttribute('aria-label')?.endsWith(' preset'))
    expect(chips).toHaveLength(6)
  })

  it('FORGE button disabled when textarea empty', () => {
    render(<ControlPanel {...defaultProps} prompt="" />)
    expect(screen.getByLabelText('Generate avatar')).toBeDisabled()
  })

  it('FORGE button enabled when textarea has text', () => {
    render(<ControlPanel {...defaultProps} prompt="test" />)
    expect(screen.getByLabelText('Generate avatar')).not.toBeDisabled()
  })

  it('FORGE button disabled when no API key', () => {
    render(<ControlPanel {...defaultProps} prompt="test" hasApiKey={false} />)
    expect(screen.getByLabelText('Generate avatar')).toBeDisabled()
  })

  it('FORGE button disabled when generating', () => {
    render(<ControlPanel {...defaultProps} prompt="test" isGenerating={true} />)
    expect(screen.getByLabelText('Generate avatar')).toBeDisabled()
  })

  it('clicking chip fills textarea', () => {
    const onPromptChange = vi.fn()
    render(<ControlPanel {...defaultProps} onPromptChange={onPromptChange} />)
    const wizardChip = screen.getByLabelText('Wizard preset')
    fireEvent.click(wizardChip)
    expect(onPromptChange).toHaveBeenCalled()
    expect(onPromptChange.mock.calls[0][0]).toContain('wizard')
  })

  it('calls onGenerate on FORGE click', () => {
    const onGenerate = vi.fn()
    render(<ControlPanel {...defaultProps} prompt="test" onGenerate={onGenerate} />)
    fireEvent.click(screen.getByLabelText('Generate avatar'))
    expect(onGenerate).toHaveBeenCalledTimes(1)
  })

  it('triggers generate on Cmd+Enter', () => {
    const onGenerate = vi.fn()
    render(<ControlPanel {...defaultProps} prompt="test" onGenerate={onGenerate} />)
    fireEvent.keyDown(screen.getByLabelText('Character prompt'), {
      key: 'Enter',
      metaKey: true,
    })
    expect(onGenerate).toHaveBeenCalledTimes(1)
  })

  it('triggers generate on Ctrl+Enter', () => {
    const onGenerate = vi.fn()
    render(<ControlPanel {...defaultProps} prompt="test" onGenerate={onGenerate} />)
    fireEvent.keyDown(screen.getByLabelText('Character prompt'), {
      key: 'Enter',
      ctrlKey: true,
    })
    expect(onGenerate).toHaveBeenCalledTimes(1)
  })
})
