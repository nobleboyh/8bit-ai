import type { PixelMapResponse, Result } from '@/types/pixelmap'

const HEX6_RE = /^#[0-9a-fA-F]{6}$/

export function parsePixelMapResponse(raw: string): Result<PixelMapResponse> {
  try {
    const parsed = JSON.parse(raw) as Partial<PixelMapResponse>

    if (!Array.isArray(parsed.palette) || parsed.palette.length === 0) {
      return { ok: false, error: { message: 'Missing required field: palette', code: 'PARSE_ERROR' } }
    }
    if (!parsed.palette.every((c): c is string => typeof c === 'string' && HEX6_RE.test(c))) {
      return { ok: false, error: { message: 'Invalid palette: all values must be 6-digit hex colors', code: 'PARSE_ERROR' } }
    }
    if (!Array.isArray(parsed.grid) || parsed.grid.length === 0) {
      return { ok: false, error: { message: 'Missing required field: grid', code: 'PARSE_ERROR' } }
    }
    if (!parsed.grid.every((row): row is string[] => Array.isArray(row) && row.length === parsed.grid.length)) {
      return { ok: false, error: { message: 'Invalid grid: each row must be an array with length matching grid size', code: 'PARSE_ERROR' } }
    }
    if (!parsed.grid.every((row) => row.every((c): c is string => typeof c === 'string' && HEX6_RE.test(c)))) {
      return { ok: false, error: { message: 'Invalid grid: all cell values must be 6-digit hex colors', code: 'PARSE_ERROR' } }
    }
    if (!parsed.label || typeof parsed.label !== 'string') {
      return { ok: false, error: { message: 'Missing required field: label', code: 'PARSE_ERROR' } }
    }

    return { ok: true, data: parsed as PixelMapResponse }
  } catch {
    return { ok: false, error: { message: 'Invalid JSON response from API', code: 'PARSE_ERROR' } }
  }
}
