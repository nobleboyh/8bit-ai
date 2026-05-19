import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { usePixelGeneration } from './usePixelGeneration'

const mockGenerateFn = vi.fn()
vi.mock('@/services/llmClient', () => ({
  generate: (...args: unknown[]) => mockGenerateFn(...args),
}))

describe('usePixelGeneration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('initial state has no pixelMap, not generating, no error, no default type', () => {
    const { result } = renderHook(() => usePixelGeneration())
    expect(result.current.pixelMap).toBeNull()
    expect(result.current.isGenerating).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.selectedType).toBe('')
  })

  it('setSelectedType updates selected type', () => {
    const { result } = renderHook(() => usePixelGeneration())
    act(() => result.current.setSelectedType('Knight'))
    expect(result.current.selectedType).toBe('Knight')
  })

  it('generate sets pixelMap on success', async () => {
    const mockData = {
      palette: ['#000'],
      grid: [['#000']],
      label: 'Test',
    }
    mockGenerateFn.mockResolvedValueOnce({ ok: true, data: mockData })

    const { result } = renderHook(() => usePixelGeneration())
    await act(async () => {
      await result.current.generate('test prompt', {
        type: 'openai',
        apiUrl: 'https://api.openai.com',
        model: 'gpt-4o',
        apiKey: 'sk-test',
      })
    })

    expect(result.current.pixelMap).toEqual(mockData)
    expect(result.current.isGenerating).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('generate sets error on API failure', async () => {
    mockGenerateFn.mockResolvedValueOnce({
      ok: false,
      error: { message: 'API 500: Server error', code: 'API_ERROR', status: 500 },
    })

    const { result } = renderHook(() => usePixelGeneration())
    await act(async () => {
      await result.current.generate('test', {
        type: 'openai',
        apiUrl: 'https://api.openai.com',
        model: 'gpt-4o',
        apiKey: 'sk-test',
      })
    })

    expect(result.current.error).toBe('API 500: Server error')
    expect(result.current.isGenerating).toBe(false)
  })

  it('generate sets human-readable message for 401 error', async () => {
    mockGenerateFn.mockResolvedValueOnce({
      ok: false,
      error: { message: 'API 401: Unauthorized', code: 'API_ERROR', status: 401 },
    })

    const { result } = renderHook(() => usePixelGeneration())
    await act(async () => {
      await result.current.generate('test', {
        type: 'openai',
        apiUrl: 'https://api.openai.com',
        model: 'gpt-4o',
        apiKey: 'sk-test',
      })
    })

    expect(result.current.error).toBe('Invalid API key. Please check your key and try again.')
  })

  it('reset clears all state', () => {
    const { result } = renderHook(() => usePixelGeneration())
    act(() => {
      result.current.setSelectedType('Ninja')
    })
    act(() => {
      result.current.reset()
    })

    expect(result.current.pixelMap).toBeNull()
    expect(result.current.isGenerating).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('generate sets isGenerating true during call', async () => {
    mockGenerateFn.mockImplementationOnce(() => new Promise(() => {}))

    const { result } = renderHook(() => usePixelGeneration())
    act(() => {
      result.current.generate('test', {
        type: 'openai',
        apiUrl: 'https://api.openai.com',
        model: 'gpt-4o',
        apiKey: 'sk-test',
      })
    })

    expect(result.current.isGenerating).toBe(true)
  })
})
