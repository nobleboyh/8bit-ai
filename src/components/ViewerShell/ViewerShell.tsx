import type { PixelMapResponse } from '@/types/pixelmap'
import { ErrorDisplay } from '@/components/ErrorDisplay/ErrorDisplay'
import { AvatarGrid } from '@/components/AvatarGrid/AvatarGrid'
import { LoadingIndicator } from '@/components/LoadingIndicator/LoadingIndicator'
import { DownloadButton } from '@/components/DownloadButton/DownloadButton'
import styles from './ViewerShell.module.css'

export type ViewerState = 'empty' | 'loading' | 'result' | 'error'

interface ViewerShellProps {
  state: ViewerState
  pixelMap?: PixelMapResponse | null
  isGenerating?: boolean
  error?: string | null
  selectedType?: string
  prompt?: string
  onReForge?: () => void
}

export function ViewerShell({
  state,
  pixelMap,
  isGenerating,
  error,
  selectedType,
  prompt,
  onReForge,
}: ViewerShellProps) {
  if (state === 'loading' || isGenerating) {
    return (
      <div className={styles.viewer} role="status" aria-label="Generating avatar">
        <LoadingIndicator />
      </div>
    )
  }

  if (state === 'error' && error) {
    return (
      <div className={styles.viewer} role="status" aria-label="Avatar viewer">
        <ErrorDisplay message={error} />
      </div>
    )
  }

  if (state === 'result' && pixelMap) {
    return (
      <div className={styles.viewer} role="region" aria-label="Avatar result">
        <AvatarGrid pixelMap={pixelMap} type={selectedType || 'character'} />
        <div className={styles.actionRow}>
          <DownloadButton pixelMap={pixelMap} type={selectedType || 'character'} name={prompt || 'avatar'} />
          <button className={styles.btn} onClick={onReForge} disabled={isGenerating}>
            RE-FORGE
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.viewer} role="region" aria-label="Avatar viewer">
      <div className={styles.icon} role="img" aria-hidden={true}>&#x25A3;</div>
      <p className={styles.text}>ENTER A PROMPT & FORGE YOUR PIXEL</p>
    </div>
  )
}
