import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { vol } from 'memfs';
import { z } from 'zod';
import * as otel_helpers from '../../open_telemetry/test/helpers.js'

vi.mock('ai', async () => {
  const actual = await vi.importActual('ai');
  return {
    ...actual,
    generateText: vi.fn(),
    Output: {object: vi.fn()}
  };
});

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

vi.mock('fs/promises', async () => {
  const { fs } = await import('memfs');
  return fs.promises;
});

import * as sut from '../core.js';
import { generateText, Output } from 'ai';
import { openai } from '@ai-sdk/openai';
import { anthropic } from '@ai-sdk/anthropic';
import { ollama, createOllama } from 'ai-sdk-ollama';
import * as helpers from './helpers.js';
import { DEFAULT_DOCUMENT_ID, quote } from './helpers.js';
import { ModelConfig, resolveModel } from '../model-resolver.js';
import Stream, { PassThrough } from 'stream';
import ExcelJS from 'exceljs';

const AIMocks = {
  mockGenerateText: vi.mocked(generateText),
  mockOpenaiProvider: vi.mocked(openai),
  mockClaudeProvider: vi.mocked(anthropic),
  mockOllamaProvider: vi.mocked(ollama),
  mockCreateOllama: vi.mocked(createOllama),
  mockOutputObject: vi.mocked(Output.object)
}

function create_config(model_id: any, model_url?: any) {
  return {model_id: model_id, model_url: model_url}
}

const LOCAL_CONFIG = create_config('gemma3:12b','http://localhost:11434')

function expectSchemasEqual(s1: any, s2: any) {
  expect(s1.toJSONSchema()).toEqual(s2.toJSONSchema())
}

function keyPointSystem(quote: string): string {
  return `Our goal is to summarize this quote: \"${quote}\" so that it is more memorable.
You are given the beginning of a sentence fragment (a verb phrase) relating to the quote.
Your task is to naturally continue the sentence fragment by adding a key point from the quote as if you were completing the fragment.
You might not include the entire sentence: do not include supporting details, these will be added in a later step.
Examples:
{
  quote: Unfortunately they were serving suffed peppers. I hate stuffed papers.
  initial verb phrase: Feel disappointed
  your response: Feel disappointed that they serve stuffed peppers at the dinner
},
{
  quote: over time I learned to say I am allergic to it. People respect allergies.
  initial verb phrase: Tell
  your response: Tell people that I am allergic to pepper
},
{
  quote: I put another small bite of pepper in my mouth and began to chew the acrid, unpleasant thing.
  initial verb phrase: Feel disgusted
  your response: Feel disgusted by the acrid taste of stuffed pepper
}
Stay true to the original quote and make sure to preserve its specific phrasing.
Preserve specificity: avoid non-specific nouns like "thing" or "they"
NEVER include thought process after giving me the full fragment.
Here is the real quote again for reference: \"${quote}\"`
}

function keyPointPrompt(verb: string) {
  return `Beginning sentence fragment: \"${verb}\"`
}

function keyPointResponseBeginning(verb: string) {
  return `Here's the fragment + key point combined into one natural phrase without fluff: ${verb} `
}

function supportingDetailSystem(quote: string) {
  return `Our goal is to extract the important parts of a quote so that it can be quickly interpreted by a researcher.
You are given the beginning of a sentence fragment with some information about from quote.
Your task is to add missing details directly mentioned in the quote to the fragment.
Do NOT repeat information.
NEVER make up or infer details.
You might not add anything at all. Only add something if the given sentence fragment is missing details from the quote.
Examples:
{
  quote: Unfortunately they were serving suffed peppers. I hate stuffed papers.

  initial fragment: Feel disappointed that they serve stuffed peppers
  your response: Feel disappointed that they serve stuffed peppers, since I hate them
},
{
  quote: Mom checking on my progress and telling me to keep going until it was half gone, even though I felt desperate to quit.

  initial fragment: Feel desperate to quot eating the stuffed pepper
  your response: Feel desperate to quot eating the stuffed pepper because Mom says I have to eat half of it, and keeps tabs
},
{
  quote: So, I knew, right, we kind of follow what performances they put on. So I think I probably either got an email or I
  initial fragment: Follow what performances this theater puts on
  your response: Follow what performances this theater puts on via email
},
{
  quote: I figured out when I saw a friend mentioning an allergy at a restaurant, and I decided to copy them

  initial fragment: Figure out that people pay attention to allergies when I saw a friend do it
  your response: Figure out that people pay attention to allergies when I saw a friend do it
},
{
  quote: I put another small bite of pepper into my mouth and began to chew the acrid, unpleasant thing.

  initial fragment: Feel disgusted by the acrid taste of stuffed pepper
  your response: Feel disgusted by the acrid taste of stuffed pepper
}
Your full response should only be the full fragment. Never include comments after the fragment.
Here is the real quote again for reference: "${quote}"`
}

function supportingDetailPrompt(verb: string, keyPoint: string) {
  const fragment = `${verb} ${keyPoint}`;
  return `\"${fragment}\"`
}

