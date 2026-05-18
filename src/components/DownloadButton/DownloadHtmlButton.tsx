import type { PixelMapResponse } from '@/types/pixelmap'
import { htmlExport } from '@/utils/htmlExport'
import styles from './DownloadHtmlButton.module.css'

interface DownloadHtmlButtonProps {
  pixelMap: PixelMapResponse | null
  prefix: string
  username: string
}

export function DownloadHtmlButton({ pixelMap, prefix, username }: DownloadHtmlButtonProps) {
  if (!pixelMap) return null

  return (
    <button
      className={styles.btn}
      onClick={() => htmlExport(pixelMap.grid, pixelMap.label, prefix, username)}
      aria-label="Download HTML"
    >
      DOWNLOAD HTML
    </button>
  )
}
