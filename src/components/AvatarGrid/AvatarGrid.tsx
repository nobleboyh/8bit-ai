import type { PixelMapResponse } from '@/types/pixelmap'
import styles from './AvatarGrid.module.css'

interface AvatarGridProps {
  pixelMap: PixelMapResponse
  type: string
}

export function AvatarGrid({ pixelMap, type }: AvatarGridProps) {
  const gridSize = pixelMap.grid.length
  const cellCount = pixelMap.palette.length

  return (
    <div className={styles.container} data-type={type}>
      <div
        className={styles.grid}
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${gridSize}, 1fr)`,
          width: 256,
          height: 256,
        }}
      >
        {pixelMap.grid.flatMap((row, y) =>
          row.map((colour, x) => (
            <div
              key={`${y}-${x}`}
              style={{ backgroundColor: colour }}
            />
          ))
        )}
      </div>
      <p className={styles.label}>{pixelMap.label}</p>
      <p className={styles.metadata}>
        {gridSize}&times;{gridSize} &middot; {cellCount} colours
      </p>
    </div>
  )
}
