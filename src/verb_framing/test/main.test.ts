import '../../test/setup-ai-mocks.js';

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { vol } from 'memfs';
import { quote } from './helpers.js';
import * as sut from '../main.js';
import * as helpers from '../../test/helpers.js';
import { QuoteClass } from '../core.js';

const AIMocks = await helpers.mockAI();

describe('createProgram', () => {
  it('creates program with name verb-framing', () => {
    const program = sut.createProgram();
    
    expect(program.name()).toBe('verb-framing');
  });

  it('creates program with description', () => {
    const program = sut.createProgram();
    
    expect(program.description()).toBe('Reframe extraction quotes to start with verbs');
  });

  it('marks --file option as required', () => {
    const program = sut.createProgram();
    const fileOption = program.options.find(opt => opt.long === '--file');
    
    expect(fileOption).toBeDefined();
    expect(fileOption?.required).toBe(true);
  });

  it('marks --model option as required', () => {
    const program = sut.createProgram();
    const modelOption = program.options.find(opt => opt.long === '--model');
    
    expect(modelOption).toBeDefined();
    expect(modelOption?.required).toBe(true);
  });

  it('marks --model-url option as optional', () => {
    const program = sut.createProgram();
    const modelUrlOption = program.options.find(opt => opt.long === '--model-url');
    
    expect(modelUrlOption).toBeDefined();
    expect(modelUrlOption?.required).toBe(false);
  });
});

describe('parseArgs', () => {
  it('parses --file argument using commander', () => {
    const argv = ['node', 'main.ts', '--file', 'path/to/file.jsonl'];
    const args = sut.parseArgs(argv);
    
    expect(args.file).toBe('path/to/file.jsonl');
  });

  it('parses short flag -f using commander', () => {
    const argv = ['node', 'main.ts', '-f', 'path/to/file.jsonl'];
    const args = sut.parseArgs(argv);
    
    expect(args.file).toBe('path/to/file.jsonl');
  });

  it('parses short flag -m using commander', () => {
    const argv = ['node', 'main.ts', '-m', 'gpt-4'];
    const args = sut.parseArgs(argv);
    
    expect(args.model).toBe('gpt-4');
  });

  it('parses short flag -u using commander', () => {
    const argv = ['node', 'main.ts', '-u', 'http://localhost:11434'];
    const args = sut.parseArgs(argv);
    
    expect(args.modelUrl).toBe('http://localhost:11434');
  });

  it('returns object with only parsed fields, no undefined values', () => {
    const argv = ['node', 'main.ts', '--file', 'test.jsonl'];
    const args = sut.parseArgs(argv);
    
    expect(args).toEqual({
      file: 'test.jsonl',
      otelUrl: 'http://localhost:4418/v1/traces'
    });
    expect(args.model).toBeUndefined();
    expect(args.modelUrl).toBeUndefined();
  });
});

describe('main', () => {
  beforeEach(() => {
    helpers.resetAIMocks(AIMocks)
    
    vol.fromJSON({
      '/fixtures/sample_extractions.jsonl': helpers.SAMPLE_EXTRACTIONS_JSONL
    });
  });

  afterEach(() => {
    vol.reset();
  });

  it.skip('orchestrates parseArgs and processExtractionFile with correct argument mapping', async () => {
    const originalArgv = process.argv;
    
    process.argv = [
      'node',
      'main.ts',
      '--file',
      '/fixtures/sample_extractions.jsonl',
      '--model',
      'gpt-4',
      '--model-url',
      'https://api.openai.com/v1'
    ];
        
    helpers.resetAIMocks(AIMocks, [
      {output: ["Like"]},{text: "Bob Hope"},{text: " "},
      {output: ["Disappointment", "Annoyed"]},{text: "from the show"},{text: ""},
      {output: ["Think"]},{text: "about chicken"},{text: "at the performances"}
    ]);
    
    const quotes = [
      quote(QuoteClass.INNER_THINKING, 'I really like Bob Hope',"001"),
      quote(QuoteClass.EMOTIONAL_REACTION, 'The show was pretty disappointing',"001"),
      quote(QuoteClass.INNER_THINKING, 'I think about chicken at the performance',"002")
    ];

    const result = await sut.main();
    
    expect(result).toEqual([
      {original: quotes[0], verbs: ["Like"], keyPoint: "Bob Hope", supportingDetail: ""},
      {original: quotes[1], verbs: ["Feel disappointment", "Feel annoyed"], keyPoint: "from the show", supportingDetail: ""},
      {original: quotes[2], verbs: ["Think"], keyPoint: "about chicken", supportingDetail: ", at the performance"}
    ]);
    
    process.argv = originalArgv;
  });
});
