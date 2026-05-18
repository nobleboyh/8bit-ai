import { useState, useCallback } from 'react'
import { generate as llmGenerate } from '@/services/llmClient'
import type { PixelMapResponse, LLMProviderType } from '@/types/pixelmap'

export function usePixelGeneration() {
  const [pixelMap, setPixelMap] = useState<PixelMapResponse | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedType, setSelectedType] = useState<string>('Wizard')

  const generate = useCallback(async (
    prompt: string,
    config: { type: LLMProviderType; apiUrl: string; model: string; apiKey: string },
  ) => {
    setIsGenerating(true)
    setError(null)
    setPixelMap(null)

    const result = await llmGenerate(config.type, {
      prompt,
      apiUrl: config.apiUrl,
      model: config.model,
      apiKey: config.apiKey,
    })

    if (result.ok) {
      setPixelMap(result.data)
    } else {
      if (result.error.code === 'API_ERROR' && result.error.status === 401) {
        setError('Invalid API key. Please check your key and try again.')
      } else {
        setError(result.error.message)
      }
    }
    setIsGenerating(false)
  }, [])

  const reset = useCallback(() => {
    setPixelMap(null)
    setIsGenerating(false)
    setError(null)
  }, [])

  return { pixelMap, isGenerating, error, selectedType, setSelectedType, generate, reset }
}
