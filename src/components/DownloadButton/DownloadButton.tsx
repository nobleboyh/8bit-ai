import { useCallback } from 'react'
import type { PixelMapResponse } from '@/types/pixelmap'
import { exportAsPng } from '@/utils/pngExport'
import styles from './DownloadButton.module.css'

interface DownloadButtonProps {
  pixelMap: PixelMapResponse | null
  type: string
  name: string
}

export function DownloadButton({ pixelMap, type, name }: DownloadButtonProps) {
  const handleDownload = useCallback(() => {
    if (!pixelMap) return
    exportAsPng(pixelMap, type, name)
  }, [pixelMap, type, name])

  return (
    <button
      className={styles.btn}
      onClick={handleDownload}
      disabled={!pixelMap}
      aria-label="Download PNG"
    >
      DOWNLOAD PNG
    </button>
  )
}
