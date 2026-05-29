from core import INNER_THINKING, EMOTIONAL_REACTION, PERSONAL_RULE
import core
from functools import partial
from . import helpers as h
import langextract as lx
from langextract import prompt_validation as pv
import extraction as sut
from pathlib import Path
import pytest
import pytest_mock

class ExtractionArgs:
    file: str
    document_id: str
    examples_file: str
    minimum_example_count: int
    question: str
    model: str
    model_url: str
    output: any

def extraction_args(
    file="document.docx",
    document_id="001",
    examples_file="examples.json", 
    minimum_example_count=1,
    question="What is the purpose of life?",
    model="llm:10b",
    model_url="https://localhost:1234", 
    output="extractions.jsonl"
):
    args = ExtractionArgs()
    args.file = file
    args.document_id = document_id
    args.examples_file = examples_file
    args.minimum_example_count = minimum_example_count
    args.question = question
    args.model = model
    args.model_url = model_url
    args.output = output
    return args

def example(text,extraction_tuples):
    return lx.data.ExampleData(
        text=text,
        extractions=list(map(
            lambda tuple: lx.data.Extraction(
                extraction_text=tuple[0],
                extraction_class=",".join(tuple[1])
            ), 
            extraction_tuples
        ))
    )

def lx_extract_mock(mocker,return_value):
    return mocker.patch('langextract.extract', return_value=return_value)

def lx_load_documents(path):
    return next(lx.io.load_annotated_documents_jsonl(Path(path),show_progress=False))

HELLO_WORLD_DOCUMENT = lx.data.AnnotatedDocument(
    text="Hello, World!",
    extractions=[
        lx.data.Extraction(
            extraction_text="World!",
            extraction_class="some_class",
            char_interval=lx.data.CharInterval(7)
        )
    ]
)
HELLO_WORLD_DOCUMENT.document_id = None

def prompt(question: str):
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

# examples_from_file vvv

def test__examples_from_file__no_examples(fs):    
    h.write_file("/no_examples.json", h.NO_EXAMPLES_TEXT)

    with open("/no_examples.json", "r") as file:
        examples = list(sut.examples_from_file(file))

    assert [] == examples

def test__examples_from_file__one_example_no_extractions(fs):
    fs.create_file("/one_example_no_extraction.json")
    
    h.write_file("/one_example_no_extraction.json", h.ONE_EXAMPLE_NO_EXTRACTION_TEXT)

    with open("/one_example_no_extraction.json", "r") as file:
        examples = list(sut.examples_from_file(file))

    expected_example = ("001", lx.data.ExampleData(
        text="some_example_text",
        extractions=[]
    ))

    assert [expected_example] == examples

def test__examples_from_file__one_example_one_extraction(fs):
    fs.create_file("/one_example_one_extraction.json")
    
    h.write_file("/one_example_one_extraction.json", h.ONE_EXAMPLE_ONE_EXTRACTION_TEXT)

    with open("/one_example_one_extraction.json", "r") as file:
        examples = list(sut.examples_from_file(file))

    expected_example = ("001", lx.data.ExampleData(
        text="the_example_text",
        extractions=[
            lx.data.Extraction(
                extraction_class="inner thinking",
                extraction_text="the_extraction_text"
            )
        ]
    ))

    assert [expected_example] == examples

def test__examples_from_file__one_example_multiple_extractions(fs):
    fs.create_file("/one_example_multiple_extractions.json")
    
    h.write_file("/one_example_multiple_extractions.json", h.ONE_EXAMPLE_MULTIPLE_EXTRACTIONS_TEXT)

    with open("/one_example_multiple_extractions.json", "r") as file:
        examples = list(sut.examples_from_file(file))

    expected_example = ("001", lx.data.ExampleData(
        text="more_example_text",
        extractions=[
            lx.data.Extraction(
                extraction_class="emotional reaction",
                extraction_text="first_extraction_text"
            ),
            lx.data.Extraction(
                extraction_class="personal rule",
                extraction_text="second_extraction_text"
            )
        ]
    ))

    assert [expected_example] == examples

