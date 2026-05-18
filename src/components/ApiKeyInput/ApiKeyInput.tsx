import { useState } from 'react'
import styles from './ApiKeyInput.module.css'

interface ApiKeyInputProps {
  apiKey: string
  onChange: (key: string) => void
}

export function ApiKeyInput({ apiKey, onChange }: ApiKeyInputProps) {
  const [visible, setVisible] = useState(false)

  return (
    <div className={styles.wrapper}>
      <input
        className={styles.input}
        type={visible ? 'text' : 'password'}
        value={apiKey}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Enter your API key"
        aria-label="API Key"
      />
      <button
        className={styles.toggle}
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? 'Hide API key' : 'Show API key'}
      >
        {visible ? 'HIDE' : 'SHOW'}
      </button>
    </div>
  )
}
