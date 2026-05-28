import fs from 'fs';
import { processExtractionFile, generateXLSX } from './core.js';
import * as self from './main.js';
import { Command } from 'commander';
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { SimpleSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { verbFramingTracer } from './open_telemetry.js';
import { wrapOTEL } from '../open_telemetry/core.js';

export function createProgram() {
  const program = new Command();
  program
    .name('verb-framing')
    .description('Reframe extraction quotes to start with verbs')
    .requiredOption('-f, --file <path>', 'path to extraction JSONL file')
    .requiredOption('-m, --model <name>', 'model identifier (e.g., gpt-4, claude-3-opus, llama3)')
    .requiredOption('-o, --output <name>', 'file name to output to')
    .option('-u, --model-url [url]', 'base URL for model API (for local/custom instances)')
    .option('--otel-url [url]', 'URL to send OpenTelemetry logs', 'http://localhost:4418/v1/traces')
  return program;
}

export function parseArgs(argv: string[], options?: { exitOnError?: boolean }) {
  const program = createProgram();
  
  if (!options?.exitOnError) {
    program.exitOverride();
    try {
      program.parse(argv);
    } catch (error) {
    }
  } else {
    program.parse(argv);
  }
  
  return program.opts();
}

export async function main() {
  const args = self.parseArgs(process.argv, { exitOnError: true });
  
  const exporter = new OTLPTraceExporter({
    url: args.otelUrl!
  });

  const sdk = new NodeSDK({
    serviceName: "qualitative-pipeline",
    spanProcessor: new SimpleSpanProcessor(exporter),
  });

  sdk.start();

  const result = await wrapOTEL(verbFramingTracer(), 'verb-framing', async (span) => {
    const reframed = await processExtractionFile({
      file: args.file!,
      model_id: args.model!,
      model_url: args.modelUrl!
    });

    span.setAttributes({
      'extractions_file': args.file,
      'model': args.model,
      'model_url': args.model_url
    })

    await generateXLSX(reframed, fs.createWriteStream(args.output!))
    return reframed
  })

  await sdk.shutdown();
  return result
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await main().catch(console.error);
}