function supportingDetailResponseBeginning(verb: string, keyPoint: string) {
  return `Here's the complete fragment with no inferred details rephrased for easy interpretation by a researcher: ${verb} ${keyPoint}`
}

function expectGeneratedVerbPhrase(mocks: helpers.AIMocks, quote_: sut.Quote, config: ModelConfig): void {
  expect(mocks.mockGenerateText).toHaveBeenCalledWith({
    model: resolveModel(config),
    system: sut.verbPhrasePrompt(quote_.class),
    prompt: quote_.text,
  })
  // figure out how to test this
  // expect(AIMocks.mockOutputObject).toHaveBeenCalledWith({
  //   schema: sut.verbPhraseSchema(sut.QuoteClass.INNER_THINKING)
  // })
}

function expectGeneratedKeyPoint(mocks: helpers.AIMocks, quote_: sut.Quote, verb: string, config: ModelConfig): void {
  expect(mocks.mockGenerateText).toHaveBeenCalledWith({
    model: resolveModel(config),
    system: keyPointSystem(quote_.text),
    messages: [
      { role: 'user', content: keyPointPrompt(verb) },
      { role: 'assistant', content: keyPointResponseBeginning(verb) },
    ]
  })
}

function expectGeneratedSupportingDetail(mocks: helpers.AIMocks, quote_: sut.Quote, verb: string, keyPoint: string, config: ModelConfig): void {
  expect(mocks.mockGenerateText).toHaveBeenCalledWith({
    model: resolveModel(config),
    system: supportingDetailSystem(quote_.text),
    messages: [
      { role: 'user', content: supportingDetailPrompt(verb,keyPoint) },
      { role: 'assistant', content: supportingDetailResponseBeginning(verb,keyPoint) },
    ]
  })
}

function expectGeneratedPhrase(mocks: helpers.AIMocks, quote_: sut.Quote, verb: string, keyPoint: string, config: ModelConfig): void {
  expectGeneratedVerbPhrase(mocks,quote_,config)
  expectGeneratedKeyPoint(mocks,quote_,verb,config)
  expectGeneratedSupportingDetail(mocks,quote_,verb,keyPoint,config)
}

function document(quotes: any,id: any) {
  return {
    quotes: quotes,
    id: id
  }
}

const VERB_PHRASE_PROMPT = 'Give me 2-5 possible verbs that describe what the person who said is doing/did do. These could be verbs explicitly mentioned in the quote or implied actions. Each candidate MUST be exactly one verb in the present tense. You should convert verb in the text to present tense. These can be very abstract actions, but try to keep things simple. The verb should make sense in the sentence \"I <verb>\". Respond only with the verb. Do not include thought process.'
const EMOTIONAL_VERB_PHRASE_PROMPT = 'Give me 2-5 possible emotions that the person who said this quote is feeling. These could be emotions explicitly mentioned in the quote or implied emotions. The emotion should be a single word and make sense in the sentence \"I feel <emotion>\". Respond only with the emotion. Do not include thought process.'

describe('verbPhrasePrompt', () => {
  it('returns a prompt about inner thinking', () => {
    const prompt = sut.verbPhrasePrompt(sut.QuoteClass.INNER_THINKING)
    expect(prompt).toBe(VERB_PHRASE_PROMPT)
  })

  it('returns a prompt about personal rules', () => {
    const prompt = sut.verbPhrasePrompt(sut.QuoteClass.PERSONAL_RULE)
    expect(prompt).toBe(VERB_PHRASE_PROMPT)
  })

  it('returns a prompt about emotional reactions', () => {
    const prompt = sut.verbPhrasePrompt(sut.QuoteClass.EMOTIONAL_REACTION)
    expect(prompt).toBe(EMOTIONAL_VERB_PHRASE_PROMPT)
  })

})

const VERB_PHRASE_SCHEMA = z.array(z.string().describe('present tense verb (one word)')).min(2).max(5)
const EMOTIONAL_VERB_PHRASE_SCHEMA = z.array(z.string().describe('emotion (one word)')).min(2).max(5)

describe('verbPhraseSchema', () => {
  it('returns a schema for inner thinking verbs', () => {
    const schema = sut.verbPhraseSchema(sut.QuoteClass.INNER_THINKING)
    expectSchemasEqual(schema,VERB_PHRASE_SCHEMA)
  })

  it('returns a schema for personal rule verbs', () => {
    const schema = sut.verbPhraseSchema(sut.QuoteClass.PERSONAL_RULE)
    expectSchemasEqual(schema,VERB_PHRASE_SCHEMA)
  })

  it('returns a schema for emotional reactions', () => {
    const schema = sut.verbPhraseSchema(sut.QuoteClass.EMOTIONAL_REACTION)
    expectSchemasEqual(schema,EMOTIONAL_VERB_PHRASE_SCHEMA)
  })
})

