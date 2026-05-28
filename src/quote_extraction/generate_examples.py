import argparse
from core import INNER_THINKING, EMOTIONAL_REACTION, PERSONAL_RULE
import core
import csv
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint
import json

@dataclass
class Quote:
    content: str
    kinds: list[str]

def is_valid_source_id(source_id: str):
    return (source_id.strip() and source_id != "ID")

def is_valid_quote(quote: Quote):
    return len(quote.kinds) > 0

def find_source_file(source_id, source_documents):
    for file in source_documents:
        if file.name.startswith(source_id):
            return file
    return None

def generate_source_map(source_ids, documents_dir):
    source_map = {}
    source_documents = core.files_in_dir(documents_dir)

    if len(source_documents) == 0:
        raise Exception(f"no documents found in {documents_dir}")

    for source_id in source_ids:
        source_file = find_source_file(source_id,source_documents)
        if source_file is not None:
            source_map[source_id] = core.normalize_fancy_characters(
                core.docx_content(source_file)
            )

    return source_map

def generate_quote_map(csv_reader):
    quote_map = {}

    for row in csv_reader:
        if len(row) < 3 :
            raise Exception("malformed rows in CSV")
        
        source_id = row[0]
        if not is_valid_source_id(source_id):
            continue
        content = core.clean_content(row[1])
        kinds = core.kinds_from_str(row[2])
        quote = Quote(content,kinds)

        if not is_valid_quote(quote):
            continue

        prev = quote_map.get(source_id)
        quote_map[source_id] = (prev or []) + [quote]
    
    return quote_map

def extraction_class_from_kinds(kinds):
    return ",".join(kinds)

def extractions_from_quotes(quotes):
    extractions = []

    for quote in quotes:
        extractions.append({
            "extraction_class": extraction_class_from_kinds(quote.kinds),
            "extraction_text": quote.content
        })
    
    return extractions

def generate_formatted_examples(source_ids,source_map,quote_map):
    examples = []
    
    for source_id in source_ids:
        source = source_map[source_id]
        quotes = quote_map[source_id]
        examples.append({
            "id": source_id,
            "text": source,
            "extractions": extractions_from_quotes(quotes)
        })

    return examples

def main():
    parser = argparse.ArgumentParser(description="Extract quotes from CSV")
    parser.add_argument("-f", "--file", default="./synthesized_documents/cognition_quotes.csv", help="CSV to read")
    parser.add_argument("-d", "--documents_dir", default="./synthesized_documents/examples", help="Directory to find documents")
    parser.add_argument("-o", "--output", default="./examples.json", help="File to output examples to")
    args = parser.parse_args()

    csv_path = args.file
    documents_dir = args.documents_dir
    output_path = args.output

    print(f"Documents source: {documents_dir}")
    print(f"Generating examples from: {csv_path}")

    with open(csv_path, mode='r', newline='') as csv_file:
        csv_reader = csv.reader(csv_file)
        quote_map = generate_quote_map(csv_reader)
    
    quote_ids = quote_map.keys()
    source_map = generate_source_map(quote_ids,documents_dir)
    source_ids = source_map.keys()
    examples = generate_formatted_examples(source_ids,source_map,quote_map)
    
    with open(output_path, "w") as f:
        json.dump(examples, f, indent=4)
    
    print(f"Successfully wrote examples to {output_path}")

if __name__ == "__main__":
    main()
