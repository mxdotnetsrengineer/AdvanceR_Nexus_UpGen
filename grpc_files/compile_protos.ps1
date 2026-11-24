$ProtosDir = Join-Path $PSScriptRoot "protos"
$OutDir = Join-Path $PSScriptRoot "generated"

# Ensure important files/folders exists
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
New-Item -ItemType File -Force -Path (Join-Path $OutDir "__init__.py") | Out-Null

# Compile .proto files
python -m grpc_tools.protoc `
    -I"$ProtosDir" `
    --python_out="$OutDir" `
    --grpc_python_out="$OutDir" `
    "$ProtosDir\*.proto"

# Fix relative imports on *_pb2_grpc.py
python -c "import pathlib, re; [p.write_text(re.sub(r'^import (\w+_pb2)', r'from . import \1', p.read_text(encoding='utf-8'), flags=re.M), encoding='utf-8') for p in pathlib.Path(r'$OutDir').glob('*_pb2_grpc.py')]"

Write-Host "Protos compiled successfully." -ForegroundColor Green