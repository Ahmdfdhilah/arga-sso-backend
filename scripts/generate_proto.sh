#!/bin/bash

set -e

echo "Generating protobuf code..."

if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found"
    exit 1
fi

PROTO_PATH="proto"

# Generate directly to proto/sso
echo "Generating Python gRPC code..."
python3 -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    --pyi_out=. \
    ${PROTO_PATH}/sso/user.proto \
    ${PROTO_PATH}/sso/auth.proto

echo "Proto generation complete!"
echo "Generated files are in proto/sso/"
