import { useState, useCallback } from 'react'

const SESSION_KEY = 'pixelforge-api-key'

export function useApiKey() {
  const [apiKey, setApiKeyState] = useState<string>(() => {
    return sessionStorage.getItem(SESSION_KEY) ?? ''
  })

  const setApiKey = useCallback((key: string) => {
    setApiKeyState(key)
    if (key) {
      sessionStorage.setItem(SESSION_KEY, key)
    } else {
      sessionStorage.removeItem(SESSION_KEY)
    }
  }, [])

  const clearKey = useCallback(() => {
    setApiKeyState('')
    sessionStorage.removeItem(SESSION_KEY)
  }, [])

  return { apiKey, setApiKey, clearKey }
}