describe('generateVerbPhrase', () => {
  it('returns AI output', async () => {
    helpers.resetAIMocks(AIMocks, [{output: ["Eat", "Consume"]}]);
    const verbs = await sut.generateVerbPhrase(
      quote(sut.QuoteClass.INNER_THINKING,"I ate a burger"),
      LOCAL_CONFIG
    )
    expect(verbs).toEqual(["Eat", "Consume"])
  })

  it('capitalizes first character of non-emotional outputs', async () => {
    helpers.resetAIMocks(AIMocks, [{output: ["eat", "consume"]}]);
    const verbs = await sut.generateVerbPhrase(
      quote(sut.QuoteClass.INNER_THINKING,"I ate a burger"),
      LOCAL_CONFIG
    )
    expect(verbs).toEqual(["Eat", "Consume"])
  })

  it('prefixes and lowers of emotional outputs', async () => {
    helpers.resetAIMocks(AIMocks, [{output: ["Hate", "Disgust"]}]);
    const verbs = await sut.generateVerbPhrase(
      quote(sut.QuoteClass.EMOTIONAL_REACTION,"I hated the disgusting burger"),
      LOCAL_CONFIG
    )
    expect(verbs).toEqual(["Feel hate", "Feel disgust"])
  })

  it('trims output', async () => {
    helpers.resetAIMocks(AIMocks, [{output: ["  Eat ", " Consume  "]}]);
    const verbs = await sut.generateVerbPhrase(
      quote(sut.QuoteClass.INNER_THINKING,"I ate the burger"),
      LOCAL_CONFIG
    )
    expect(verbs).toEqual(["Eat", "Consume"])

    helpers.resetAIMocks(AIMocks, [{output: [" Hate  ", "  Disgust "]}]);
    const emotional_verbs = await sut.generateVerbPhrase(
      quote(sut.QuoteClass.EMOTIONAL_REACTION,"I hated the disgusting burger"),
      LOCAL_CONFIG
    )
    expect(emotional_verbs).toEqual(["Feel hate", "Feel disgust"])
  })

  it('generates according to schema', async () => {
    helpers.resetAIMocks(AIMocks, [{output: ["Eat", "Consume"]}]);
    const thinking_verbs = await sut.generateVerbPhrase(
      quote(sut.QuoteClass.INNER_THINKING,"I ate a burger"),
      LOCAL_CONFIG
    )
    expect(VERB_PHRASE_SCHEMA.safeParse(thinking_verbs).success).true
  
    helpers.resetAIMocks(AIMocks, [{output: ["Eat", "Consume"]}]);
    const personal_verbs = await sut.generateVerbPhrase(
      quote(sut.QuoteClass.PERSONAL_RULE,"I ate a burger"),
      LOCAL_CONFIG
    )
    expect(VERB_PHRASE_SCHEMA.safeParse(personal_verbs).success).true

    helpers.resetAIMocks(AIMocks, [{output: ["hate", "disgust"]}]);
    const emotional_verbs = await sut.generateVerbPhrase(
      quote(sut.QuoteClass.EMOTIONAL_REACTION,"I hated the disgusting burger"),
      LOCAL_CONFIG
    )
    expect(EMOTIONAL_VERB_PHRASE_SCHEMA.safeParse(emotional_verbs).success).true
  })

  it('generates with params', async () => {
    {
      helpers.resetAIMocks(AIMocks, [{output: ["Eat", "Consume"]}]);
      const config = LOCAL_CONFIG
      const quote_ = quote(sut.QuoteClass.INNER_THINKING,"I ate a burger")
      await sut.generateVerbPhrase(quote_,config)
      expectGeneratedVerbPhrase(AIMocks, quote_, config)
    }
    {
      helpers.resetAIMocks(AIMocks, [{output: ["hate", "disgust"]}]);
      const config = create_config('claude-haiku-4-5')
      const quote_ = quote(sut.QuoteClass.EMOTIONAL_REACTION,"I hated the disgusting burger")
      await sut.generateVerbPhrase(quote_,config)
      expectGeneratedVerbPhrase(AIMocks, quote_, config)
    }
  })

  it('OTEL', async () => {
    const { exporter } = otel_helpers.memorySDK()
    
    helpers.resetAIMocks(AIMocks, [{
      output: ["Eat", "Consume"],
      usage: {
        inputTokens: 200,
        outputTokens: 100,
        totalTokens: 350
      }
    }]);
    await sut.generateVerbPhrase(
      quote(sut.QuoteClass.INNER_THINKING,"I ate a burger"),
      LOCAL_CONFIG
    )
    
    const spans = exporter.getFinishedSpans()
    otel_helpers.expectSpansContainName(spans,sut.generateVerbPhrase.name)
    const span = otel_helpers.spanByName(spans,sut.generateVerbPhrase.name)
    expect(span?.attributes).toEqual({
      'input_tokens': 200,
      'output_tokens': 100,
      'total_tokens': 350
    })
  })
})

