import { useCallback } from 'react'
import type { PixelMapResponse } from '@/types/pixelmap'
import { htmlExport } from '@/utils/htmlExport'
import styles from './DownloadHtmlButton.module.css'

interface DownloadHtmlButtonProps {
  pixelMap: PixelMapResponse | null
  type: string
  name: string
}

export function DownloadHtmlButton({ pixelMap, type, name }: DownloadHtmlButtonProps) {
  const handleDownload = useCallback(() => {
    if (!pixelMap) return
    htmlExport(pixelMap.grid, pixelMap.label, type, name)
  }, [pixelMap, type, name])

  return (
    <button
      className={styles.btn}
      onClick={handleDownload}
      disabled={!pixelMap}
      aria-label="Download HTML"
    >
      DOWNLOAD HTML
    </button>
  )
}
