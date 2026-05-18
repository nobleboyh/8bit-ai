import type { PixelGenRequest, PixelMapResponse, Result } from '@/types/pixelmap'

export interface LLMProvider {
  generate(request: PixelGenRequest): Promise<Result<PixelMapResponse>>
}