describe('generateKeyPoint', () => {
  it('returns AI output', async () => {
    helpers.resetAIMocks(AIMocks, [{text: 'a burger'}]);
    const verbs = await sut.generateKeyPoint(
      "Eat",
      quote(sut.QuoteClass.INNER_THINKING,"I ate a burger"),
      LOCAL_CONFIG
    )
    expect(verbs).toEqual('a burger')
  })

  it('trims verb if output starts with verb', async () => {
    helpers.resetAIMocks(AIMocks, [{text: 'Eat a burger'}]);
    const verbs = await sut.generateKeyPoint(
      "Eat",
      quote(sut.QuoteClass.INNER_THINKING,"I ate a burger"),
      LOCAL_CONFIG
    )
    expect(verbs).toEqual('a burger')
  })

  it('trims output', async () => {
    helpers.resetAIMocks(AIMocks, [{text: '  a burger  '}]);
    const verbs = await sut.generateKeyPoint(
      "Eat",
      quote(sut.QuoteClass.INNER_THINKING,"I ate a burger"),
      LOCAL_CONFIG
    )
    expect(verbs).toEqual('a burger')
  })

  it('removes trailing punctuation', async () => {
    helpers.resetAIMocks(AIMocks, [{text: 'a, burger.!?,;:'}]);
    const verbs = await sut.generateKeyPoint(
      "Eat",
      quote(sut.QuoteClass.INNER_THINKING,"I ate a burger"),
      LOCAL_CONFIG
    )
    expect(verbs).toEqual('a, burger')
  })

  it('empty if only punctuation', async () => {
    helpers.resetAIMocks(AIMocks, [{text: '.!?,;:'}]);
    const verbs = await sut.generateKeyPoint(
      "Eat",
      quote(sut.QuoteClass.INNER_THINKING,"I ate a burger"),
      LOCAL_CONFIG
    )
    expect(verbs).toEqual('')
  })

  it('generates with params', async () => {
    helpers.resetAIMocks(AIMocks, [{text: "a burger"}]);
    const config = LOCAL_CONFIG
    const quote_ = quote(sut.QuoteClass.INNER_THINKING,"I ate a burger")
    const verb = "Eat"
    await sut.generateKeyPoint(verb,quote_,config)
    expectGeneratedKeyPoint(AIMocks,quote_,verb,config)
  })

  it('OTEL', async () => {
    const { exporter } = otel_helpers.memorySDK()
    
    helpers.resetAIMocks(AIMocks, [{
      text: 'a burger',
      usage: {
        inputTokens: 123,
        outputTokens: 456,
        totalTokens: 789
      }
    }]);
    await sut.generateKeyPoint(
      "Eat",
      quote(sut.QuoteClass.INNER_THINKING,"I ate a burger"),
      LOCAL_CONFIG
    )
    
    const spans = exporter.getFinishedSpans()
    otel_helpers.expectSpansContainName(spans,sut.generateKeyPoint.name)
    const span = otel_helpers.spanByName(spans,sut.generateKeyPoint.name)
    expect(span?.attributes).toEqual({
      'verb': 'Eat',
      'input_tokens': 123,
      'output_tokens': 456,
      'total_tokens': 789
    })
  })
})

describe('generateSupportingDetail', async () => {
  it('returns AI output', async () => {
    helpers.resetAIMocks(AIMocks, [{text: ', in the woods'}]);
    const supportingDetail = await sut.generateSupportingDetail(
      "Eat",
      "a burger",
      quote(sut.QuoteClass.INNER_THINKING,"I ate a burger in the woods"),
      LOCAL_CONFIG
    )
    expect(supportingDetail).toEqual(', in the woods')
  })

  it('trims output', async () => {
    helpers.resetAIMocks(AIMocks, [{text: ': in the woods  '}]);
    const supportingDetail = await sut.generateSupportingDetail(
      "Eat",
      "a burger",
      quote(sut.QuoteClass.INNER_THINKING,"I ate a burger in the woods"),
      LOCAL_CONFIG
    )
    expect(supportingDetail).toEqual(': in the woods')
  })

  it('removes trailing punctuation', async () => {

    helpers.resetAIMocks(AIMocks, [{text: ', in the woods.!?,;:'}]);
    const supportingDetail = await sut.generateSupportingDetail(
      "Eat",
      "a burger",
      quote(sut.QuoteClass.INNER_THINKING,"I ate a burger in the woods"),
      LOCAL_CONFIG
    )
    expect(supportingDetail).toEqual(', in the woods')
  })

  it('empty if only punctuation', async () => {
    helpers.resetAIMocks(AIMocks, [{text: '.!?,;:'}]);
    const supportingDetail = await sut.generateSupportingDetail(
      "Eat",
      "a burger",
      quote(sut.QuoteClass.INNER_THINKING,"I ate a burger"),
      LOCAL_CONFIG
    )
    expect(supportingDetail).toEqual('')
  })

  it('adds space if first character is not punctuation', async () => {
    helpers.resetAIMocks(AIMocks, [{text: 'at the highschool'}]);
    const supportingDetail = await sut.generateSupportingDetail(
      "Eat",
      "a burger",
      quote(sut.QuoteClass.INNER_THINKING,"I ate a burger at the highschool"),
      LOCAL_CONFIG
    )
    expect(supportingDetail).toEqual(' at the highschool')
  })

  it('generates with params', async () => {
    helpers.resetAIMocks(AIMocks, [{text: "with salad"}]);
    const config = LOCAL_CONFIG
    const quote_ = quote(sut.QuoteClass.INNER_THINKING,"I ate a burger with salad")
    const verb = "Eat"
    const keyPoint = "a burger"
    await sut.generateSupportingDetail(verb,keyPoint,quote_,config)
    expectGeneratedSupportingDetail(AIMocks,quote_,verb,keyPoint,config)
  })

  it('OTEL', async () => {
    const { exporter } = otel_helpers.memorySDK()
    
    helpers.resetAIMocks(AIMocks, [{
      text: ', in the woods',
      usage: {
        inputTokens: 987,
        outputTokens: 654,
        totalTokens: 321
      }
    }]);
    await sut.generateSupportingDetail(
      "Eat",
      "a burger",
      quote(sut.QuoteClass.INNER_THINKING,"I ate a burger in the woods"),
      LOCAL_CONFIG
    )
    
    const spans = exporter.getFinishedSpans()
    otel_helpers.expectSpansContainName(spans,sut.generateSupportingDetail.name)
    const span = otel_helpers.spanByName(spans,sut.generateSupportingDetail.name)
    expect(span?.attributes).toEqual({
      'verb': 'Eat',
      'key_point': 'a burger',
      'input_tokens': 987,
      'output_tokens': 654,
      'total_tokens': 321
    })
  })
})

