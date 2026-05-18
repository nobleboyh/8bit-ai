import { useState } from 'react'
import { useTheme } from '@/hooks/useTheme'
import { useApiKey } from '@/hooks/useApiKey'
import { useProviderConfig } from '@/hooks/useProviderConfig'
import { ThemeToggle } from '@/components/ThemeToggle/ThemeToggle'
import { ApiKeyInput } from '@/components/ApiKeyInput/ApiKeyInput'
import { ProviderSelect } from '@/components/ProviderSelect/ProviderSelect'
import { ControlPanel } from '@/components/ControlPanel/ControlPanel'
import { ViewerShell } from '@/components/ViewerShell/ViewerShell'
import styles from './App.module.css'

export function App() {
  const { theme, toggleTheme } = useTheme()
  const { apiKey, setApiKey } = useApiKey()
  const {
    providerType,
    apiUrl,
    model,
    savedNotice,
    setProviderType,
    setApiUrl,
    setModel,
  } = useProviderConfig()

  const [prompt, setPrompt] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)

  const handleGenerate = () => {
    if (!prompt.trim() || !apiKey) return
    setIsGenerating(true)
    // Generation flow will be implemented in Epic 2
  }

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>PIXELFORGE</h1>
          <p className={styles.subtitle}>8-BIT AVATAR GENERATOR</p>
        </div>
        <ThemeToggle theme={theme} onToggle={toggleTheme} />
      </header>

      <section className={styles.section}>
        <h2 className={styles['section-label']}>01 // CONFIG</h2>
        <div className={styles.field}>
          <label className={styles.fieldLabel}>Provider</label>
          <ProviderSelect value={providerType} onChange={setProviderType} />
        </div>
        <div className={styles.field}>
          <label className={styles.fieldLabel}>API URL</label>
          <input
            className={styles.textInput}
            type="text"
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            aria-label="API URL"
          />
        </div>
        <div className={styles.field}>
          <label className={styles.fieldLabel}>Model</label>
          <input
            className={styles.textInput}
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            aria-label="Model"
          />
        </div>
        <div className={styles.field}>
          <label className={styles.fieldLabel}>API Key</label>
          <ApiKeyInput apiKey={apiKey} onChange={setApiKey} />
        </div>
        {savedNotice && (
          <p className={styles.notice}>Settings saved locally</p>
        )}
      </section>

      <section className={styles.section}>
        <h2 className={styles['section-label']}>02 // PROMPT</h2>
        <ControlPanel
          prompt={prompt}
          onPromptChange={setPrompt}
          onGenerate={handleGenerate}
          isGenerating={isGenerating}
          hasApiKey={!!apiKey}
        />
      </section>

      <section className={styles.section}>
        <h2 className={styles['section-label']}>03 // AVATAR</h2>
        <ViewerShell state="empty" />
      </section>
    </div>
  )
}
