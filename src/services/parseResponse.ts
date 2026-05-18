import type { PixelMapResponse, Result } from '@/types/pixelmap'

export function parsePixelMapResponse(raw: string): Result<PixelMapResponse> {
  try {
    const parsed = JSON.parse(raw) as Partial<PixelMapResponse>

    if (!Array.isArray(parsed.palette) || parsed.palette.length === 0) {
      return { ok: false, error: { message: 'Missing required field: palette', code: 'PARSE_ERROR' } }
    }
    if (!Array.isArray(parsed.grid) || parsed.grid.length === 0) {
      return { ok: false, error: { message: 'Missing required field: grid', code: 'PARSE_ERROR' } }
    }
    if (!parsed.label || typeof parsed.label !== 'string') {
      return { ok: false, error: { message: 'Missing required field: label', code: 'PARSE_ERROR' } }
    }

    return { ok: true, data: parsed as PixelMapResponse }
  } catch {
    return { ok: false, error: { message: 'Invalid JSON response from API', code: 'PARSE_ERROR' } }
  }
}
