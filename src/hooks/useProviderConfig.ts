import { useState, useCallback } from 'react'
import { PROVIDER_PRESETS, type LLMProviderType, type ProviderConfig } from '@/types/pixelmap'

const STORAGE_KEYS = {
  provider: 'pixelforge-provider',
  apiUrl: 'pixelforge-api-url',
  model: 'pixelforge-model',
  apiKey: 'pixelforge-api-key',
}

function loadFromStorage(): Partial<ProviderConfig> {
  try {
    return {
      type: (localStorage.getItem(STORAGE_KEYS.provider) as LLMProviderType) || undefined,
      apiUrl: localStorage.getItem(STORAGE_KEYS.apiUrl) || undefined,
      model: localStorage.getItem(STORAGE_KEYS.model) || undefined,
      apiKey: localStorage.getItem(STORAGE_KEYS.apiKey) || undefined,
    }
  } catch {
    return {}
  }
}

function getPreset(type: LLMProviderType) {
  return PROVIDER_PRESETS.find((p) => p.type === type)
}

export function useProviderConfig() {
  const saved = loadFromStorage()
  const initialType = saved.type || 'anthropic'
  const preset = getPreset(initialType)

  const [providerType, setProviderType] = useState<LLMProviderType>(initialType)
  const [apiUrl, setApiUrl] = useState(saved.apiUrl || preset?.apiUrl || '')
  const [model, setModel] = useState(saved.model || preset?.model || '')
  const [overrideUrl, setOverrideUrl] = useState(!!saved.apiUrl)
  const [overrideModel, setOverrideModel] = useState(!!saved.model)
  const [savedNotice, setSavedNotice] = useState(false)

  const handleProviderChange = useCallback(
    (type: LLMProviderType) => {
      setProviderType(type)
      const preset = getPreset(type)
      if (preset) {
        if (!overrideUrl) setApiUrl(preset.apiUrl)
        if (!overrideModel) setModel(preset.model)
      }
    },
    [overrideUrl, overrideModel],
  )

  const handleUrlChange = useCallback((url: string) => {
    setApiUrl(url)
    setOverrideUrl(true)
  }, [])

  const handleModelChange = useCallback((model: string) => {
    setModel(model)
    setOverrideModel(true)
  }, [])

  const saveToStorage = useCallback((apiKey: string) => {
    try {
      localStorage.setItem(STORAGE_KEYS.provider, providerType)
      localStorage.setItem(STORAGE_KEYS.apiUrl, apiUrl)
      localStorage.setItem(STORAGE_KEYS.model, model)
      if (apiKey) localStorage.setItem(STORAGE_KEYS.apiKey, apiKey)
    } catch {
      // localStorage may be full or unavailable
    }
    setSavedNotice(true)
    setTimeout(() => setSavedNotice(false), 3000)
  }, [providerType, apiUrl, model])

  return {
    providerType,
    apiUrl,
    model,
    savedNotice,
    setProviderType: handleProviderChange,
    setApiUrl: handleUrlChange,
    setModel: handleModelChange,
    saveToStorage,
    setProviderTypeRaw: setProviderType,
    setApiUrlRaw: setApiUrl,
    setModelRaw: setModel,
  }
}
