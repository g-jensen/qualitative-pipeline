import '../../test/setup-ai-mocks.js';

import { describe, it, expect, beforeEach } from 'vitest';
import { resolveModel } from '../model-resolver.js';
import * as helpers from '../../test/helpers.js';

const AIMocks = await helpers.mockAI();

describe('resolveModel', () => {
  beforeEach(() => {
    helpers.resetAIMocks(AIMocks)
  });

  it('uses OpenAI provider for gpt-4 model', () => {
    const config = { model_id: 'gpt-4' };
    const model = resolveModel(config);

    expect(AIMocks.mockOpenaiProvider).toHaveBeenCalledWith('gpt-4');
    expect(model).toBe('mocked-openai-model');
  });

  it('uses OpenAI provider for gpt-4o model', () => {
    const config = { model_id: 'gpt-4o' };
    const model = resolveModel(config);

    expect(AIMocks.mockOpenaiProvider).toHaveBeenCalledWith('gpt-4o');
    expect(model).toBe('mocked-openai-model');
  });

  it('uses Anthropic provider for claude-3-opus model', () => {
    const config = { model_id: 'claude-3-opus-20240229' };
    const model = resolveModel(config);

    expect(AIMocks.mockClaudeProvider).toHaveBeenCalledWith('claude-3-opus-20240229');
    expect(model).toBe('mocked-anthropic-model');
  });

  it('uses Anthropic provider for claude-3-sonnet model', () => {
    const config = { model_id: 'claude-3-5-sonnet-20241022' };
    const model = resolveModel(config);

    expect(AIMocks.mockClaudeProvider).toHaveBeenCalledWith('claude-3-5-sonnet-20241022');
    expect(model).toBe('mocked-anthropic-model');
  });

  it('uses Ollama provider for llama3 model', () => {
    const config = { model_id: 'llama3' };
    const model = resolveModel(config);

    expect(AIMocks.mockOllamaProvider).toHaveBeenCalledWith('llama3');
    expect(model).toBe('mocked-ollama-model');
  });

  it('uses createOllama with baseURL when model_url is provided', () => {
    const config = { 
      model_id: 'llama3',
      model_url: 'http://localhost:11434'
    };
    const model = resolveModel(config);

    expect(AIMocks.mockCreateOllama).toHaveBeenCalledWith({
      baseURL: 'http://localhost:11434'
    });
    expect(AIMocks.mockOllamaProvider).toHaveBeenCalledWith('llama3');
    expect(model).toBe('mocked-ollama-model');
  });

  it('uses Ollama provider for unrecognized model names', () => {
    const config = { model_id: 'mistral-7b' };
    const model = resolveModel(config);

    expect(AIMocks.mockOllamaProvider).toHaveBeenCalledWith('mistral-7b');
    expect(model).toBe('mocked-ollama-model');
  });
});
