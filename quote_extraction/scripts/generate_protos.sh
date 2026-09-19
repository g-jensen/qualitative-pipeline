#!/bin/bash

for proto in idl/protos/*.proto; do
    python3 -m grpc_tools.protoc -Iidl --python_out=. --pyi_out=. --grpc_python_out=. "$proto"
done
