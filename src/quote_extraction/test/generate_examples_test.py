from core import INNER_THINKING, EMOTIONAL_REACTION, PERSONAL_RULE
import core
import csv
import generate_examples as sut
from . import helpers as h
import pytest

def should_except_with(f, exception_args):
    try:
        f()
        pytest.fail("Expected exception")
    except Exception as e:
        assert e.args == exception_args

def should_except_with_malformed_csv(f):
    should_except_with(f,("malformed rows in CSV",))

def should_except_with_no_dir(f,dir):
    should_except_with(f,(f"directory not found: {dir}",))

def should_except_with_no_documents(f,dir):
    should_except_with(f,(f"no documents found in {dir}",))

# generate_quote_map vvv

def test__generate_quote_map__empty_reader():
    reader = csv.reader([])
    assert {} == sut.generate_quote_map(reader)

def test__generate_quote_map__malformed_row():
    reader = csv.reader([""])
    should_except_with_malformed_csv(
        lambda: sut.generate_quote_map(reader)
    )

    reader = csv.reader(["a"])
    should_except_with_malformed_csv(
        lambda: sut.generate_quote_map(reader)
    )

    reader = csv.reader(["a,b"])
    should_except_with_malformed_csv(
        lambda: sut.generate_quote_map(reader)
    )

def test__generate_quote_map__one_row():
    reader = csv.reader(["001,this is a quote,inner thinking"])
    assert {
        "001": [sut.Quote("this is a quote",[INNER_THINKING])]
    } == sut.generate_quote_map(reader)

def test__generate_quote_map__multiple_rows():
    reader = csv.reader([
        "001,this is a quote,inner thinking",
        "002,this is another quote,emotional reaction"
    ])
    assert {
        "001": [sut.Quote("this is a quote",[INNER_THINKING])],
        "002": [sut.Quote("this is another quote",[EMOTIONAL_REACTION])]
    } == sut.generate_quote_map(reader)

def test__generate_quote_map__multiple_quotes_for_one_source():
    reader = csv.reader([
        "001,this is a quote,inner thinking",
        "001,this is another quote,emotional reaction"
    ])
    assert {
        "001": [
            sut.Quote("this is a quote",[INNER_THINKING]),
            sut.Quote("this is another quote",[EMOTIONAL_REACTION])
        ],
    } == sut.generate_quote_map(reader)

def test__generate_quote_map__blank_source_id():
    reader = csv.reader([
        " ,this is a quote,inner thinking",
        "002,this is another quote,emotional reaction"
    ])
    assert {
        "002": [sut.Quote("this is another quote",[EMOTIONAL_REACTION])]
    } == sut.generate_quote_map(reader)

def test__generate_quote_map__blank_source_id():
    reader = csv.reader([
        "ID,QUOTE,TYPE",
        "001,this is a quote,inner thinking"
    ])
    assert {
        "001": [sut.Quote("this is a quote",[INNER_THINKING])],
    } == sut.generate_quote_map(reader)

def test__generate_quote_map__invalid_kind():
    reader = csv.reader([
        "001,this is a quote,outer thinking",
        "002,this is another quote,emotional reaction"
    ])
    assert {
        "002": [sut.Quote("this is another quote",[EMOTIONAL_REACTION])]
    } == sut.generate_quote_map(reader)

    reader = csv.reader([
        "001,this is a quote,inner thinking",
        "002,this is another quote,something random"
    ])
    assert {
        "001": [sut.Quote("this is a quote",[INNER_THINKING])]
    } == sut.generate_quote_map(reader)

    reader = csv.reader([
        "001,this is a quote,personal rule",
        "002,this is another quote,something random"
    ])
    assert {
        "001": [sut.Quote("this is a quote",[PERSONAL_RULE])]
    } == sut.generate_quote_map(reader)

def test__generate_quote_map__inner_thinking():
    reader = csv.reader([
        "001,this is a quote,inner thinking",
    ])
    assert {
        "001": [sut.Quote("this is a quote",[INNER_THINKING])]
    } == sut.generate_quote_map(reader)

    reader = csv.reader([
        "001,this is a quote,reason",
    ])
    assert {
        "001": [sut.Quote("this is a quote",[INNER_THINKING])]
    } == sut.generate_quote_map(reader)

def test__generate_quote_map__emotional_reaction():
    reader = csv.reader([
        "001,this is a quote,react",
    ])
    assert {
        "001": [sut.Quote("this is a quote",[EMOTIONAL_REACTION])]
    } == sut.generate_quote_map(reader)

    reader = csv.reader([
        "001,this is a quote,emotion",
    ])
    assert {
        "001": [sut.Quote("this is a quote",[EMOTIONAL_REACTION])]
    } == sut.generate_quote_map(reader)

def test__generate_quote_map__personal_rule():
    reader = csv.reader([
        "001,this is a quote,person",
    ])
    assert {
        "001": [sut.Quote("this is a quote",[PERSONAL_RULE])]
    } == sut.generate_quote_map(reader)

    reader = csv.reader([
        "001,this is a quote,rule",
    ])
    assert {
        "001": [sut.Quote("this is a quote",[PERSONAL_RULE])]
    } == sut.generate_quote_map(reader)

    reader = csv.reader([
        "001,this is a quote,guid",
    ])
    assert {
        "001": [sut.Quote("this is a quote",[PERSONAL_RULE])]
    } == sut.generate_quote_map(reader)

    reader = csv.reader([
        "001,this is a quote,principle",
    ])
    assert {
        "001": [sut.Quote("this is a quote",[PERSONAL_RULE])]
    } == sut.generate_quote_map(reader)

