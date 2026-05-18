import styles from './ViewerShell.module.css'

export type ViewerState = 'empty' | 'loading' | 'result' | 'error'

interface ViewerShellProps {
  state: ViewerState
}

export function ViewerShell({ state }: ViewerShellProps) {
  if (state !== 'empty') return null

  return (
    <div className={styles.viewer} role="status" aria-label="Avatar viewer">
      <div className={styles.icon} role="img" aria-hidden={true}>&#x25A3;</div>
      <p className={styles.text}>ENTER A PROMPT & FORGE YOUR PIXEL</p>
    </div>
  )
}
