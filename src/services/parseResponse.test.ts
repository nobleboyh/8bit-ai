import { describe, it, expect } from 'vitest'
import { parsePixelMapResponse } from './parseResponse'

const validResponse = {
  palette: ['#000000', '#ffffff', '#ff0000'],
  grid: [
    ['#000000', '#ffffff'],
    ['#ff0000', '#000000'],
  ],
  label: 'Test Avatar',
}

describe('parsePixelMapResponse', () => {
  it('parses valid response', () => {
    const result = parsePixelMapResponse(JSON.stringify(validResponse))
    expect(result.ok).toBe(true)
    if (result.ok) {
      expect(result.data.label).toBe('Test Avatar')
      expect(result.data.palette).toHaveLength(3)
      expect(result.data.grid).toHaveLength(2)
    }
  })

  it('returns error for malformed JSON', () => {
    const result = parsePixelMapResponse('not json')
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.code).toBe('PARSE_ERROR')
      expect(result.error.message).toContain('Invalid JSON')
    }
  })

  it('returns error for missing palette', () => {
    const { palette, ...rest } = validResponse
    const result = parsePixelMapResponse(JSON.stringify(rest))
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.message).toContain('palette')
    }
  })

  it('returns error for empty palette', () => {
    const result = parsePixelMapResponse(JSON.stringify({ ...validResponse, palette: [] }))
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.message).toContain('palette')
    }
  })

  it('returns error for missing grid', () => {
    const { grid, ...rest } = validResponse
    const result = parsePixelMapResponse(JSON.stringify(rest))
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.message).toContain('grid')
    }
  })

  it('returns error for missing label', () => {
    const { label, ...rest } = validResponse
    const result = parsePixelMapResponse(JSON.stringify(rest))
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.message).toContain('label')
    }
  })

  it('returns error for non-string label', () => {
    const result = parsePixelMapResponse(JSON.stringify({ ...validResponse, label: 123 }))
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.message).toContain('label')
    }
  })
})