describe('reframeQuote', () => {
  it('returns result of LLM calls', async () => {
    helpers.resetAIMocks(AIMocks, [
      {output: ["Eat", "Consume"]},
      {text: "a burger"},
      {text: " in the morning"}
    ]);
    const quote_ = quote(sut.QuoteClass.INNER_THINKING, 'I ate a burger in the morning');
    const config = LOCAL_CONFIG;
    const reframedParts = await sut.reframeQuote(quote_,config);
    expect(reframedParts).toEqual({
      original: quote_,
      verbs: ["Eat", "Consume"], 
      keyPoint: "a burger", 
      supportingDetail: " in the morning"
    })
  });

  it('does not include supportingDetail if blank', async () => {
    helpers.resetAIMocks(AIMocks, [
      {output: ["Eat", "Consume"]},
      {text: "a burger"},
      {text: " "}
    ]);
    const quote_ = quote(sut.QuoteClass.INNER_THINKING, 'I ate a burger');
    const config = LOCAL_CONFIG;
    const reframedParts = await sut.reframeQuote(quote_,config);
    expect(reframedParts).toEqual({
      original: quote_,
      verbs: ["Eat", "Consume"], 
      keyPoint: "a burger", 
      supportingDetail: ""
    })
  });

  it('calls LLM with params', async () => {
    helpers.resetAIMocks(AIMocks, [
      {output: ["Eat"]},
      {text: "a burger"},
      {text: " in the morning"}
    ]);
    const quote_ = quote(sut.QuoteClass.INNER_THINKING, 'I ate a burger in the morning');
    const config = LOCAL_CONFIG;
    await sut.reframeQuote(quote_,config);
    expectGeneratedVerbPhrase(AIMocks,quote_,config)
    expectGeneratedKeyPoint(AIMocks,quote_,"Eat",config)
    expectGeneratedSupportingDetail(AIMocks,quote_,"Eat","a burger",config)
  });

  it('always uses first verb in params', async () => {
    helpers.resetAIMocks(AIMocks, [
      {output: ["Eat", "Consume"]},
      {text: "a burger"},
      {text: " in the morning"}
    ]);
    const quote_ = quote(sut.QuoteClass.INNER_THINKING, 'I ate a burger in the morning');
    const config = LOCAL_CONFIG;
    await sut.reframeQuote(quote_,config);
    expectGeneratedPhrase(AIMocks,quote_,"Eat","a burger",config)
  });

  it('OTEL', async () => {
    const { exporter } = otel_helpers.memorySDK()
    
    helpers.resetAIMocks(AIMocks, [
      {output: ["Eat", "Consume"]},
      {text: "a burger"},
      {text: " in the morning"}
    ]);
    const quote_ = quote(sut.QuoteClass.INNER_THINKING, 'I ate a burger in the morning');
    const config = LOCAL_CONFIG;
    await sut.reframeQuote(quote_,config);
    
    const spans = exporter.getFinishedSpans()
    otel_helpers.expectSpansContainName(spans,sut.reframeQuote.name)
    const span = otel_helpers.spanByName(spans,sut.reframeQuote.name)
    expect(span?.attributes).toEqual(quote_)
  })
});

