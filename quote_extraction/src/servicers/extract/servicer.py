from protos import extract_pb2_grpc
from protos import extract_pb2

import langextract as lx
from langextract import prompt_validation as pv
from langextract.providers import router
import langextract.providers.gemini
from . import claude_provider
import json

from google.protobuf import any_pb2
from google.rpc import code_pb2
from google.rpc import error_details_pb2
from google.rpc import status_pb2
import grpc
from grpc_status import rpc_status


INNER_THINKING = "inner thinking"
EMOTIONAL_REACTION = "emotional reaction"
PERSONAL_RULE = "personal rule"


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


# TODO - load pre-compiled examples in from disk for tests and src. For now, these can be stored in the Docker image itself. Later, create an 'example store' service.
example_internal_thinking = lx.data.AnnotatedDocument(
    extractions=[
        lx.data.Extraction(
            extraction_class=INNER_THINKING, 
            extraction_text="I think salad goes well with hot foods.",
            char_interval=lx.data.CharInterval(start_pos=39,end_pos=77)
        )
    ], 
    text="The chicken went great with the salad. I think salad goes well with hot foods."
)


def is_valid_model(model: str):
    try:
        router.resolve(model)
        return True
    except Exception as _:
        return False


def extraction_response(extraction: lx.data.Extraction):
    return {
        "text": extraction.extraction_text,
        "class": extraction.extraction_class,
        "interval": [extraction.char_interval.start_pos, extraction.char_interval.end_pos]
    }


def handle(event, context):
    request: Request = TypeAdapter(Request).validate_json(event.body)

    if not is_valid_model(request.model):
        return {
            "statusCode": 400,
            "body": f"Unknown model: {request.model}"
        }

    document: lx.data.AnnotatedDocument = lx.extract(
        config=lx.factory.ModelConfig(model_id=request.model),
        examples=[example_internal_thinking],
        prompt_validation_level=pv.PromptValidationLevel.OFF,
        prompt_description=prompt(request.topic),
        text_or_documents=request.document
    )

    return {
        "statusCode": 200,
        "body": json.dumps(list(map(extraction_response, document.extractions)))
    }


def create_invalid_model_error_status(model):
    return status_pb2.Status(
        code=code_pb2.INVALID_ARGUMENT,
        message=f"Invalid model: {model}",
    )


class ExtractServicer(extract_pb2_grpc.ExtractServicer):
    def __init__(self):
        return
    
    def Call(self, request: extract_pb2.ExtractionRequest, context):
        if not is_valid_model(request.model):
            context.abort_with_status(rpc_status.to_status(create_invalid_model_error_status(request.model)))
            return

        document: lx.data.AnnotatedDocument = lx.extract(
            config=lx.factory.ModelConfig(model_id=request.model),
            examples=[example_internal_thinking],
            prompt_validation_level=pv.PromptValidationLevel.OFF,
            prompt_description=prompt(request.topic),
            text_or_documents=request.document
        )

        for extraction in document.extractions:
            yield extract_pb2.Extraction(
                text=extraction.extraction_text,
                type=extraction.extraction_class,
                interval=extract_pb2.Interval(start=extraction.char_interval.start_pos,end=extraction.char_interval.end_pos)
            )