def test__examples_from_file__multiple_examples_multiple_extractions(fs):
    fs.create_file("/multiple_examples_multiple_extractions.json")
    
    h.write_file("/multiple_examples_multiple_extractions.json", h.MULTIPLE_EXAMPLES_MULTIPLE_EXTRACTIONS_TEXT)

    with open("/multiple_examples_multiple_extractions.json", "r") as file:
        examples = list(sut.examples_from_file(file))

    expected_examples = [
        ("001", lx.data.ExampleData(
            text="first_example_text",
            extractions=[
                lx.data.Extraction(
                    extraction_class="inner thinking,emotional reaction",
                    extraction_text="first_extraction_text"
                ),
                lx.data.Extraction(
                    extraction_class="emotional reaction,personal rule",
                    extraction_text="second_extraction_text"
                )
            ]
        )),
        ("002", lx.data.ExampleData(
            text="second_example_text",
            extractions=[
                lx.data.Extraction(
                    extraction_class="inner thinking,personal rule",
                    extraction_text="third_extraction_text"
                )
            ]
        ))
    ]

    assert expected_examples == examples

# examples_from_file ^^^

# filter_examples vvv

def test__filter_examples__counts_extractions_in_example():
    examples = [
        ("001", example("example_1",[
            ("extracted_1",[INNER_THINKING, EMOTIONAL_REACTION]),
            ("extracted_2",[PERSONAL_RULE]),
            ("extracted_3",[INNER_THINKING]),
            ("extracted_4",[EMOTIONAL_REACTION])
        ]))
    ]

    filtered_examples = sut.filter_examples(examples,1)
    expected_examples = examples
    assert expected_examples == filtered_examples

def test__filter_examples__counts_extractions_across_examples():
    examples = [
        ("001",example("example_1",[("extracted_1",[INNER_THINKING, EMOTIONAL_REACTION])])),
        ("002",example("example_2",[("extracted_2",[PERSONAL_RULE])])),
        ("003",example("example_3",[("extracted_3",[INNER_THINKING])])),
        ("004",example("example_4",[("extracted_4",[EMOTIONAL_REACTION])]))
    ]

    filtered_examples = sut.filter_examples(examples,1)
    expected_examples = [examples[0], examples[1]]
    assert expected_examples == filtered_examples

    filtered_examples = sut.filter_examples(examples,2)
    expected_examples = examples
    assert expected_examples == filtered_examples

    filtered_examples = sut.filter_examples(examples,3)
    expected_examples = examples
    assert expected_examples == filtered_examples

# filter_examples ^^^

# pretty_extraction vvv

def test__pretty_extraction__no_char_interval():
    extraction = lx.data.Extraction(
        extraction_class=f"{INNER_THINKING},{EMOTIONAL_REACTION}",
        extraction_text="Possibly summarized text",
        char_interval=None
    )
    source_text = "This is the actual source that was extracted from"

    assert sut.pretty_extraction(source_text,extraction) == f"""\
Type: {INNER_THINKING}, {EMOTIONAL_REACTION}
Quote: \"Possibly summarized text\"
Alignment: None\
"""

def test__pretty_extraction__no_alignment():
    extraction = lx.data.Extraction(
        extraction_class=f"{INNER_THINKING},{EMOTIONAL_REACTION}",
        extraction_text="Possibly summarized text",
        char_interval=lx.data.CharInterval(8,25)
    )
    source_text = "This is the actual source that was extracted from"

    assert sut.pretty_extraction(source_text,extraction) == f"""\
Type: {INNER_THINKING}, {EMOTIONAL_REACTION}
Quote: \"Possibly summarized text\"
Alignment: None
Exact Text: \"the actual source\"\
"""

