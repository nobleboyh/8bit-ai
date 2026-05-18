export type LLMProviderType = 'anthropic' | 'openai' | 'openai-compatible' | 'deepseek'

export interface ProviderConfig {
  type: LLMProviderType
  apiUrl: string
  model: string
  apiKey: string
}

export interface ProviderPreset {
  type: LLMProviderType
  label: string
  apiUrl: string
  model: string
}

export const PROVIDER_PRESETS: ProviderPreset[] = [
  {
    type: 'anthropic',
    label: 'Anthropic',
    apiUrl: 'https://api.anthropic.com',
    model: 'claude-sonnet-4-20250514',
  },
  {
    type: 'openai',
    label: 'OpenAI',
    apiUrl: 'https://api.openai.com',
    model: 'gpt-4o',
  },
  {
    type: 'openai-compatible',
    label: 'OpenAI-Compatible',
    apiUrl: 'https://api.together.xyz',
    model: 'meta-llama/Llama-3.3-70B-Instruct-Turbo',
  },
  {
    type: 'deepseek',
    label: 'DeepSeek',
    apiUrl: 'https://api.deepseek.com',
    model: 'deepseek-v4-flash',
  },
]
