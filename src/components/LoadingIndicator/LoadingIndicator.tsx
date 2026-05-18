import styles from './LoadingIndicator.module.css'

export function LoadingIndicator() {
  return (
    <div className={styles.container} role="status" aria-label="Generating avatar">
      <div className={styles.pixel} />
      <p className={styles.text}>GENERATING...</p>
    </div>
  )
}
