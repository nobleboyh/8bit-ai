import { buildAvatarHTML } from '@/utils/buildAvatarHTML'
import { sanitize } from '@/utils/sanitize'

export function htmlExport(grid: string[][], label: string, prefix: string, username: string): void {
  if (!document.body) return

  let html: string
  try {
    html = buildAvatarHTML(grid, label, prefix, username)
  } catch {
    return
  }

  const blob = new Blob([html], { type: 'text/html' })

  const safeType = sanitize(prefix) || 'avatar'
  const safeName = sanitize(username) || 'avatar'

  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `pixelforce-${safeType}-${safeName}.html`
  a.style.display = 'none'
  document.body.appendChild(a)
  try {
    a.click()
    document.body.removeChild(a)
  } finally {
    URL.revokeObjectURL(url)
  }
}
