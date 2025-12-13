# Generate protobuf code for Windows

$ErrorActionPreference = "Stop"

Write-Host "Generating protobuf code..."

$PROTO_PATH = "proto"

# Generate directly to proto/sso
Write-Host "Generating Python gRPC code..."
python -m grpc_tools.protoc `
    -I. `
    --python_out=. `
    --grpc_python_out=. `
    --pyi_out=. `
    "$PROTO_PATH/sso/user.proto" `
    "$PROTO_PATH/sso/auth.proto"

Write-Host "Proto generation complete!"
Write-Host "Generated files are in proto/sso/"
