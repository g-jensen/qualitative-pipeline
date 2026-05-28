import { openai } from '@ai-sdk/openai';
import { anthropic } from '@ai-sdk/anthropic';
import { ollama, createOllama } from 'ai-sdk-ollama';

export interface ModelConfig {
  model_id: string;
  model_url?: string;
}

export function resolveModel(config: ModelConfig) {
  if (config.model_id.startsWith('gpt')) {
    return openai(config.model_id);
  }
  
  if (config.model_id.startsWith('claude')) {
    return anthropic(config.model_id);
  }
  
  if (config.model_url) {
    return createOllama({ baseURL: config.model_url })(config.model_id);
  }
  
  return ollama(config.model_id);
}
