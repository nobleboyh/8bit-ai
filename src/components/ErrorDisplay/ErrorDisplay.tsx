import styles from './ErrorDisplay.module.css'

interface ErrorDisplayProps {
  message: string
  onDismiss?: () => void
}

export function ErrorDisplay({ message, onDismiss }: ErrorDisplayProps) {
  return (
    <div className={styles.errorBox} role="alert">
      <p className={styles.message}>{message}</p>
      {onDismiss && (
        <button className={styles.dismiss} onClick={onDismiss} aria-label="Dismiss error">
          &#x2715;
        </button>
      )}
    </div>
  )
}
