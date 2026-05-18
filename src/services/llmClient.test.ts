import { describe, it, expect, vi, beforeEach } from 'vitest'
import { generate } from './llmClient'

const mockPixelMap = {
  palette: ['#000'],
  grid: [['#000']],
  label: 'Test',
}

describe('llmClient', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('dispatches to anthropic provider', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Network error'))
    const result = await generate('anthropic', {
      prompt: 'test',
      apiUrl: 'https://api.anthropic.com',
      model: 'claude-sonnet-4-20250514',
      apiKey: 'sk-test',
    })
    expect(result.ok).toBe(false)
  })

  it('dispatches to openai provider', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Network error'))
    const result = await generate('openai', {
      prompt: 'test',
      apiUrl: 'https://api.openai.com',
      model: 'gpt-4o',
      apiKey: 'sk-test',
    })
    expect(result.ok).toBe(false)
  })

  it('dispatches to openai-compatible provider', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Network error'))
    const result = await generate('openai-compatible', {
      prompt: 'test',
      apiUrl: 'https://api.together.xyz',
      model: 'meta-llama/Llama-3.3-70B-Instruct-Turbo',
      apiKey: 'sk-test',
    })
    expect(result.ok).toBe(false)
  })

  it('dispatches to deepseek provider and succeeds with mock', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({
        choices: [{ message: { content: JSON.stringify(mockPixelMap) } }],
      }), { status: 200 }),
    )

    const result = await generate('deepseek', {
      prompt: 'test',
      apiUrl: 'https://api.deepseek.com',
      model: 'deepseek-v4-flash',
      apiKey: 'sk-test',
    })

    expect(result.ok).toBe(true)
    if (result.ok) {
      expect(result.data.label).toBe('Test')
    }
  })

  it('returns error for unknown provider type', async () => {
    const result = await generate('unknown' as never, {
      prompt: 'test',
      apiUrl: 'https://api.example.com',
      model: 'test',
      apiKey: 'sk-test',
    })
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.code).toBe('INVALID_PROVIDER')
    }
  })
})
