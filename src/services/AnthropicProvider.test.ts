import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AnthropicProvider } from './AnthropicProvider'

const mockResponse = {
  palette: ['#000000', '#ffffff'],
  grid: [['#000000', '#ffffff'], ['#ffffff', '#000000']],
  label: 'Wizard',
}

describe('AnthropicProvider', () => {
  let provider: AnthropicProvider

  beforeEach(() => {
    provider = new AnthropicProvider()
    vi.restoreAllMocks()
  })

  it('sends correct request and returns parsed response on success', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({
        content: [{ text: JSON.stringify(mockResponse) }],
      }), { status: 200 }),
    )

    const result = await provider.generate({
      prompt: 'test prompt',
      apiUrl: 'https://api.anthropic.com',
      model: 'claude-sonnet-4-20250514',
      apiKey: 'sk-test',
    })

    expect(result.ok).toBe(true)
    if (result.ok) {
      expect(result.data.label).toBe('Wizard')
    }
  })

  it('sends POST to /v1/messages with x-api-key header', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({
        content: [{ text: JSON.stringify(mockResponse) }],
      }), { status: 200 }),
    )

    await provider.generate({
      prompt: 'test',
      apiUrl: 'https://api.anthropic.com',
      model: 'claude-sonnet-4-20250514',
      apiKey: 'sk-test',
    })

    const callUrl = fetchSpy.mock.calls[0][0]
    const callInit = fetchSpy.mock.calls[0][1] as RequestInit
    expect(callUrl).toBe('https://api.anthropic.com/v1/messages')
    expect(callInit.headers).toMatchObject({
      'x-api-key': 'sk-test',
      'anthropic-version': '2023-06-01',
    })
  })

  it('returns error on non-2xx response', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response('Unauthorized', { status: 401, statusText: 'Unauthorized' }),
    )

    const result = await provider.generate({
      prompt: 'test',
      apiUrl: 'https://api.anthropic.com',
      model: 'claude-sonnet-4-20250514',
      apiKey: 'sk-test',
    })

    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.code).toBe('API_ERROR')
      expect(result.error.status).toBe(401)
    }
  })

  it('returns error on network failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Network failure'))

    const result = await provider.generate({
      prompt: 'test',
      apiUrl: 'https://api.anthropic.com',
      model: 'claude-sonnet-4-20250514',
      apiKey: 'sk-test',
    })

    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.code).toBe('NETWORK_ERROR')
    }
  })

  it('returns error on empty response content', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ content: [] }), { status: 200 }),
    )

    const result = await provider.generate({
      prompt: 'test',
      apiUrl: 'https://api.anthropic.com',
      model: 'claude-sonnet-4-20250514',
      apiKey: 'sk-test',
    })

    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.code).toBe('PARSE_ERROR')
    }
  })

  it('returns error on 500 response', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response('Server Error', { status: 500, statusText: 'Internal Server Error' }),
    )

    const result = await provider.generate({
      prompt: 'test',
      apiUrl: 'https://api.anthropic.com',
      model: 'claude-sonnet-4-20250514',
      apiKey: 'sk-test',
    })

    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.status).toBe(500)
      expect(result.error.code).toBe('API_ERROR')
    }
  })
})
