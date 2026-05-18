import { useState, useCallback, useRef, useEffect } from 'react'
import { PROVIDER_PRESETS, type LLMProviderType } from '@/types/pixelmap'

const STORAGE_KEYS = {
  provider: 'pixelforge-provider',
  apiUrl: 'pixelforge-api-url',
  model: 'pixelforge-model',
}

interface SavedConfig {
  type?: LLMProviderType
  apiUrl?: string
  model?: string
}

function loadFromStorage(): SavedConfig {
  try {
    return {
      type: (localStorage.getItem(STORAGE_KEYS.provider) as LLMProviderType) || undefined,
      apiUrl: localStorage.getItem(STORAGE_KEYS.apiUrl) || undefined,
      model: localStorage.getItem(STORAGE_KEYS.model) || undefined,
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
  const initialType = saved.type && PROVIDER_PRESETS.some((p) => p.type === saved.type)
    ? saved.type
    : 'anthropic'
  const preset = getPreset(initialType)

  const [providerType, setProviderType] = useState<LLMProviderType>(initialType)
  const [apiUrl, setApiUrl] = useState(saved.apiUrl || preset?.apiUrl || '')
  const [model, setModel] = useState(saved.model || preset?.model || '')
  const [overrideUrl, setOverrideUrl] = useState(!!saved.apiUrl)
  const [overrideModel, setOverrideModel] = useState(!!saved.model)
  const [savedNotice, setSavedNotice] = useState(false)
  const noticeTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEYS.provider, providerType)
      localStorage.setItem(STORAGE_KEYS.apiUrl, apiUrl)
      localStorage.setItem(STORAGE_KEYS.model, model)
    } catch {
      // localStorage may be full or unavailable
    }
    setSavedNotice(true)
    if (noticeTimer.current) clearTimeout(noticeTimer.current)
    noticeTimer.current = setTimeout(() => setSavedNotice(false), 3000)
    return () => {
      if (noticeTimer.current) clearTimeout(noticeTimer.current)
    }
  }, [providerType, apiUrl, model])

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

  const resetOverrides = useCallback(() => {
    setOverrideUrl(false)
    setOverrideModel(false)
  }, [])

  const handleUrlChange = useCallback((url: string) => {
    setApiUrl(url)
    setOverrideUrl(true)
  }, [])

  const handleModelChange = useCallback((model: string) => {
    setModel(model)
    setOverrideModel(true)
  }, [])

  const saveToStorage = useCallback(() => {
    try {
      localStorage.setItem(STORAGE_KEYS.provider, providerType)
      localStorage.setItem(STORAGE_KEYS.apiUrl, apiUrl)
      localStorage.setItem(STORAGE_KEYS.model, model)
    } catch {
      // localStorage may be full or unavailable
    }
    setSavedNotice(true)
    if (noticeTimer.current) clearTimeout(noticeTimer.current)
    noticeTimer.current = setTimeout(() => setSavedNotice(false), 3000)
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
    resetOverrides,
  }
}
