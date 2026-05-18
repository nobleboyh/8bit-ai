import { buildAvatarHTML } from '@/utils/buildAvatarHTML'

function sanitize(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9-]/g, '').replace(/-+/g, '-').replace(/^-|-$/g, '')
}

export function htmlExport(grid: string[][], label: string, prefix: string, username: string): void {
  const html = buildAvatarHTML(grid, label, prefix, username)
  const blob = new Blob([html], { type: 'text/html' })

  const safeType = sanitize(prefix) || 'avatar'
  const safeName = sanitize(username) || 'avatar'

  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `pixelforce-${safeType}-${safeName}.html`
  a.style.display = 'none'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
