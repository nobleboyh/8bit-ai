import { describe, it, expect, vi, beforeEach } from 'vitest'
import { OpenAICompatibleProvider } from './OpenAICompatibleProvider'

const mockResponse = {
  palette: ['#000000', '#ffffff'],
  grid: [['#000000', '#ffffff'], ['#ffffff', '#000000']],
  label: 'Robot',
}

describe('OpenAICompatibleProvider', () => {
  let provider: OpenAICompatibleProvider

  beforeEach(() => {
    provider = new OpenAICompatibleProvider()
    vi.restoreAllMocks()
  })

  it('sends correct request and returns parsed response on success', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({
        choices: [{ message: { content: JSON.stringify(mockResponse) } }],
      }), { status: 200 }),
    )

    const result = await provider.generate({
      prompt: 'test prompt',
      apiUrl: 'https://api.together.xyz',
      model: 'meta-llama/Llama-3.3-70B-Instruct-Turbo',
      apiKey: 'sk-test',
    })

    expect(result.ok).toBe(true)
    if (result.ok) {
      expect(result.data.label).toBe('Robot')
    }
  })

  it('uses default model when none provided', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({
        choices: [{ message: { content: JSON.stringify(mockResponse) } }],
      }), { status: 200 }),
    )

    await provider.generate({
      prompt: 'test',
      apiUrl: 'https://api.together.xyz',
      model: '',
      apiKey: 'sk-test',
    })

    const callInit = fetchSpy.mock.calls[0][1] as RequestInit
    const body = JSON.parse(callInit.body as string)
    expect(body.model).toBe('meta-llama/Llama-3.3-70B-Instruct-Turbo')
  })

  it('returns error on network failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Network failure'))

    const result = await provider.generate({
      prompt: 'test',
      apiUrl: 'https://api.together.xyz',
      model: 'meta-llama/Llama-3.3-70B-Instruct-Turbo',
      apiKey: 'sk-test',
    })

    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.code).toBe('NETWORK_ERROR')
    }
  })
})
