from . import servicer as sut
import pytest
from pytest_mock import MockerFixture
from unittest.mock import MagicMock

from protos import extract_pb2
from protos import extract_pb2_grpc
import grpc

from langextract import prompt_validation as pv
import langextract as lx


@pytest.fixture(scope="module")
def grpc_add_to_server(): return extract_pb2_grpc.add_ExtractServicer_to_server


@pytest.fixture(scope="module")
def grpc_servicer(): return sut.ExtractServicer()


@pytest.fixture(scope="module")
def grpc_stub_cls(): return extract_pb2_grpc.ExtractStub


INNER_THINKING = "inner thinking"
EMOTIONAL_REACTION = "emotional reaction"
PERSONAL_RULE = "personal rule"


def request(
    topic="Burgers", 
    document="I like chicken. I like burgers", 
    model="gemini-2.5-flash"
):
    return extract_pb2.ExtractionRequest(topic=topic,document=document,model=model)


BURGERS_DOCUMENT = lx.data.AnnotatedDocument(
    text="I like chicken. I like burgers.",
    extractions=[
        lx.data.Extraction(
            extraction_text="I like burgers.",
            extraction_class=PERSONAL_RULE,
            char_interval=lx.data.CharInterval(start_pos=16,end_pos=30)
        )
    ]
)


BURGER_AND_CHICKEN_DOCUMENT = lx.data.AnnotatedDocument(
    text="I like chicken. I like burgers.",
    extractions=[
        lx.data.Extraction(
            extraction_text="I like chicken.",
            extraction_class=PERSONAL_RULE,
            char_interval=lx.data.CharInterval(start_pos=0,end_pos=15)
        ),
        lx.data.Extraction(
            extraction_text="I like burgers.",
            extraction_class=PERSONAL_RULE,
            char_interval=lx.data.CharInterval(start_pos=16,end_pos=30)
        )
    ]
)


EXAMPLE_INTERNAL_THINKING = lx.data.AnnotatedDocument(
    extractions=[
        lx.data.Extraction(
            extraction_class=INNER_THINKING, 
            extraction_text="I think salad goes well with hot foods.",
            char_interval=lx.data.CharInterval(start_pos=39,end_pos=77)
        )
    ], 
    text="The chicken went great with the salad. I think salad goes well with hot foods."
)


def prompt(topic: str):
    return f"""\
You are given a transcript of an interview given by a cognitive researcher.
Extract interior cognition of the interviewee relevant for research analysis that fit into these categories:
\"{INNER_THINKING}\", \"{EMOTIONAL_REACTION}\", and \"{PERSONAL_RULE}\".
The point is to extract quotes relevant to answer the topic: \"{topic}\"
1. NEVER include any extraction classes that are not: \"{INNER_THINKING}\", \"{EMOTIONAL_REACTION}\", or \"{PERSONAL_RULE}\".
2. NEVER quote the interviewer. ONLY quote the interviewee.
3. NEVER duplicate an extraction or paraphrase.
4. Extractions that fall under multiple cognition types MUST have an extraction_class with comma-separated types.
5. ONLY Use EXACT quotes. No paraphrasing.
6. Extractions should be in order.
7. Do not extract quotes that are simply 'setting the scene' or irrelevant basic opinions. Personal rules are still good though, obivously.
"""


def lx_extract_mock(mocker,return_value):
    return mocker.patch('langextract.extract', return_value=return_value)


def assert_prompt_validation(extract_mock: MagicMock, prompt_validation):
    assert len(extract_mock.call_args_list) == 1
    _, kwargs = extract_mock.call_args_list[0]
    assert kwargs["prompt_validation_level"] == prompt_validation


def assert_document_content(extract_mock: MagicMock, content: str):
    assert len(extract_mock.call_args_list) == 1
    _, kwargs = extract_mock.call_args_list[0]
    assert kwargs["text_or_documents"] == content


def assert_prompt(extract_mock: MagicMock, prompt):
    _, kwargs = extract_mock.call_args
    assert kwargs["prompt_description"] == prompt


def assert_model(extract_mock: MagicMock, model: str):
    assert len(extract_mock.call_args_list) == 1
    _, kwargs = extract_mock.call_args_list[0]
    assert kwargs["config"] == lx.factory.ModelConfig(
        model_id=model
    )


# def test__call(grpc_stub):
#     request = extract_pb2.ExtractionRequest()
#     responses = list(grpc_stub.Call(request))


# def test__handle__malformed_request(mocker: MockerFixture, grpc_stub):
#     extract_mock = lx_extract_mock(mocker,BURGERS_DOCUMENT)
    
#     request = extract_pb2.ExtractionRequest(topic=None,document=None,model=None)
#     _responses = list(grpc_stub.Call(request))
    
#     assert len(extract_mock.call_args_list) == 0


def test__handle__automatic_prompt_validation_off(mocker: MockerFixture, grpc_stub):
    extract_mock = lx_extract_mock(mocker,BURGERS_DOCUMENT)
    
    _responses = list(grpc_stub.Call(request()))

    assert_prompt_validation(extract_mock, pv.PromptValidationLevel.OFF)


def test__handle__document_content(mocker: MockerFixture, grpc_stub):
    extract_mock = lx_extract_mock(mocker,BURGERS_DOCUMENT)

    _responses = list(grpc_stub.Call(request(
        document="I like chicken. I like burgers.",
    )))

    assert_document_content(extract_mock, "I like chicken. I like burgers.")