def test__pretty_extraction__non_exact_alignment():
    extraction = lx.data.Extraction(
        extraction_class=f"{INNER_THINKING},{EMOTIONAL_REACTION}",
        extraction_text="Possibly summarized text",
        char_interval=lx.data.CharInterval(8,25),
        alignment_status=lx.data.AlignmentStatus.MATCH_FUZZY
    )
    source_text = "This is the actual source that was extracted from"

    assert sut.pretty_extraction(source_text,extraction) == f"""\
Type: {INNER_THINKING}, {EMOTIONAL_REACTION}
Quote: \"Possibly summarized text\"
Alignment: MATCH_FUZZY
Exact Text: \"the actual source\"\
"""

def test__pretty_extraction__exact_alignment():
    extraction = lx.data.Extraction(
        extraction_class=f"{INNER_THINKING},{EMOTIONAL_REACTION}",
        extraction_text="Possibly summarized text",
        char_interval=lx.data.CharInterval(8,25),
        alignment_status=lx.data.AlignmentStatus.MATCH_EXACT
    )
    source_text = "This is the actual source that was extracted from"

    assert sut.pretty_extraction(source_text,extraction) == f"""\
Type: {INNER_THINKING}, {EMOTIONAL_REACTION}
Quote: \"Possibly summarized text\"
Alignment: MATCH_EXACT\
"""

# pretty_extraction ^^^

# annotated_document_from_example vvv

def test__annotated_document_from_example__exact_match():
    example = lx.data.ExampleData(
        text="This text will be matched exactly",
        extractions=[lx.data.Extraction(
            extraction_class="some_class",
            extraction_text="exactly"
        )]
    )
    annotated_document = sut.annotated_document_from_example(example)
    expected_document = lx.data.AnnotatedDocument(
        text=example.text,
        extractions=[lx.data.Extraction(
            extraction_class="some_class",
            extraction_text="exactly",
            alignment_status=lx.data.AlignmentStatus.MATCH_EXACT,
            char_interval=lx.data.CharInterval(26,33)
        )]
    )
    assert expected_document == annotated_document

def test__annotated_document_from_example__non_exact_match():
    example = lx.data.ExampleData(
        text="This text will not be matched exactly",
        extractions=[lx.data.Extraction(
            extraction_class="some_class",
            extraction_text="will be matched"
        )]
    )
    annotated_document = sut.annotated_document_from_example(example)
    expected_document = lx.data.AnnotatedDocument(
        text=example.text,
        extractions=[lx.data.Extraction(
            extraction_class="some_class",
            extraction_text="will be matched",
            alignment_status=lx.data.AlignmentStatus.MATCH_LESSER,
            char_interval=lx.data.CharInterval(10,14)
        )]
    )
    assert expected_document == annotated_document

# annotated_document_from_example ^^

# result_from_example_id vvv

def test__result_from_example_id__finds_and_converts_example(fs):
    examples_json = """[
    {
        "id": "test123",
        "text": "This is test text with first quote and second quote",
        "extractions": [
            {
                "extraction_class": "inner thinking",
                "extraction_text": "first quote"
            },
            {
                "extraction_class": "emotional reaction",
                "extraction_text": "second quote"
            }
        ]
    }
]"""
    h.write_file("/examples.json", examples_json)

    with open("/examples.json", "r") as file:
        result = sut.document_from_source_id(file, "test123")

    assert result.text == "This is test text with first quote and second quote"
    assert len(result.extractions) == 2
    assert result.extractions[0].extraction_class == "inner thinking"
    assert result.extractions[0].extraction_text == "first quote"
    assert result.extractions[0].char_interval is not None
    assert result.extractions[0].alignment_status is not None
    assert result.extractions[1].extraction_class == "emotional reaction"
    assert result.extractions[1].extraction_text == "second quote"
    assert result.extractions[1].char_interval is not None
    assert result.extractions[1].alignment_status is not None


def test__result_from_example_id__returns_none_when_id_not_found(fs):
    examples_json = """[
    {
        "id": "test123",
        "text": "This is test text",
        "extractions": []
    }
]"""
    h.write_file("/examples.json", examples_json)

    with open("/examples.json", "r") as file:
        result = sut.document_from_source_id(file, "nonexistent")

    assert result is None

