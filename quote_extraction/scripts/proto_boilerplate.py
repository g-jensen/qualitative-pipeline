# TODO - add automated testing for this script
# TODO - add patch support to automate service registration

import sys
import os
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Sequence

from grpc_tools import protoc
from google.protobuf import descriptor_pb2


ROOT_DIR = Path("templates/service")
TEMPLATE_SUFFIX = ".template"
PATCH_SUFFIX = ".patch"
DEFINITION_SUFFIX = ".definition"


def get_file_paths():
    template_file_paths = []
    patch_file_paths = []

    for root, dirs, files in os.walk(ROOT_DIR):
        for file in files:
            path = os.path.join(root, file)

            if path.endswith(TEMPLATE_SUFFIX):
                template_file_paths.append(path)
            
            if path.endswith(PATCH_SUFFIX):
                patch_file_paths.append(path)

    return (template_file_paths, patch_file_paths)


def replace_strs(s: str, replace_dict: dict[str,str]):
    for (old, new) in replace_dict.items():
        s = s.replace(old,new)
    return s


@dataclass
class Procedure:
    name: str
    input_type: str
    output_type: str


@dataclass
class Service:
    name: str
    procedures: Sequence[Procedure]


@dataclass
class Proto:
    name: str
    services: Sequence[Service]


def procedure_context(old_context: dict[str,str], procedure: Procedure):
    context = old_context.copy()
    context.update({
        "${PROCEDURE_NAME}": procedure.name,
        "${PROCEDURE_NAME_LOWER}": procedure.name.lower(),
        "${PROCEDURE_INPUT_TYPE}": procedure.input_type,
        "${PROCEDURE_OUTPUT_TYPE}": procedure.output_type,
    })
    return context


def all_content(contexts: Sequence[dict[str,str]], template: str):
    _all = ""
    for context in contexts:
        _all += replace_strs(template, context)
    return _all


def parse_proto(file_path):
    file_path = Path(file_path)

    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        desc_path = f.name

    protoc.main([
        "grpc_tools.protoc",
        f"--proto_path={file_path.parent}",
        f"--descriptor_set_out={desc_path}",
        str(file_path),
    ])

    desc_set = descriptor_pb2.FileDescriptorSet()
    desc_set.ParseFromString(open(desc_path, "rb").read())
    os.unlink(desc_path)

    file_desc = desc_set.file[0]

    services = []
    for svc in file_desc.service:
        procedures = []
        for method in svc.method:
            in_type = method.input_type.split(".")[-1]
            out_type = method.output_type.split(".")[-1]
            procedures.append(Procedure(name=method.name, input_type=in_type, output_type=out_type))
        services.append(Service(name=svc.name, procedures=procedures))

    return Proto(name=file_path.stem, services=services)


def print_err(*args):
    print(*args, file=sys.stderr)


def main():
    args = sys.argv[1:]
    
    proto = parse_proto(args[0])

    template_file_paths, patch_file_paths = get_file_paths()
    
    procedure_test_path = str(ROOT_DIR / Path("PROCEDURE_TEST" + DEFINITION_SUFFIX))
    procedure_test_content = open(procedure_test_path).read()

    procedure_src_path = str(ROOT_DIR / Path("PROCEDURE_SRC" + DEFINITION_SUFFIX))
    procedure_src_content = open(procedure_src_path).read()

    new_file_count = 0

    for service in proto.services:
        context = {
            "${PROTO_NAME}": proto.name,
            "${SERVICE_NAME}": service.name,
            "${SERVICE_NAME_LOWER}": service.name.lower(),
        }
        procedure_contexts = list(map(lambda p: procedure_context(context,p), service.procedures))
        context["${PROCEDURE_TEST[@]}"] = all_content(procedure_contexts, procedure_test_content)
        context["${PROCEDURE_SRC[@]}"] = all_content(procedure_contexts, procedure_src_content)

        for template_file_path in template_file_paths:
            template_file_content = open(template_file_path, "r").read()

            file_path = Path(replace_strs(template_file_path, context))
            reoriented_path = Path(*(file_path.parts[2:]))
            detemplated_path = Path(str(reoriented_path)[:-len(TEMPLATE_SUFFIX)])
            
            if detemplated_path.exists():
                print_err(f"Skipping: service file {detemplated_path} already exists")
                continue
                
            new_file_count += 1
            
            file_content = replace_strs(template_file_content, context)

            os.makedirs(detemplated_path.parent, exist_ok=True)
            with open(detemplated_path, "w") as file:
                file.write(file_content)
    
    print_err(f"Done. Created {new_file_count} new files.")


if __name__ == "__main__":
    main()