def test_forcing__handle__document_content(mocker: MockerFixture, grpc_stub):
    extract_mock = lx_extract_mock(mocker,BURGERS_DOCUMENT)

    _responses = list(grpc_stub.Call(request(
        document="I hate chicken. I hate burgers.",
    ))) 
    
    assert_document_content(extract_mock, "I hate chicken. I hate burgers.")


def test__handle__prompt(mocker: MockerFixture, grpc_stub):
    extract_mock = lx_extract_mock(mocker,BURGERS_DOCUMENT)
    
    _responses = list(grpc_stub.Call(request(
        topic="Burgers",
    )))

    assert_prompt(extract_mock, prompt("Burgers"))


def test_forcing__handle__prompt(mocker: MockerFixture, grpc_stub):
    extract_mock = lx_extract_mock(mocker,BURGERS_DOCUMENT)
    
    _responses = list(grpc_stub.Call(request(
        topic="Chicken",
    )))

    assert_prompt(extract_mock, prompt("Chicken"))


def test__handle__examples(mocker: MockerFixture, grpc_stub):
    extract_mock = lx_extract_mock(mocker,BURGERS_DOCUMENT)
    
    _responses = list(grpc_stub.Call(request()))

    _, kwargs = extract_mock.call_args
    assert kwargs["examples"] == [EXAMPLE_INTERNAL_THINKING]


def test__handle__gemini_model(mocker: MockerFixture, grpc_stub):
    extract_mock = lx_extract_mock(mocker,BURGERS_DOCUMENT)
    
    _responses = list(grpc_stub.Call(request(
        model="gemini-2.5-flash",
    )))

    assert_model(extract_mock, "gemini-2.5-flash")


def test_forcing__handle__gemini_model(mocker: MockerFixture, grpc_stub):
    extract_mock = lx_extract_mock(mocker,BURGERS_DOCUMENT)
    
    _responses = list(grpc_stub.Call(request(
        model="gemini-3.8-flash",
    )))

    assert_model(extract_mock, "gemini-3.8-flash")


def test__handle__claude_model(mocker: MockerFixture, grpc_stub):
    extract_mock = lx_extract_mock(mocker,BURGERS_DOCUMENT)
    
    _responses = list(grpc_stub.Call(request(
        model="claude-opus-4-8",
    )))

    assert_model(extract_mock, "claude-opus-4-8")


def test_forcing__handle__claude_model(mocker: MockerFixture, grpc_stub):
    extract_mock = lx_extract_mock(mocker,BURGERS_DOCUMENT)
    
    _responses = list(grpc_stub.Call(request(
        model="claude-opus-5",
    )))

    assert_model(extract_mock, "claude-opus-5")


def test__extract__unknown_model(mocker: MockerFixture, grpc_stub):
    extract_mock = lx_extract_mock(mocker,BURGERS_DOCUMENT)

    with pytest.raises(grpc._channel._MultiThreadedRendezvous) as excinfo:
        _responses = list(grpc_stub.Call(request(
            model="unknown-model",
        )))
    
    assert 'status = StatusCode.INVALID_ARGUMENT' in str(excinfo.value)
    assert 'details = "Invalid model: unknown-model"' in str(excinfo.value)
    assert len(extract_mock.call_args_list) == 0


def test_forcing__extract__unknown_model(mocker: MockerFixture, grpc_stub):
    extract_mock = lx_extract_mock(mocker,BURGERS_DOCUMENT)

    with pytest.raises(grpc._channel._MultiThreadedRendezvous) as excinfo:
        _responses = list(grpc_stub.Call(request(
            model="another-unknown-model",
        )))
    
    assert 'status = StatusCode.INVALID_ARGUMENT' in str(excinfo.value)
    assert 'details = "Invalid model: another-unknown-model"' in str(excinfo.value)
    assert len(extract_mock.call_args_list) == 0


def test__handle__returns_extraction(mocker: MockerFixture, grpc_stub):
    extract_mock = lx_extract_mock(mocker,BURGERS_DOCUMENT)

    responses = list(grpc_stub.Call(request()))
    
    extraction = BURGERS_DOCUMENT.extractions[0]
    assert responses == [
        extract_pb2.Extraction(
            text=extraction.extraction_text,
            type=extraction.extraction_class,
            interval=extract_pb2.Interval(start=extraction.char_interval.start_pos,end=extraction.char_interval.end_pos)
        )
    ]
 

def test__handle__returns_multiple_extractions(mocker: MockerFixture, grpc_stub):
    extract_mock = lx_extract_mock(mocker,BURGER_AND_CHICKEN_DOCUMENT)

    responses = list(grpc_stub.Call(request()))
    
    extraction_0 = BURGER_AND_CHICKEN_DOCUMENT.extractions[0]
    extraction_1 = BURGER_AND_CHICKEN_DOCUMENT.extractions[1]
    assert responses == [
        extract_pb2.Extraction(
            text=extraction_0.extraction_text,
            type=extraction_0.extraction_class,
            interval=extract_pb2.Interval(start=extraction_0.char_interval.start_pos,end=extraction_0.char_interval.end_pos)
        ),
        extract_pb2.Extraction(
            text=extraction_1.extraction_text,
            type=extraction_1.extraction_class,
            interval=extract_pb2.Interval(start=extraction_1.char_interval.start_pos,end=extraction_1.char_interval.end_pos)
        )
    ]