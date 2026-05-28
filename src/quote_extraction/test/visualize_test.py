import langextract as lx
import visualize as sut
import pytest

# add_paraphrase_attributes vvv

def test__add_paraphrase_attributes__adds_attributes_for_non_exact_match():
    text = "The quick brown fox jumps over the lazy dog"
    extraction = lx.data.Extraction(
        extraction_class="inner thinking",
        extraction_text="fast brown animal",
        char_interval=lx.data.CharInterval(start_pos=4, end_pos=19),
        alignment_status=lx.data.AlignmentStatus.MATCH_FUZZY,
    )

    result = lx.data.AnnotatedDocument(text=text, extractions=[extraction])

    sut.add_paraphrase_attributes(result)

    assert result.extractions[0].attributes is not None
    assert "full_extraction" in result.extractions[0].attributes
    assert result.extractions[0].attributes["full_extraction"] == "fast brown animal"

def test__add_paraphrase_attributes__no_attributes_for_exact_match():
    text = "The quick brown fox jumps over the lazy dog"
    extraction = lx.data.Extraction(
        extraction_class="inner thinking",
        extraction_text="quick brown fox",
        char_interval=lx.data.CharInterval(start_pos=4, end_pos=19),
        alignment_status=lx.data.AlignmentStatus.MATCH_EXACT,
    )

    result = lx.data.AnnotatedDocument(text=text, extractions=[extraction])

    sut.add_paraphrase_attributes(result)

    assert (
        result.extractions[0].attributes is None
        or "full_extraction" not in result.extractions[0].attributes
    )

def test__add_paraphrase_attributes__adds_attributes_when_no_char_interval():
    text = "The quick brown fox"
    extraction = lx.data.Extraction(
        extraction_class="inner thinking",
        extraction_text="fast animal",
        char_interval=None,
        alignment_status=None,
    )

    result = lx.data.AnnotatedDocument(text=text, extractions=[extraction])

    sut.add_paraphrase_attributes(result)

    assert result.extractions[0].attributes is not None
    assert result.extractions[0].attributes["full_extraction"] == "fast animal"

# add_paraphrase_attributes ^^^