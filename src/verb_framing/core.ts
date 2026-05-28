import { generateText, GenerateTextResult, Output } from 'ai';
import * as promises from 'fs/promises';
import * as self from './core.js';
import { ModelConfig, resolveModel } from './model-resolver.js';
import { z } from 'zod';
import ExcelJS from 'exceljs';
import Stream from 'stream';
import { verbFramingTracer } from './open_telemetry.js';
import * as otel from '../open_telemetry/core.js'
import { wrapOTEL } from '../open_telemetry/core.js';

const TRAILING_PUNCTUATION = ['.','!','?',',',';',':']

export enum QuoteClass {
  INNER_THINKING = 'inner thinking',
  EMOTIONAL_REACTION = 'emotional reaction',
  PERSONAL_RULE = 'personal rule'
}

export interface Quote {
  class: QuoteClass,
  text: string,
  documentId: string
}

export interface ReframedQuote {
  original: Quote,
  verbs: string[],
  keyPoint: string,
  supportingDetail?: string,
}

interface Document {
  quotes: Quote[],
  id: string
}

export async function generateXLSX(reframedQuotes: ReframedQuote[], output_stream: Stream) {
  return wrapOTEL(verbFramingTracer(), generateXLSX.name, async (_span) => {
    const workbook = new ExcelJS.Workbook();
    const sheet = workbook.addWorksheet('Parking Lot');
    sheet.columns = columns()
    reframedQuotes.forEach(quote => addRow(sheet,quote))
    await workbook.xlsx.write(output_stream);
  });
}

function columns() {
  return [
    { header: "Summary", width: 90 },
    { header: "ID", width: 10 },
    { header: "Quote", width: 90 },
    { header: "Type", width: 20 }
  ];
}

function addRow(sheet: ExcelJS.Worksheet, quote: ReframedQuote) {
  const row = sheet.addRow([
    reframedQuoteToString(quote),
    quote.original.documentId,
    quote.original.text,
    quoteClassToPrettyString(quote.original.class)
  ])
  row.alignment = { vertical: 'top', horizontal: 'left', wrapText: true }
  row.height = 150
}

function quoteClassToPrettyString(class_: QuoteClass) {
  return new Map([
    [QuoteClass.INNER_THINKING, "Inner thinking"],
    [QuoteClass.EMOTIONAL_REACTION, "Emotional Reaction"],
    [QuoteClass.PERSONAL_RULE, "Personal Rule"]
  ]).get(class_)
}

function reframedQuoteToString(quote: ReframedQuote) {
  const str = `${quote.verbs[0]} ${quote.keyPoint}`
  if (quote.supportingDetail) {
    return `${str}${quote.supportingDetail}`
  }
  return str
}

export async function processExtractionFile(args: { file: string; model_id: string; model_url: string }): Promise<ReframedQuote[]> {
  return wrapOTEL(verbFramingTracer(), processExtractionFile.name, async (_span) => {
    const documents = await self.parseExtractionFile(args.file);
    const quotes = documents.map(d => d.quotes).flat();
    const config = { model_id: args.model_id, model_url: args.model_url }
    return await self.batchReframeQuotes(quotes, config);
  })
}

export async function parseExtractionFile(path: string): Promise<Document[]> {
  return wrapOTEL(verbFramingTracer(), parseExtractionFile.name, async (_span) => {
    const content = await promises.readFile(path, 'utf-8');
    const lines = content.trim().split('\n');
    const documents: Document[] = [];
    
    for (const line of lines) {
      const raw_document = JSON.parse(line);
      const quotes = []
      for (const extraction of raw_document.extractions) {
        const quote = extractionToQuote(extraction,raw_document.document_id);
        if (quote) {
          quotes.push(quote);
        }
      }
      if (quotes.length > 0) {
        documents.push({quotes: quotes, id: raw_document.document_id})
      }
    }
    return documents;
  })
}

export function extractionToQuote(extraction: any, documentId: string): Quote | undefined {
  const extraction_class = stringToQuoteClass(extraction.extraction_class)
  if (extraction.extraction_text && extraction_class) {
    return {class: extraction_class, text: extraction.extraction_text, documentId: documentId};
  }
  return undefined;
}

function stringToQuoteClass(s: string): QuoteClass | undefined {
  return Object.values(QuoteClass).includes(s as QuoteClass)
    ? (s as QuoteClass)
    : undefined;
}

export function batchReframeQuotes(quotes: Quote[], config: any): Promise<ReframedQuote[]> {
  return wrapOTEL(verbFramingTracer(), batchReframeQuotes.name, async (_span) => {
    return new Promise((resolve,reject) => {
      const quote_count = quotes.length
      const results: ReframedQuote[] = Array(quote_count);
      
      let i = 0;
      for (const quote of quotes) {
        reframeQuote(quote, config).then((reframed: ReframedQuote) => {
            results[i++] = reframed;
            if (i == quote_count) {
              resolve(results)
            }
          },reject)
      }
    });
  })
}

export async function reframeQuote(quote: Quote, config: ModelConfig): Promise<ReframedQuote> {
  return wrapOTEL(verbFramingTracer(), reframeQuote.name, async (span) => {
    span.setAttributes(otel.flattenObject(quote))
    const verbs = await generateVerbPhrase(quote,config)
    const best_verb = verbs[0]
    const keyPoint = await generateKeyPoint(best_verb,quote,config)
    const supportingDetail = await generateSupportingDetail(best_verb,keyPoint,quote,config)
    return {
      original: quote,
      verbs: verbs,
      keyPoint: keyPoint,
      supportingDetail: supportingDetail
    };
  })
}

