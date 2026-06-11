import { vi } from 'vitest';

vi.resetModules();

vi.doMock('ai', async () => {
  const actual = await vi.importActual('ai');
  return {
    ...actual,
    generateText: vi.fn(),
    Output: {object: vi.fn()}
  };
});

vi.doMock('@ai-sdk/openai', () => ({
  openai: vi.fn(() => 'mocked-openai-model')
}));

vi.doMock('@ai-sdk/anthropic', () => ({
  anthropic: vi.fn(() => 'mocked-anthropic-model')
}));

vi.doMock('ai-sdk-ollama', () => ({
  ollama: vi.fn(() => 'mocked-ollama-model'),
  createOllama: vi.fn(() => vi.fn(() => 'mocked-ollama-model'))
}));

vi.doMock('fs/promises', async () => {
  const { fs } = await import('memfs');
  return fs.promises;
});