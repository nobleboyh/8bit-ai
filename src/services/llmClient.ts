import type { LLMProviderType, PixelGenRequest, PixelMapResponse, Result } from '@/types/pixelmap'
import { AnthropicProvider } from '@/services/AnthropicProvider'
import { OpenAIProvider } from '@/services/OpenAIProvider'
import { OpenAICompatibleProvider } from '@/services/OpenAICompatibleProvider'
import { DeepSeekProvider } from '@/services/DeepSeekProvider'
import type { LLMProvider } from '@/services/providers'

let providers: Record<LLMProviderType, LLMProvider> | null = null

function getProviders(): Record<LLMProviderType, LLMProvider> {
  if (!providers) {
    providers = {
      anthropic: new AnthropicProvider(),
      openai: new OpenAIProvider(),
      'openai-compatible': new OpenAICompatibleProvider(),
      deepseek: new DeepSeekProvider(),
    }
  }
  return providers
}

export async function generate(
  providerType: LLMProviderType,
  request: PixelGenRequest,
): Promise<Result<PixelMapResponse>> {
  const provider = getProviders()[providerType]
  if (!provider) {
    return {
      ok: false,
      error: { message: `Unknown provider type: ${providerType}`, code: 'INVALID_PROVIDER' },
    }
  }
  return provider.generate(request)
}
