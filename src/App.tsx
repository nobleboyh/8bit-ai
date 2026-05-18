import { useState, useCallback } from 'react'
import { useTheme } from '@/hooks/useTheme'
import { useApiKey } from '@/hooks/useApiKey'
import { useProviderConfig } from '@/hooks/useProviderConfig'
import { usePixelGeneration } from '@/hooks/usePixelGeneration'
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

  const {
    pixelMap,
    isGenerating,
    error,
    selectedType,
    setSelectedType,
    generate,
    reset,
  } = usePixelGeneration()

  const [prompt, setPrompt] = useState('')

  const handleGenerate = useCallback(() => {
    if (!prompt.trim() || !apiKey) return
    const fullPrompt = `Generate a pixel avatar for a ${selectedType} character named ${prompt}.`
    generate(fullPrompt, { type: providerType, apiUrl, model, apiKey })
  }, [prompt, apiKey, selectedType, generate, providerType, apiUrl, model])

  const handleReForge = useCallback(() => {
    reset()
  }, [reset])

  const getViewerState = () => {
    if (isGenerating) return 'loading'
    if (error) return 'error'
    if (pixelMap) return 'result'
    return 'empty'
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
          selectedType={selectedType}
          onTypeSelect={setSelectedType}
        />
      </section>

      <section className={styles.section}>
        <h2 className={styles['section-label']}>03 // AVATAR</h2>
        <ViewerShell
          state={getViewerState()}
          pixelMap={pixelMap}
          isGenerating={isGenerating}
          error={error}
          selectedType={selectedType}
          prompt={prompt}
          onReForge={handleReForge}
        />
      </section>
    </div>
  )
}
