import type { PixelGenRequest, PixelMapResponse, Result, AppError } from '@/types/pixelmap'
import type { LLMProvider } from '@/services/providers'
import { parsePixelMapResponse } from '@/services/parseResponse'
import { SYSTEM_PROMPT } from '@/services/constants'

export class AnthropicProvider implements LLMProvider {
  async generate(request: PixelGenRequest): Promise<Result<PixelMapResponse>> {
    try {
      const response = await fetch(`${request.apiUrl}/v1/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': request.apiKey,
          'anthropic-version': '2025-01-01',
        },
        body: JSON.stringify({
          model: request.model,
          max_tokens: 8192,
          system: SYSTEM_PROMPT,
          messages: [{ role: 'user', content: request.prompt }],
        }),
      })

      if (!response.ok) {
        const statusText = await response.text().catch(() => response.statusText)
        return {
          ok: false,
          error: {
            message: `API ${response.status}: ${statusText}`,
            code: 'API_ERROR',
            status: response.status,
          } satisfies AppError,
        }
      }

      const data = await response.json()
      const content = data.content?.[0]?.text
      if (!content) {
        return {
          ok: false,
          error: { message: 'Empty response from Anthropic API', code: 'PARSE_ERROR' },
        }
      }

      return parsePixelMapResponse(content)
    } catch (err) {
      return {
        ok: false,
        error: {
          message: `Network error: ${err instanceof Error ? err.message : 'Unknown'}`,
          code: 'NETWORK_ERROR',
        },
      }
    }
  }
}
