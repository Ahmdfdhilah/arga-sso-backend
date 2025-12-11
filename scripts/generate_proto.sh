#!/bin/bash

set -e

echo "Generating protobuf code..."

if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found"
    exit 1
fi

PROTO_PATH="proto"
OUTPUT_PATH="grpc_server/generated"

mkdir -p $OUTPUT_PATH

echo "Generating Python gRPC code..."
python3 -m grpc_tools.protoc \
    -I. \
    --python_out=$OUTPUT_PATH \
    --grpc_python_out=$OUTPUT_PATH \
    --pyi_out=$OUTPUT_PATH \
    ${PROTO_PATH}/sso/user.proto

touch $OUTPUT_PATH/__init__.py

echo "Proto generation complete!"
