import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

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