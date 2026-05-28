from core import INNER_THINKING, EMOTIONAL_REACTION, PERSONAL_RULE, INNER_COGNITION_TYPES
import core
from dataclasses import asdict
import langextract as lx
from langextract import prompt_validation as pv
from langextract import resolver
import langextract.providers as providers
from langextract.providers import router
import claude_provider
from pathlib import Path
import json
import random
from typing import Callable

def extraction_from_json(json_extraction):
    return lx.data.Extraction(
        extraction_class=json_extraction["extraction_class"],
        extraction_text=json_extraction["extraction_text"]
    )

def extractions_from_json(json_extractions):
    extractions = []

    for json_extraction in json_extractions:
        extractions.append(extraction_from_json(json_extraction))

    return extractions

def example_from_json(json_example):
    return lx.data.ExampleData(
        text=json_example["text"],
        extractions=extractions_from_json(json_example["extractions"])
    )

def examples_from_file(file) -> tuple[str, lx.data.ExampleData]:
    examples = []

    json_examples = json.load(file)
    
    for json_example in json_examples:
        yield (json_example["id"], example_from_json(json_example))

def initial_counter_map():
    counter_map = {}
    for key in INNER_COGNITION_TYPES:
        counter_map[key] = 0
    return counter_map

def is_counter_map_full(counter_map, minimum_per_type_count):
    for key in INNER_COGNITION_TYPES:
        if counter_map[key] < minimum_per_type_count:
            return False
    return True

def update_counter_map(counter_map, example):
    for extraction in example.extractions:
        kinds = core.kinds_from_str(extraction.extraction_class)
        for kind in kinds:
            counter_map[kind] += 1

def filter_examples(examples: list[tuple[str, lx.data.ExampleData]], minimum_per_type_count):
    filtered_examples = []
    counter_map = initial_counter_map()
    
    for example in examples:
        if is_counter_map_full(counter_map,minimum_per_type_count):
            return filtered_examples
        filtered_examples.append(example)
        update_counter_map(counter_map,example[1])    

    return filtered_examples

def get_alignment(extraction):
    if extraction.alignment_status is None:
        return None
    else:
        return extraction.alignment_status.name

def pretty_extraction(source_text: str, extraction: lx.data.Extraction):
    output = f"""\
Type: {", ".join(core.kinds_from_str(extraction.extraction_class))}
Quote: \"{extraction.extraction_text}\"\
"""

    alignment = get_alignment(extraction)

    output += f"\nAlignment: {alignment}"

    if extraction.alignment_status == lx.data.AlignmentStatus.MATCH_EXACT:
        return output
    elif extraction.char_interval is not None:
        start_pos = extraction.char_interval.start_pos
        end_pos = extraction.char_interval.end_pos
        return output + f"""
Exact Text: \"{source_text[start_pos:end_pos]}\"\
"""

    return output

def annotated_document_from_example(example: lx.data.ExampleData) -> lx.data.AnnotatedDocument:
    aligner = resolver.WordAligner()
    aligned_groups = aligner.align_extractions(
        extraction_groups=[example.extractions], source_text=example.text
    )

    aligned_extractions = list(aligned_groups[0]) if aligned_groups else []

    return lx.data.AnnotatedDocument(
        text=example.text,
        extractions=aligned_extractions,
    )

def document_from_source_id(file, source_id):
    json_examples = json.load(file)

    for json_example in json_examples:
        if json_example["id"] == source_id:
            example = example_from_json(json_example)
            result = annotated_document_from_example(example)
            return result

    return None

def cache_annotated_document(cache_dir, document: lx.data.AnnotatedDocument, source_id: str):
    lx.io.save_annotated_documents(
        [document], 
        output_name=f"{source_id}.jsonl",
        output_dir=str(cache_dir),
        show_progress=False
    )

def cached_document(cache_dir, source_id):
    if Path(cache_dir).exists():
        cached_files = core.files_in_dir(cache_dir)
        return next(filter(lambda f: f.name.startswith(source_id), cached_files),None)
    else:
        return None

def load_annotated_document(examples_file_path, cache_dir, source_id):
    cached_doc = cached_document(cache_dir,source_id)
    if cached_doc:
        return next(lx.io.load_annotated_documents_jsonl(cached_doc,show_progress=False))
    else:
        with open(examples_file_path, "r") as file:
            doc = document_from_source_id(file,source_id)
            cache_annotated_document(cache_dir,doc,source_id)
            return doc

def _document_content(document_path):
    return core.normalize_fancy_characters(core.docx_content(Path(document_path)))

def _prompt(question: str):
    return f"""\
You are given a transcript of an interview given by a cognitive researcher.
Extract interior cognition of the interviewee relevant for research analysis that fit into these categories:
\"{INNER_THINKING}\", \"{EMOTIONAL_REACTION}\", and \"{PERSONAL_RULE}\".
The point is to extract quotes relevant to answer the question: \"{question}\"
1. NEVER include any extraction classes that are not: \"{INNER_THINKING}\", \"{EMOTIONAL_REACTION}\", or \"{PERSONAL_RULE}\".
2. NEVER quote the interviewer. ONLY quote the interviewee.
3. NEVER duplicate an extraction or paraphrase.
4. Extractions that fall under multiple cognition types MUST have an extraction_class with comma-separated types.
5. ONLY Use EXACT quotes. No paraphrasing.
6. Extractions should be in order.
7. Do not extract quotes that are simply 'setting the scene' or irrelevant basic opinions. Personal rules are still good though, obivously.
"""

def _validated_examples(examples_path, minimum_example_count: int):
    with open(Path(examples_path), 'r') as file:
        all_examples = examples_from_file(file)
        filtered_examples = filter_examples(all_examples,minimum_example_count)
        validate_example = lambda e: load_annotated_document(
            examples_path,
            ".examples_cache",
            e[0]
        )
    return list(map(validate_example,filtered_examples))

def _config(model_id: str, model_url: str):
    provider_str = None
    try:
        router.resolve(model_id)
    except Exception as e:
        provider_str = "OllamaLanguageModel"
        print(f"can't resolve model, defaulting to {provider_str}")

    return lx.factory.ModelConfig(
        model_id=model_id,
        provider=provider_str,
        provider_kwargs={
            "model_url": model_url
        }
    )

def extract(args) -> lx.data.AnnotatedDocument:
    providers.load_builtins_once()
    extraction = lx.extract(
        prompt_validation_level=pv.PromptValidationLevel.OFF,
        text_or_documents=_document_content(args.file),
        prompt_description=_prompt(args.question),
        examples=_validated_examples(args.examples_file,args.minimum_example_count),
        config=_config(args.model,args.model_url)
        # temperature=0.1,
        # extraction_passes=2,
        # max_workers=3,
        # max_char_buffer=500 # Smaller contexts for better quote matching but also smaller quotes with less context
    )
    extraction.document_id = args.document_id
    return extraction

def _save_extraction_to_jsonl(extraction,args):
    lx.io.save_annotated_documents(
        [extraction],
        output_name=args.output,
        output_dir=".",
    )

def extract_and_save(args, save_func: Callable[[lx.data.AnnotatedDocument, any], None] = _save_extraction_to_jsonl) -> lx.data.AnnotatedDocument:
    result = extract(args)
    save_func(result,args)
    return result