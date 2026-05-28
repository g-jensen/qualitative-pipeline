import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { MockedFunction } from 'vitest';

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

export const DEFAULT_DOCUMENT_ID = "001"

export function quote(class_: any, text: any, documentId?: string) {
  documentId = documentId || DEFAULT_DOCUMENT_ID
  return {class: class_, text: text, documentId: documentId};
}