def test__generate_quote_map__multiple_kinds():
    reader = csv.reader([
        "001,this is a quote,inner thinking emotional reaction",
    ])
    assert {
        "001": [sut.Quote("this is a quote",[INNER_THINKING, EMOTIONAL_REACTION])]
    } == sut.generate_quote_map(reader)

    reader = csv.reader([
        "001,this is a quote,\"emotional reaction, personal rule\"",
    ])
    assert {
        "001": [sut.Quote("this is a quote",[EMOTIONAL_REACTION, PERSONAL_RULE])]
    } == sut.generate_quote_map(reader)

def test__generate_quote_map__replaces_fancy_characters():
    content = "fancy chars “”’‘…"
    reader = csv.reader([
        f"001,{content},personal rule",
    ])
    assert {
        "001": [sut.Quote(core.clean_content(content),[PERSONAL_RULE])]
    } == sut.generate_quote_map(reader)

def test__generate_quote_map__strips_quote():
    content = "   stripped quote  "
    reader = csv.reader([
        f"001,{content},inner thinking",
    ])
    assert {
        "001": [sut.Quote(core.clean_content(content),[INNER_THINKING])]
    } == sut.generate_quote_map(reader)

def test__generate_quote_map__removes_starting_number():
    content = "#123 quote with number"
    reader = csv.reader([
        f"001,{content},inner thinking",
    ])
    assert {
        "001": [sut.Quote(core.clean_content(content),[INNER_THINKING])]
    } == sut.generate_quote_map(reader)

    content = "  #123 quote with number"
    reader = csv.reader([
        f"001,{content},inner thinking",
    ])
    assert {
        "001": [sut.Quote(core.clean_content(content),[INNER_THINKING])]
    } == sut.generate_quote_map(reader)

# generate_quote_map ^^^

# generate_source_map vvv

def test__generate_source_map__non_exisent_dir(fs):
    should_except_with_no_dir(
        lambda: sut.generate_source_map([],"/i-dont-exist"),
        "/i-dont-exist"
    )

def test__generate_source_map__no_documents(fs):
    should_except_with_no_documents(
        lambda: sut.generate_source_map([],"/"),
        "/"
    )

    fs.create_dir("/docs")
    should_except_with_no_documents(
        lambda: sut.generate_source_map([],"/docs"),
        "/docs"
    )

def test__generate_source_map__no_source_ids(fs):
    fs.create_file("/file.docx")
    assert {} == sut.generate_source_map([],"/")

def test__generate_source_map__one_source_id(fs):
    h.write_bytes("/001_file.docx",h.BASIC_BYTES)
    assert {
        "001": h.BASIC_CONTENT
    } == sut.generate_source_map(["001"],"/")

def test__generate_source_map__two_source_ids(fs):
    h.write_bytes("/001_file.docx",h.BASIC_BYTES)
    h.write_bytes("/002_file.docx",h.BASIC_BYTES)
    assert {
        "001": h.BASIC_CONTENT,
        "002": h.BASIC_CONTENT
    } == sut.generate_source_map(["001", "002"],"/")

def test__generate_source_map__cant_find_source_id(fs):
    h.write_bytes("/001_file.docx",h.BASIC_BYTES)
    h.write_bytes("/002_file.docx",h.BASIC_BYTES)
    assert {
        "001": h.BASIC_CONTENT
    } == sut.generate_source_map(["001", "003"],"/")

def test__generate_source_map__replaces_fancy_characters(fs):
    h.write_bytes("/001_file.docx",h.FANCY_BYTES)
    assert {
        "001": "\"Fancy quoted text\"\nFancy's apostrophe\nFancy ellipses...\n"
    } == sut.generate_source_map(["001"],"/")

# generate_source_map ^^^

# generate_formatted_examples vvv

def test__generate_formatted_examples__remaps_fields():
    source_ids = ["001", "002"]
    source_map = {
        "001": "Hello!",
        "002": "Goodbye!"
    }
    quote_map = {
        "001": [
            sut.Quote("ello",[EMOTIONAL_REACTION]),
            sut.Quote("o!",[INNER_THINKING])
        ],
        "002": [
            sut.Quote("bye!",[EMOTIONAL_REACTION])
        ]
    }
    assert [
        {
          "extractions": [
              {
                  "extraction_class": EMOTIONAL_REACTION,
                  "extraction_text": "ello",
              },
              {
                  "extraction_class": INNER_THINKING,
                  "extraction_text": "o!",
              },
          ],
          "id": "001",
          "text": "Hello!",
        },
        {
            "extractions": [
                {
                    "extraction_class": EMOTIONAL_REACTION,
                    "extraction_text": "bye!",
                },
            ],
            "id": "002",
            "text": "Goodbye!",
        }
    ] == sut.generate_formatted_examples(source_ids,source_map,quote_map)

def test__generate_formatted_examples__joins_kinds():
    source_ids = ["001"]
    source_map = {"001": "Hello!"}
    quote_map = {"001": [sut.Quote("ello",[EMOTIONAL_REACTION, INNER_THINKING])]}
    assert [
        {
            "extractions": [
                {
                    "extraction_class": f"{EMOTIONAL_REACTION},{INNER_THINKING}",
                    "extraction_text": "ello",
                },
            ],
            "id": "001",
            "text": "Hello!",
        }
    ] == sut.generate_formatted_examples(source_ids,source_map,quote_map)

# generate_formatted_examples ^^^