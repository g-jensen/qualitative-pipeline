protos=("quote_extraction")

for proto in "${protos[@]}"; do
    out_path=src/servicers/$proto
    python -m grpc_tools.protoc -I./protos --python_out=$out_path --pyi_out=$out_path --grpc_python_out=$out_path protos/$proto.proto
done