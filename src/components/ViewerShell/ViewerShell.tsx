import styles from './ViewerShell.module.css'

type ViewerState = 'empty' | 'loading' | 'result' | 'error'

interface ViewerShellProps {
  state: ViewerState
}

export function ViewerShell({ state }: ViewerShellProps) {
  if (state !== 'empty') return null

  return (
    <div className={styles.viewer}>
      <div className={styles.icon}>&#x25A3;</div>
      <p className={styles.text}>ENTER A PROMPT & FORGE YOUR PIXEL</p>
    </div>
  )
}
