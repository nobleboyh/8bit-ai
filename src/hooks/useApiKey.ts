import { useState, useCallback } from 'react'

const SESSION_KEY = 'pixelforge-api-key'

function getSessionKey(): string {
  try {
    return sessionStorage.getItem(SESSION_KEY) ?? ''
  } catch {
    return ''
  }
}

function setSessionKey(key: string) {
  try {
    if (key) {
      sessionStorage.setItem(SESSION_KEY, key)
    } else {
      sessionStorage.removeItem(SESSION_KEY)
    }
  } catch {
    // sessionStorage may be full or unavailable
  }
}

function removeSessionKey() {
  try {
    sessionStorage.removeItem(SESSION_KEY)
  } catch {
    // sessionStorage may be full or unavailable
  }
}

export function useApiKey() {
  const [apiKey, setApiKeyState] = useState<string>(() => {
    return getSessionKey()
  })

  const setApiKey = useCallback((key: string) => {
    setApiKeyState(key)
    setSessionKey(key)
  }, [])

  const clearKey = useCallback(() => {
    setApiKeyState('')
    removeSessionKey()
  }, [])

  return { apiKey, setApiKey, clearKey }
}