def test__result_from_example_id__no_attributes_when_exact_match(fs):
    examples_json = """[
    {
        "id": "test123",
        "text": "The quick brown fox jumps over the lazy dog",
        "extractions": [
            {
                "extraction_class": "inner thinking",
                "extraction_text": "quick brown fox"
            }
        ]
    }
]"""
    h.write_file("/examples.json", examples_json)

    with open("/examples.json", "r") as file:
        result = sut.document_from_source_id(file, "test123")

    extraction = result.extractions[0]
    assert extraction.alignment_status == lx.data.AlignmentStatus.MATCH_EXACT
    assert (
        extraction.attributes is None or "full_extraction" not in extraction.attributes
    )

# result_from_example_id ^^^

# cache_annotated_document vvv

def test__cache_annotated_document__fresh_cache(fs):
    annotated_document = lx.data.AnnotatedDocument(
        text="Hello, World!",
        extractions=[
            lx.data.Extraction(
                extraction_class="some_class",
                extraction_text="Hello",
                char_interval=lx.data.CharInterval(0,5),
                alignment_status=lx.data.AlignmentStatus.MATCH_EXACT
            )
        ]
    )
    sut.cache_annotated_document("/", annotated_document, "001")
    loaded_document = lx_load_documents("/001.jsonl")
    assert annotated_document == loaded_document

def test__cache_annotated_document__existing_cache(fs):
    h.write_file("/002.jsonl", "already cached data")
    annotated_document = lx.data.AnnotatedDocument(
        text="Hello, World!",
        extractions=[
            lx.data.Extraction(
                extraction_class="some_class",
                extraction_text="Hello",
                char_interval=lx.data.CharInterval(0,5),
                alignment_status=lx.data.AlignmentStatus.MATCH_EXACT
            )
        ]
    )
    sut.cache_annotated_document("/", annotated_document, "002")
    loaded_document = lx_load_documents("/002.jsonl")
    assert annotated_document == loaded_document

def test__cache_annotated_document__dir_doesnt_exist(fs):
    annotated_document = lx.data.AnnotatedDocument(
        text="Hello, World!",
        extractions=[
            lx.data.Extraction(
                extraction_class="some_class",
                extraction_text="Hello",
                char_interval=lx.data.CharInterval(0,5),
                alignment_status=lx.data.AlignmentStatus.MATCH_EXACT
            )
        ]
    )
    sut.cache_annotated_document("/.example_cache", annotated_document, "001")
    loaded_document = lx_load_documents("/.example_cache/001.jsonl")
    assert annotated_document == loaded_document

# cache_annotated_document ^^^

# load_annotated_document vvv

def test__load_annotated_document__not_cached(fs):
    h.write_file("/examples.json",h.ONE_EXAMPLE_ONE_EXTRACTION_TEXT)
    document = sut.load_annotated_document("/examples.json","/.example_cache","001")
    with open("/examples.json", "r") as file:
        expected_document = sut.document_from_source_id(file,"001")
    
    assert expected_document == document

def test__load_annotated_document__not_cached_but_path_exists(fs):
    fs.create_dir("/.example_cache")
    h.write_file("/examples.json",h.ONE_EXAMPLE_ONE_EXTRACTION_TEXT)
    document = sut.load_annotated_document("/examples.json","/.example_cache","001")
    with open("/examples.json", "r") as file:
        expected_document = sut.document_from_source_id(file,"001")
    
    assert expected_document == document

def test__load_annotated_document__caches_if_not_cached(fs):
    h.write_file("/examples.json",h.ONE_EXAMPLE_ONE_EXTRACTION_TEXT)
    annotated_document = sut.load_annotated_document("/examples.json","/.example_cache","001")
    loaded_document = lx_load_documents("/.example_cache/001.jsonl")
    assert annotated_document == loaded_document

