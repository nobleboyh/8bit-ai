import type { LLMProviderType, PixelGenRequest, PixelMapResponse, Result } from '@/types/pixelmap'
import { AnthropicProvider } from '@/services/AnthropicProvider'
import { OpenAIProvider } from '@/services/OpenAIProvider'
import { OpenAICompatibleProvider } from '@/services/OpenAICompatibleProvider'
import { DeepSeekProvider } from '@/services/DeepSeekProvider'
import type { LLMProvider } from '@/services/providers'

const providers: Record<LLMProviderType, LLMProvider> = {
  anthropic: new AnthropicProvider(),
  openai: new OpenAIProvider(),
  'openai-compatible': new OpenAICompatibleProvider(),
  deepseek: new DeepSeekProvider(),
}

export async function generate(
  providerType: LLMProviderType,
  request: PixelGenRequest,
): Promise<Result<PixelMapResponse>> {
  const provider = providers[providerType]
  if (!provider) {
    return {
      ok: false,
      error: { message: `Unknown provider type: ${providerType}`, code: 'INVALID_PROVIDER' },
    }
  }
  return provider.generate(request)
}
