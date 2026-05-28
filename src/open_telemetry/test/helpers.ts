import { InMemorySpanExporter, ReadableSpan, SimpleSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { expect } from 'vitest';

let globalExporter: InMemorySpanExporter | null = null;
let globalProvider: NodeTracerProvider | null = null;

export function memorySDK() {
  if (!globalExporter) {
    globalExporter = new InMemorySpanExporter();
    const processor = new SimpleSpanProcessor(globalExporter);
    globalProvider = new NodeTracerProvider({
      spanProcessors: [processor]
    });
    globalProvider.register();
  }
  
  globalExporter.reset();
    
  return { exporter: globalExporter };
}

export function expectSpansContainName(spans: ReadableSpan[], expectedName: string) {
  expect(spans.map(s => s.name)).contains(expectedName)
}

export function spanByName(spans: ReadableSpan[], name: string) {
  for (const [i, span] of spans.entries()) {
    if (span.name == name) return spans[i]
  }
}