def test__load_annotated_document__cached(fs):
    h.write_file("/examples.json",h.ONE_EXAMPLE_ONE_EXTRACTION_TEXT)
    expected_document = lx.data.AnnotatedDocument(
        text="Hello, World!",
        extractions=[
            lx.data.Extraction(
                extraction_text="World!",
                extraction_class="some_class",
                char_interval=lx.data.CharInterval(7)
            )
        ]
    )
    sut.cache_annotated_document("/.example_cache",expected_document,"001")
    document = sut.load_annotated_document("/examples.json","/.example_cache","001")
    
    assert expected_document == document

# load_annotated_document ^^^

# extract vvv

def _test__extract__automatic_prompt_validation_off(extract_fn,fs,mocker):
    extract_mock = lx_extract_mock(mocker,HELLO_WORLD_DOCUMENT)
    args = extraction_args()
    h.write_bytes(args.file,h.BASIC_BYTES)
    h.write_file(args.examples_file,h.NO_EXAMPLES_TEXT)
    
    extract_fn(args)

    _, kwargs = extract_mock.call_args
    assert kwargs["prompt_validation_level"] == pv.PromptValidationLevel.OFF

def _test__extract__document_content(extract_fn,fs,mocker):
    extract_mock = lx_extract_mock(mocker,HELLO_WORLD_DOCUMENT)
    args = extraction_args()
    h.write_bytes(args.file,h.BASIC_BYTES)
    h.write_file(args.examples_file,h.NO_EXAMPLES_TEXT)
    
    extract_fn(args)

    _, kwargs = extract_mock.call_args
    assert kwargs["text_or_documents"] == core.normalize_fancy_characters(core.docx_content(Path(args.file)))

def _test__extract__prompt(extract_fn,fs,mocker):
    extract_mock = lx_extract_mock(mocker,HELLO_WORLD_DOCUMENT)
    args = extraction_args()
    h.write_bytes(args.file,h.BASIC_BYTES)
    h.write_file(args.examples_file,h.NO_EXAMPLES_TEXT)
    
    extract_fn(args)

    _, kwargs = extract_mock.call_args
    assert kwargs["prompt_description"] == prompt(args.question)

    args = extraction_args(question="What's up?")

    extract_fn(args)

    _, kwargs = extract_mock.call_args
    assert kwargs["prompt_description"] == prompt(args.question)

def _test__extract__examples(extract_fn,fs,mocker):
    extract_mock = lx_extract_mock(mocker,HELLO_WORLD_DOCUMENT)
    args = extraction_args()
    h.write_bytes(args.file,h.BASIC_BYTES)
    h.write_file(args.examples_file,h.MULTIPLE_EXAMPLES_MULTIPLE_EXTRACTIONS_TEXT)
    
    extract_fn(args)

    _, kwargs = extract_mock.call_args
    assert kwargs["examples"] == [sut.load_annotated_document(args.examples_file,".examples_cache","001")]

def _test__extract__config_resolved_model(extract_fn,fs,mocker):
    extract_mock = lx_extract_mock(mocker,HELLO_WORLD_DOCUMENT)
    args = extraction_args(model="gemini-2.5-flash")
    h.write_bytes(args.file,h.BASIC_BYTES)
    h.write_file(args.examples_file,h.MULTIPLE_EXAMPLES_MULTIPLE_EXTRACTIONS_TEXT)
    
    extract_fn(args)

    _, kwargs = extract_mock.call_args
    assert kwargs["config"] == lx.factory.ModelConfig(
        model_id=args.model,
        provider=None,
        provider_kwargs={
            "model_url": args.model_url
        }
    )

def _test__extract__config_unresolved_model(extract_fn,fs,mocker):
    extract_mock = lx_extract_mock(mocker,HELLO_WORLD_DOCUMENT)
    args = extraction_args(model="unknown-model")
    h.write_bytes(args.file,h.BASIC_BYTES)
    h.write_file(args.examples_file,h.MULTIPLE_EXAMPLES_MULTIPLE_EXTRACTIONS_TEXT)
    
    extract_fn(args)

    _, kwargs = extract_mock.call_args
    assert kwargs["config"] == lx.factory.ModelConfig(
        model_id=args.model,
        provider="OllamaLanguageModel",
        provider_kwargs={
            "model_url": args.model_url
        }
    )