describe('extractionToQuote', () => {
  it('returns undefined with empty object', () => {
    expect(sut.extractionToQuote({},DEFAULT_DOCUMENT_ID)).toBe(undefined)
  })

  it('returns undefined with only text', () => {
    const input = {extraction_text: "some text"}
    expect(sut.extractionToQuote(input,DEFAULT_DOCUMENT_ID)).toBe(undefined)
  })

  it('returns undefined with only class', () => {
    const input = {extraction_class: "emotional response"}
    expect(sut.extractionToQuote(input,DEFAULT_DOCUMENT_ID)).toBe(undefined)
  })

  it('parses unknown class', () => {
    const input = {
      extraction_class: "unknown class",
      extraction_text: "more text"
    }
    expect(sut.extractionToQuote(input,DEFAULT_DOCUMENT_ID)).toEqual(undefined)
  })

  it('parses inner thinking', () => {
    const input = {
      extraction_class: "inner thinking",
      extraction_text: "some text"
    }
    const expected_quote = quote(sut.QuoteClass.INNER_THINKING, "some text")
    expect(sut.extractionToQuote(input,DEFAULT_DOCUMENT_ID)).toEqual(expected_quote)
  })

  it('parses emotional reaction', () => {
    const input = {
      extraction_class: "emotional reaction",
      extraction_text: "other text"
    }
    const expected_quote = quote(sut.QuoteClass.EMOTIONAL_REACTION, "other text")
    expect(sut.extractionToQuote(input,DEFAULT_DOCUMENT_ID)).toEqual(expected_quote)
  })

  it('parses personal rule', () => {
    const input = {
      extraction_class: "personal rule",
      extraction_text: "more text"
    }
    const expected_quote = quote(sut.QuoteClass.PERSONAL_RULE, "more text")
    expect(sut.extractionToQuote(input,DEFAULT_DOCUMENT_ID)).toEqual(expected_quote)
  })

  it('parses document_id', () => {
    const input = {
      extraction_class: "personal rule",
      extraction_text: "more text"
    }
    const expected_quote = quote(sut.QuoteClass.PERSONAL_RULE, "more text","002")
    expect(sut.extractionToQuote(input,"002")).toEqual(expected_quote)
  })

})

describe('parseExtractionFile', () => {
  beforeEach(() => {
    vol.fromJSON({
      '/fixtures/sample_extractions.jsonl': helpers.SAMPLE_EXTRACTIONS_JSONL,
      '/fixtures/malformed_extraction.jsonl': helpers.MALFORMED_EXTRACTIONS_JSONL
    });
  });

  afterEach(() => {
    vol.reset();
  });

  it('returns an array of extraction texts from a JSONL file', async () => {
    const filePath = '/fixtures/sample_extractions.jsonl';
    const texts = await sut.parseExtractionFile(filePath);
    
    expect(Array.isArray(texts)).toBe(true);
    expect(texts).toEqual([
      document([
        quote(sut.QuoteClass.INNER_THINKING, 'I really like Bob Hope',"001"),
        quote(sut.QuoteClass.EMOTIONAL_REACTION, 'The show was pretty disappointing',"001"),
      ],"001"),
      document([
        quote(sut.QuoteClass.INNER_THINKING, 'I think about chicken',"002")
      ], "002")
    ]);
  });

  it('skips malformed extractions', async () => {
    const filePath = '/fixtures/malformed_extraction.jsonl';
    const quotes = await sut.parseExtractionFile(filePath);
    
    expect(quotes).toEqual([
      document([
        quote(sut.QuoteClass.INNER_THINKING, 'I really like Bob Hope',"003"),
        quote(sut.QuoteClass.EMOTIONAL_REACTION, 'The show was pretty disappointing',"003"),
      ],"003"),
    ]);
  });

  it('OTEL', async () => {
    const { exporter } = otel_helpers.memorySDK()
    
    const filePath = '/fixtures/malformed_extraction.jsonl';
    await sut.parseExtractionFile(filePath);
    
    otel_helpers.expectSpansContainName(
      exporter.getFinishedSpans(),
      sut.parseExtractionFile.name
    )
    
  })
});

