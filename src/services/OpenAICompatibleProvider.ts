import type { PixelGenRequest, PixelMapResponse, Result, AppError } from '@/types/pixelmap'
import type { LLMProvider } from '@/services/providers'
import { parsePixelMapResponse } from '@/services/parseResponse'
import { SYSTEM_PROMPT } from '@/services/constants'

const DEFAULT_MODEL = 'meta-llama/Llama-3.3-70B-Instruct-Turbo'

export class OpenAICompatibleProvider implements LLMProvider {
  async generate(request: PixelGenRequest): Promise<Result<PixelMapResponse>> {
    const model = request.model || DEFAULT_MODEL

    try {
      const response = await fetch(`${request.apiUrl}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${request.apiKey}`,
        },
        body: JSON.stringify({
          model,
          max_tokens: 8192,
          messages: [
            { role: 'system', content: SYSTEM_PROMPT },
            { role: 'user', content: request.prompt },
          ],
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
      const content = data.choices?.[0]?.message?.content
      if (!content) {
        return {
          ok: false,
          error: { message: 'Empty response from API', code: 'PARSE_ERROR' },
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
