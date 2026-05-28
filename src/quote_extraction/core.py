from docx import Document
from pathlib import Path

INNER_THINKING = "inner thinking"
EMOTIONAL_REACTION = "emotional reaction"
PERSONAL_RULE = "personal rule"

INNER_COGNITION_TYPES = [INNER_THINKING, EMOTIONAL_REACTION, PERSONAL_RULE]

def files_in_dir(dir):
    try:
        return [f for f in Path(dir).iterdir() if f.is_file()]
    except Exception as e:
        raise Exception(f"directory not found: {dir}")

def kinds_from_str(raw_kinds: str):
    lower_kinds = raw_kinds.lower()
    kinds = []
    
    if "inner thinking" in lower_kinds or\
       "reason" in lower_kinds:
        kinds.append(INNER_THINKING)
    
    if "react" in lower_kinds or\
       "emotion" in lower_kinds:
        kinds.append(EMOTIONAL_REACTION)

    if "person" in lower_kinds or\
       "rule" in lower_kinds or\
       "guid" in lower_kinds or\
       "principle" in lower_kinds:
        kinds.append(PERSONAL_RULE)
    
    return kinds

def docx_content(path):
    doc = Document(path)
    content = ""
    for para in doc.paragraphs:
        if not para.text.strip():
            continue
        content += para.text + "\n"
    return content

def normalize_fancy_characters(text):
    return text\
        .replace("“", "\"").replace("”", "\"")\
        .replace("’", "\'").replace("‘", "\'")\
        .replace("…", "...")

def numbers_in_a_row(content: str):
    for i, c in enumerate(content):
        if not c.isnumeric():
            return i
    return len(content)

def clean_content(content: str):
    content = normalize_fancy_characters(content).strip()
    if content.startswith("#"):
        rest = content[1:]
        content = content[1+numbers_in_a_row(rest):]
    return content.strip()