export async function generateVerbPhrase(quote: Quote, config: ModelConfig) {
  return wrapOTEL(verbFramingTracer(), generateVerbPhrase.name, async (span) => {
    const result = (await generateText({
      model: resolveModel(config),
      system: verbPhrasePrompt(quote.class),
      prompt: quote.text,
      output: Output.object({schema: verbPhraseSchema(quote.class)}) // untested
    }))
    span.setAttributes(usageAttributes(result))
    const verbs = result.output;
    return conformVerbs(verbs,quote)
  })
}

// TODO - allow multi-word predicates like "Let them know", "Figure out" or "Feel left out"
export function verbPhrasePrompt(class_: QuoteClass): string {
  if (class_ == QuoteClass.EMOTIONAL_REACTION) {
    return 'Give me 2-5 possible emotions that the person who said this quote is feeling. These could be emotions explicitly mentioned in the quote or implied emotions. The emotion should be a single word and make sense in the sentence \"I feel <emotion>\". Respond only with the emotion. Do not include thought process.'
  }
  return 'Give me 2-5 possible verbs that describe what the person who said is doing/did do. These could be verbs explicitly mentioned in the quote or implied actions. Each candidate MUST be exactly one verb in the present tense. You should convert verb in the text to present tense. These can be very abstract actions, but try to keep things simple. The verb should make sense in the sentence \"I <verb>\". Respond only with the verb. Do not include thought process.'
}

export function verbPhraseSchema(class_: QuoteClass) {
  if (class_ == QuoteClass.EMOTIONAL_REACTION) {
    return z.array(z.string().describe('emotion (one word)')).min(2).max(5)
  }
  return z.array(z.string().describe('present tense verb (one word)')).min(2).max(5)
}

function usageAttributes(result: GenerateTextResult<any,any>) {
  return {
    'input_tokens': result.usage?.inputTokens,
    'output_tokens': result.usage?.outputTokens,
    'total_tokens': result.usage?.totalTokens
  }
}

function conformVerbs(verbs: string[], quote: Quote) {
  if (quote.class == QuoteClass.EMOTIONAL_REACTION) {
    return verbs.map((s) => "Feel " + conformEmotionalVerb(s))
  }
  return verbs.map(conformVerb)
}

function conformEmotionalVerb(verb: string) {
  let s = verb.trim()
  return s.charAt(0).toLowerCase() + s.slice(1)
}

function conformVerb(verb: string) {
  let s = verb.trim()
  return s.charAt(0).toUpperCase() + s.slice(1)
}

export async function generateKeyPoint(verb: string, quote: Quote, config: ModelConfig) {
  return wrapOTEL(verbFramingTracer(), generateKeyPoint.name, async (span) => {
    const result = (await generateText({
      model: resolveModel(config),
      system: keyPointSystem(quote.text),
      messages: [
          { role: 'user', content: keyPointPrompt(verb) },
          { role: 'assistant', content: keyPointResponseBeginning(verb) },
        ]
    }))
    span.setAttributes(keyPointAttributes(result,verb))
    
    const keyPoint = result.text
    return conformKeyPoint(verb,keyPoint)
  })
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

function keyPointAttributes(result: GenerateTextResult<any,any>, verb: string) {
  let attributes: any = usageAttributes(result)
  attributes['verb'] = verb
  return attributes
}

function conformKeyPoint(verb: string, keyPoint: string) {
  if (keyPoint.startsWith(verb)) {
    keyPoint = keyPoint.substring(verb.length).trim()
  }
  return removeTrailingPunctuation(keyPoint).trim()
}

function removeTrailingPunctuation(s: string) {
  return s.substring(0,trailingPunctuationStartIndex(s))
}

function trailingPunctuationStartIndex(s: string) {
  let i = s.length-1
  while (i >= 0) {
    if (!TRAILING_PUNCTUATION.includes(s.charAt(i))) {
      return i+1
    } else {
      i--
    }
  }
  return i+1
}

export async function generateSupportingDetail(verb: string, keyPoint: string, quote: Quote, config: ModelConfig) {
  return wrapOTEL(verbFramingTracer(), generateSupportingDetail.name, async (span) => {
    const result = (await generateText({
      model: resolveModel(config),
      system: supportingDetailSystem(quote.text),
      messages: [
        { role: 'user', content: supportingDetailPrompt(verb,keyPoint) },
        { role: 'assistant', content: supportingDetailResponseBeginning(verb,keyPoint) }
      ]
    }))
    span.setAttributes(supportingDetailAttributes(result,verb,keyPoint))

    const supportingDetail = result.text
    return conformSupportingDetail(supportingDetail)
  })
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

function supportingDetailAttributes(result: GenerateTextResult<any,any>, verb: string, keyPoint: string) {
  let attributes: any = keyPointAttributes(result,verb)
  attributes['key_point'] = keyPoint
  return attributes
}

function conformSupportingDetail(supportingDetail: string) {
  return maybeAddSpace(removeTrailingPunctuation(supportingDetail).trim())
}

function maybeAddSpace(s: string) {
  const is_blank = s.trim().length == 0
  if (!TRAILING_PUNCTUATION.includes(s.charAt(0)) && !is_blank) {
    return " " + s
  }
  return s
}