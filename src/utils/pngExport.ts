import type { PixelMapResponse } from '@/types/pixelmap'

export function exportAsPng(pixelMap: PixelMapResponse, type: string, name: string): void {
  const size = pixelMap.grid.length
  const scale = 16
  const canvas = new OffscreenCanvas(size * scale, size * scale)
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  pixelMap.grid.forEach((row, y) => {
    row.forEach((colour, x) => {
      ctx.fillStyle = colour
      ctx.fillRect(x * scale, y * scale, scale, scale)
    })
  })

  const sanitize = (s: string) => s.toLowerCase().replace(/[^a-z0-9-]/g, '').replace(/-+/g, '-').replace(/^-|-$/g, '')
  const safeType = sanitize(type) || 'avatar'
  const safeName = sanitize(name) || 'avatar'

  canvas.convertToBlob({ type: 'image/png' })
    .then((blob) => {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `pixelforce-${safeType}-${safeName}.png`
      a.style.display = 'none'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    })
    .catch(() => {
      // Silently fail — export is best-effort
    })
}