def _test__extract__returns_extraction(extract_fn,fs,mocker):
    extract_mock = lx_extract_mock(mocker,HELLO_WORLD_DOCUMENT)
    args = extraction_args()
    h.write_bytes(args.file,h.BASIC_BYTES)
    h.write_file(args.examples_file,h.MULTIPLE_EXAMPLES_MULTIPLE_EXTRACTIONS_TEXT)
    
    result = extract_fn(args)
    assert result == HELLO_WORLD_DOCUMENT
    assert result.document_id == args.document_id

def _test__extract__otel(extract_fn,fs,mocker):
    exporter = h.memory_otel()
    extract_mock = lx_extract_mock(mocker,HELLO_WORLD_DOCUMENT)
    args = extraction_args()
    h.write_bytes(args.file,h.BASIC_BYTES)
    h.write_file(args.examples_file,h.MULTIPLE_EXAMPLES_MULTIPLE_EXTRACTIONS_TEXT)
    
    extract_fn(args)
    spans = exporter.get_finished_spans()
    
    h.assert_spans_contain_name(spans,sut.extract.__name__)
    assert h.span_by_name(spans,sut.extract.__name__).attributes == vars(args)
    
    h.assert_spans_contain_name(spans,"validate_examples")
    assert h.span_by_name(spans,"validate_examples").attributes == {
        "minimum_example_count": 1
    }

    h.assert_spans_contain_name(spans,"langextract")

def _test__extract_fn(extract_fn,fs,mocker):
    _test__extract__automatic_prompt_validation_off(extract_fn,fs,mocker)
    _test__extract__document_content(extract_fn,fs,mocker)
    _test__extract__prompt(extract_fn,fs,mocker)
    _test__extract__examples(extract_fn,fs,mocker)
    _test__extract__config_resolved_model(extract_fn,fs,mocker)
    _test__extract__config_unresolved_model(extract_fn,fs,mocker)
    _test__extract__returns_extraction(extract_fn,fs,mocker)
    _test__extract__otel(extract_fn,fs,mocker)

def test__extract(fs,mocker):
    _test__extract_fn(sut.extract,fs,mocker)

# extract ^^^

# extract_and_save vvv

def test__extract_and_save__extracts(fs,mocker):
    _test__extract_fn(partial(sut.extract_and_save,save_func=h.noop),fs,mocker)

def test__extract_and_save__saves_extraction(fs,mocker):
    extract_mock = lx_extract_mock(mocker,HELLO_WORLD_DOCUMENT)
    args = extraction_args()
    h.write_bytes(args.file,h.BASIC_BYTES)
    h.write_file(args.examples_file,h.MULTIPLE_EXAMPLES_MULTIPLE_EXTRACTIONS_TEXT)
    
    save_func_args = []
    sut.extract_and_save(args,lambda doc,args: save_func_args.append((doc,args)))
    assert save_func_args == [(HELLO_WORLD_DOCUMENT,args)]

def _test__saves_extraction_to_jsonl_by_default(args,test_fn,fs,mocker):
    expected_document = HELLO_WORLD_DOCUMENT
    extract_mock = lx_extract_mock(mocker,expected_document)
    h.write_bytes(args.file,h.BASIC_BYTES)
    h.write_file(args.examples_file,h.MULTIPLE_EXAMPLES_MULTIPLE_EXTRACTIONS_TEXT)
    
    assert not fs.exists(args.output)

    test_fn()

    loaded_document = lx_load_documents(args.output)

    assert expected_document == loaded_document

def test__extract_and_save__saves_extraction_to_jsonl_by_default(fs,mocker):
    args = extraction_args()
    test_fn = lambda: sut.extract_and_save(args)
    _test__saves_extraction_to_jsonl_by_default(
        args, test_fn, fs, mocker
    )

# extract_and_save ^^^