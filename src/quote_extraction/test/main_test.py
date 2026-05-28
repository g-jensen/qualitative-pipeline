from core import INNER_THINKING, EMOTIONAL_REACTION, PERSONAL_RULE
import core
from . import extraction_test
from functools import partial
from . import helpers as h
import langextract as lx
from langextract import prompt_validation as pv
import main as sut
from pathlib import Path
import pytest
import pytest_mock
import sys
from unittest.mock import patch

def test__main__full_pass_without_errors(fs,mocker):
    command = [
        "program_name", 
        "--model", "gemma3:12b",
        "--document_id", "001"
    ]
    with patch.object(sys, 'argv', command):
        args = sut.parse_args()
        extraction_test._test__saves_extraction_to_jsonl_by_default(
            args, sut.main, fs, mocker
        )