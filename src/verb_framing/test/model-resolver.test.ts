import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('@ai-sdk/openai', () => ({
  openai: vi.fn(() => 'mocked-openai-model')
}));

vi.mock('@ai-sdk/anthropic', () => ({
  anthropic: vi.fn(() => 'mocked-anthropic-model')
}));

vi.mock('ai-sdk-ollama', () => ({
  ollama: vi.fn(() => 'mocked-ollama-model'),
  createOllama: vi.fn(() => vi.fn(() => 'mocked-ollama-model'))
}));

import { resolveModel } from '../model-resolver.js';
import { openai } from '@ai-sdk/openai';
import { anthropic } from '@ai-sdk/anthropic';
import { ollama, createOllama } from 'ai-sdk-ollama';
import * as helpers from './helpers.js';

const AIMocks = {
  mockOpenaiProvider: vi.mocked(openai),
  mockAnthropicProvider: vi.mocked(anthropic),
  mockOllamaProvider: vi.mocked(ollama),
  mockCreateOllama: vi.mocked(createOllama)
}

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

    expect(AIMocks.mockAnthropicProvider).toHaveBeenCalledWith('claude-3-opus-20240229');
    expect(model).toBe('mocked-anthropic-model');
  });

  it('uses Anthropic provider for claude-3-sonnet model', () => {
    const config = { model_id: 'claude-3-5-sonnet-20241022' };
    const model = resolveModel(config);

    expect(AIMocks.mockAnthropicProvider).toHaveBeenCalledWith('claude-3-5-sonnet-20241022');
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
