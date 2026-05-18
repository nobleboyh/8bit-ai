import type { PixelMapResponse } from '@/types/pixelmap'

export function exportAsPng(pixelMap: PixelMapResponse, type: string, name: string): void {
  const size = pixelMap.grid.length
  const scale = 16
  const canvas = new OffscreenCanvas(size * scale, size * scale)
  const ctx = canvas.getContext('2d')!

  pixelMap.grid.forEach((row, y) => {
    row.forEach((colour, x) => {
      ctx.fillStyle = colour
      ctx.fillRect(x * scale, y * scale, scale, scale)
    })
  })

  canvas.convertToBlob({ type: 'image/png' }).then((blob) => {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `pixelforce-${type.toLowerCase()}-${name.toLowerCase().replace(/\s+/g, '-')}.png`
    a.style.display = 'none'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  })
}