describe('batchReframeQuotes', () => {
  beforeEach(() => {
    helpers.resetAIMocks(AIMocks)
  });

  it('processes multiple quotes and returns reframed versions in order', async () => {
    const quotes = [
      quote(sut.QuoteClass.EMOTIONAL_REACTION, 'I am feeling nervous about the presentation'),
      quote(sut.QuoteClass.EMOTIONAL_REACTION, 'I enjoy hiking on the weekends'),
      quote(sut.QuoteClass.INNER_THINKING, 'I think the weather is nice today')
    ];
    
    helpers.resetAIMocks(AIMocks, [
      {output: ["Nervous"]},            {output: ["Enjoyment"]},    {output: ["Think"]},
      {text: "about the presentation"}, {text: "from hiking"},      {text: "that the weather is nice today"},
      {text: " "},                      {text: " on the weekends"}, {text: " "}
    ]);

    const config = create_config('gpt-4o-mini','https://api.openai.com/v1');
    
    const reframed = await sut.batchReframeQuotes(quotes, config);
    expect(reframed).toEqual([
      {original: quotes[0], verbs: ["Feel nervous"], keyPoint: "about the presentation", supportingDetail: ""},
      {original: quotes[1], verbs: ["Feel enjoyment"], keyPoint: "from hiking", supportingDetail: " on the weekends"},
      {original: quotes[2], verbs: ["Think"], keyPoint: "that the weather is nice today", supportingDetail: ""}
    ]);
    expectGeneratedPhrase(AIMocks,quotes[0],"Feel nervous","about the presentation",config)
    expectGeneratedPhrase(AIMocks,quotes[1],"Feel enjoyment","from hiking",config)
    expectGeneratedPhrase(AIMocks,quotes[2],"Think","that the weather is nice today",config)
  });

  it('OTEL', async () => {
    const { exporter } = otel_helpers.memorySDK()
    
    const quotes = [
      quote(sut.QuoteClass.EMOTIONAL_REACTION, 'I am feeling nervous about the presentation'),
      quote(sut.QuoteClass.EMOTIONAL_REACTION, 'I enjoy hiking on the weekends'),
      quote(sut.QuoteClass.INNER_THINKING, 'I think the weather is nice today')
    ];
    
    helpers.resetAIMocks(AIMocks, [
      {output: ["Nervous"]},            {output: ["Enjoyment"]},    {output: ["Think"]},
      {text: "about the presentation"}, {text: "from hiking"},      {text: "that the weather is nice today"},
      {text: " "},                      {text: " on the weekends"}, {text: " "}
    ]);

    const config = create_config('gpt-4o-mini','https://api.openai.com/v1');
    await sut.batchReframeQuotes(quotes, config);
    
    otel_helpers.expectSpansContainName(
      exporter.getFinishedSpans(),
      sut.batchReframeQuotes.name
    )
  })
});

describe('processExtractionFile', () => {
  beforeEach(() => {
    vol.fromJSON({
      '/fixtures/sample_extractions.jsonl': helpers.SAMPLE_EXTRACTIONS_JSONL
    });
  });

  afterEach(() => {
    vol.reset();
  });

  it('orchestrates parsing and reframing with provided CLI args', async () => {    
    const quotes = [
      quote(sut.QuoteClass.INNER_THINKING, 'I really like Bob Hope'),
      quote(sut.QuoteClass.EMOTIONAL_REACTION, 'The show was pretty disappointing'),
      quote(sut.QuoteClass.INNER_THINKING, 'I think about chicken',"002")
    ];

    helpers.resetAIMocks(AIMocks, [
      {output: ["Like"]},  {output: ["Disappointment"]}, {output: ["Think"]},
      {text: "Bob Hope"},   {text: "from the show"},      {text: "about chicken"},
      {text: " "},         {text: ""},                   {text: " "}
    ]);

    const config = {
      model_id: 'gpt-4',
      model_url: 'https://api.openai.com/v1'
    }
    const result = await sut.processExtractionFile({
      file: '/fixtures/sample_extractions.jsonl',
      model_id: config.model_id,
      model_url: config.model_url
    });
    
    expect(result).toEqual([
      {original: quotes[0], verbs: ["Like"], keyPoint: "Bob Hope", supportingDetail: ""},
      {original: quotes[1], verbs: ["Feel disappointment"], keyPoint: "from the show", supportingDetail: ""},
      {original: quotes[2], verbs: ["Think"], keyPoint: "about chicken", supportingDetail: ""}
    ]);

    expectGeneratedPhrase(AIMocks,quotes[0],"Like","Bob Hope",config)
    expectGeneratedPhrase(AIMocks,quotes[1],"Feel disappointment","from the show",config)
    expectGeneratedPhrase(AIMocks,quotes[2],"Think","about chicken",config)
  });

  it('OTEL', async () => {
    const { exporter } = otel_helpers.memorySDK()
    
    helpers.resetAIMocks(AIMocks, [
      {output: ["Like"]},  {output: ["Disappointment"]}, {output: ["Think"]},
      {text: "Bob Hope"},  {text: "from the show"},      {text: "about chicken"},
      {text: " "},         {text: ""},                   {text: " "}
    ]);

    const config = {
      model_id: 'gpt-4',
      model_url: 'https://api.openai.com/v1'
    }
    await sut.processExtractionFile({
      file: '/fixtures/sample_extractions.jsonl',
      model_id: config.model_id,
      model_url: config.model_url
    });
    
    otel_helpers.expectSpansContainName(
      exporter.getFinishedSpans(),
      sut.processExtractionFile.name
    )
  })
});

