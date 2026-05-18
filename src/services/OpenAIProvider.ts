import type { PixelGenRequest, PixelMapResponse, Result, AppError } from '@/types/pixelmap'
import type { LLMProvider } from '@/services/providers'
import { parsePixelMapResponse } from '@/services/parseResponse'

const SYSTEM_PROMPT = `You are a pixel avatar generator. Respond ONLY with valid JSON matching this schema:
{
  "palette": ["#RRGGBB", ...],
  "grid": [["#RRGGBB", ...], ...],
  "label": "character name"
}
The grid must be 16x16, every cell a valid 6-digit hex color. Use a reduced 64-color NES-inspired palette. The label is the display name shown beneath the avatar.`

export class OpenAIProvider implements LLMProvider {
  async generate(request: PixelGenRequest): Promise<Result<PixelMapResponse>> {
    try {
      const response = await fetch(`${request.apiUrl}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${request.apiKey}`,
        },
        body: JSON.stringify({
          model: request.model,
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
          error: { message: 'Empty response from OpenAI API', code: 'PARSE_ERROR' },
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
