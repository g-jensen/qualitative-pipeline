import core as sut
import pytest

def test__normalize_fancy_characters():
    assert "\"\"\'\'..." == sut.normalize_fancy_characters("“”’‘…")

def test__clean_content():
    assert "Normal"      == sut.clean_content("Normal")
    assert "\"\"\'\'..." == sut.clean_content("“”’‘…")
    assert "Hello"       == sut.clean_content("  Hello   ")
    assert "Goodbye"     == sut.clean_content(" #123 Goodbye   ")