describe('generateXLSX', () => {
  it('no quotes', async () => {
    const stream = new PassThrough();
    await sut.generateXLSX([],stream)
    const workbook = new ExcelJS.Workbook()
    await workbook.xlsx.read(stream)
    const worksheet = workbook.getWorksheet('Parking Lot');
    expect(worksheet.rowCount).toEqual(1)
    expect(worksheet.getRow(1).values).toEqual([undefined,
      "Summary", "ID", "Quote", "Type"
    ])
  })

  it('one quote', async () => {
    const stream = new PassThrough();
    await sut.generateXLSX([{
      original: quote(sut.QuoteClass.INNER_THINKING, "I ate chicken yesterday", "001"),
      verbs: ["Eat", "Consume"],
      keyPoint: "chicken",
      supportingDetail: " yesterday"
    }],stream)
    const workbook = new ExcelJS.Workbook()
    await workbook.xlsx.read(stream)
    const worksheet = workbook.getWorksheet('Parking Lot');
    expect(worksheet.rowCount).toEqual(2)
    expect(worksheet.getRow(1).values).toEqual([undefined, 
      "Summary", "ID", "Quote", "Type"
    ])
    expect(worksheet.getRow(2).values).toEqual([undefined, 
      "Eat chicken yesterday", "001", "I ate chicken yesterday", "Inner thinking"
    ])
  })

  it('no supporting detail', async () => {
    const stream = new PassThrough();
    await sut.generateXLSX([{
      original: quote(sut.QuoteClass.INNER_THINKING, "I ate chicken", "001"),
      verbs: ["Eat", "Consume"],
      keyPoint: "chicken",
    }],stream)
    const workbook = new ExcelJS.Workbook()
    await workbook.xlsx.read(stream)
    const worksheet = workbook.getWorksheet('Parking Lot');
    expect(worksheet.rowCount).toEqual(2)
    expect(worksheet.getRow(1).values).toEqual([undefined, 
      "Summary", "ID", "Quote", "Type"
    ])
    expect(worksheet.getRow(2).values).toEqual([undefined, 
      "Eat chicken", "001", "I ate chicken", "Inner thinking"
    ])
  })

  it('multiple quotes', async () => {
    const stream = new PassThrough();
    await sut.generateXLSX([
      {
        original: quote(sut.QuoteClass.INNER_THINKING, "We decided not to eat chicken", "103"),
        verbs: ["Decide"],
        keyPoint: "not to eat chicken",
      },
      {
        original: quote(sut.QuoteClass.EMOTIONAL_REACTION, "Smile when I saw it", "555"),
        verbs: ["Smile"],
        keyPoint: "when I see it",
      },
      {
        original: quote(sut.QuoteClass.PERSONAL_RULE, "I shouldn't do that", "123"),
        verbs: ["Should"],
        keyPoint: "not do that",
      }
    ],stream)
    const workbook = new ExcelJS.Workbook()
    await workbook.xlsx.read(stream)
    const worksheet = workbook.getWorksheet('Parking Lot');
    expect(worksheet.rowCount).toEqual(4)
    expect(worksheet.getRow(1).values).toEqual([undefined, 
      "Summary", "ID", "Quote", "Type"
    ])
    expect(worksheet.getRow(2).values).toEqual([undefined, 
      "Decide not to eat chicken", "103", "We decided not to eat chicken", "Inner thinking"
    ])
    expect(worksheet.getRow(3).values).toEqual([undefined, 
      "Smile when I see it", "555", "Smile when I saw it", "Emotional Reaction"
    ])
    expect(worksheet.getRow(4).values).toEqual([undefined, 
      "Should not do that", "123", "I shouldn't do that", "Personal Rule"
    ])
  })

  it('styling', async () => {
    const stream = new PassThrough();
    await sut.generateXLSX([{
      original: quote(sut.QuoteClass.INNER_THINKING, "I ate chicken yesterday", "001"),
      verbs: ["Eat", "Consume"],
      keyPoint: "chicken",
      supportingDetail: " yesterday"
    }],stream)
    const workbook = new ExcelJS.Workbook()
    await workbook.xlsx.read(stream)
    const worksheet = workbook.getWorksheet('Parking Lot');

    expect(worksheet.getCell(1,1).text).toEqual("Summary")
    expect(worksheet.getColumn(1).width).toEqual(90)

    expect(worksheet.getCell(1,2).text).toEqual("ID")
    expect(worksheet.getColumn(2).width).toEqual(10)

    expect(worksheet.getCell(1,3).text).toEqual("Quote")
    expect(worksheet.getColumn(3).width).toEqual(90)

    expect(worksheet.getCell(1,4).text).toEqual("Type")
    expect(worksheet.getColumn(4).width).toEqual(20)

    expect(worksheet.getRow(2).alignment).toEqual({ 
      vertical: 'top', 
      horizontal: 'left', 
      wrapText: true 
    })
    expect(worksheet.getRow(2).height).toEqual(150)
  })

  it('OTEL', async () => {
    const { exporter } = otel_helpers.memorySDK()
    
    const stream = new PassThrough();
    await sut.generateXLSX([{
      original: quote(sut.QuoteClass.INNER_THINKING, "I ate chicken yesterday", "001"),
      verbs: ["Eat", "Consume"],
      keyPoint: "chicken",
      supportingDetail: " yesterday"
    }],stream)
    
    otel_helpers.expectSpansContainName(
      exporter.getFinishedSpans(),
      sut.generateXLSX.name
    )
  })
})