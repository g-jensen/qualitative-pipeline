import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { MockedFunction, vi } from 'vitest';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export const SAMPLE_EXTRACTIONS_JSONL = readFileSync(
  join(__dirname, 'fixtures', 'sample_extractions.jsonl'),
  'utf-8'
);

export const MALFORMED_EXTRACTIONS_JSONL = readFileSync(
  join(__dirname, 'fixtures', 'malformed_extraction.jsonl'),
  'utf-8'
);

export interface AIMocks {
  mockGenerateText?: MockedFunction<any>,
  mockOpenaiProvider?: MockedFunction<any>,
  mockAnthropicProvider?: MockedFunction<any>,
  mockOllamaProvider?: MockedFunction<any>,
  mockCreateOllama?: MockedFunction<any>,
  mockOuptutObject?: MockedFunction<any>
}

function returnOutputsFn(generatedOutputs: any[]) {
  let i = 0
  return (..._args: any) => {
    if (i < generatedOutputs.length) {
      return generatedOutputs[i++]
    }
    return undefined
  }
}

export function resetAIMocks(AIMocks: AIMocks, generatedOutputs?: any[]) {
  AIMocks.mockGenerateText?.mockReset();
  AIMocks.mockOpenaiProvider?.mockReset();
  AIMocks.mockAnthropicProvider?.mockReset();
  AIMocks.mockOllamaProvider?.mockReset();
  AIMocks.mockCreateOllama?.mockReset();
  AIMocks.mockOuptutObject?.mockReset();
  AIMocks.mockOpenaiProvider?.mockReturnValue('mocked-openai-model');
  AIMocks.mockAnthropicProvider?.mockReturnValue('mocked-anthropic-model');
  AIMocks.mockOllamaProvider?.mockReturnValue('mocked-ollama-model');
  AIMocks.mockCreateOllama?.mockReturnValue(AIMocks.mockOllamaProvider);
  if (generatedOutputs) {
    AIMocks.mockGenerateText.mockImplementation(returnOutputsFn(generatedOutputs));
  }
}

export async function mockAI() {
  const { generateText, Output } = await import('ai');
  const { openai } = await import('@ai-sdk/openai');
  const { anthropic } = await import('@ai-sdk/anthropic');
  const { ollama, createOllama } = await import('ai-sdk-ollama');

  return {
    mockGenerateText: vi.mocked(generateText),
    mockOpenaiProvider: vi.mocked(openai),
    mockClaudeProvider: vi.mocked(anthropic),
    mockOllamaProvider: vi.mocked(ollama),
    mockCreateOllama: vi.mocked(createOllama),
    mockOutputObject: vi.mocked(Output.object)
  }
}