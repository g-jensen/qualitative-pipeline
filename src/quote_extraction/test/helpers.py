from pathlib import Path

def noop(*args, **kwargs):
    pass

CURRENT_FILE = Path(__file__).resolve()
CURRENT_DIR = CURRENT_FILE.parent
FIXTURES_PATH = "fixtures"


EXAMPLES_PATH = f"{FIXTURES_PATH}/examples"

def get_example_content(path):
    return (CURRENT_DIR / f"{EXAMPLES_PATH}/{path}").read_text()

NO_EXAMPLES_TEXT = get_example_content("no_examples.json")
ONE_EXAMPLE_ONE_EXTRACTION_TEXT = get_example_content("one_example_one_extraction.json")
ONE_EXAMPLE_NO_EXTRACTION_TEXT = get_example_content("one_example_no_extractions.json")
ONE_EXAMPLE_MULTIPLE_EXTRACTIONS_TEXT = get_example_content("one_example_multiple_extractions.json")
MULTIPLE_EXAMPLES_MULTIPLE_EXTRACTIONS_TEXT = get_example_content("multiple_examples_multiple_extractions.json")


DOCS_PATH = f"{FIXTURES_PATH}/docs"

def get_doc_content(path):
    return (CURRENT_DIR / f"{DOCS_PATH}/{path}").read_bytes()

BASIC_BYTES = get_doc_content("basic.docx")
BASIC_CONTENT = "This is a paragraph\nThis is another paragraph\nOne more paragraph\n"

FANCY_BYTES = get_doc_content("fancy.docx")


def write_file(path, content: str):
    with open(path, "w") as file:
        file.write(content)

def write_bytes(path, content: bytes):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as file:
        file.write(content)