import type { PixelGenRequest, PixelMapResponse, Result, AppError } from '@/types/pixelmap'
import type { LLMProvider } from '@/services/providers'
import { parsePixelMapResponse } from '@/services/parseResponse'
import { SYSTEM_PROMPT } from '@/services/constants'

const DEFAULT_MODEL = 'deepseek-v4-flash'

export class DeepSeekProvider implements LLMProvider {
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
          thinking: { type: 'disabled' },
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
      const choice = data.choices?.[0]
      const content = choice?.message?.content
      const finishReason = choice?.finish_reason

      if (!content) {
        return {
          ok: false,
          error: { message: 'Empty response from DeepSeek API', code: 'PARSE_ERROR' },
        }
      }

      const result = parsePixelMapResponse(content)
      if (finishReason === 'length') {
        const truncMsg = 'The model ran out of output tokens before completing the avatar. Try a simpler character description or increase max_tokens.'
        if (!result.ok) {
          return {
            ok: false,
            error: { message: `${result.error.message}. ${truncMsg}`, code: 'TRUNCATED_RESPONSE' },
          }
        }
        return {
          ok: false,
          error: { message: truncMsg, code: 'TRUNCATED_RESPONSE' },
        }
      }

      return result
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
