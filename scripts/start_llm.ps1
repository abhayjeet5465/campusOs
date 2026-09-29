# Starts the local LLM server. Run in its own terminal before `python -m backend`.
# Port 8090, not 8080: 8080 is commonly taken by other dev tooling.
param([string]$Model = "llama-3.2-3b-instruct-q4_k_m.gguf", [int]$Port = 8090)

$root = Split-Path $PSScriptRoot -Parent
$exe = Get-ChildItem "$root\models\llama.cpp" -Recurse -Filter llama-server.exe -EA SilentlyContinue |
       Select-Object -First 1
if (-not $exe) {
  Write-Error "llama-server.exe missing. Run: python scripts\fetch_models.py server"; exit 1
}

$gguf = Join-Path "$root\models" $Model
if (-not (Test-Path $gguf)) {
  # Fall back to any GGUF present, so a partially-fetched setup still starts.
  $gguf = (Get-ChildItem "$root\models" -Filter *.gguf -EA SilentlyContinue | Select-Object -First 1).FullName
  if (-not $gguf) { Write-Error "No .gguf in models\. Run: python scripts\fetch_models.py llm"; exit 1 }
  Write-Warning "$Model not found - using $(Split-Path $gguf -Leaf) instead."
}

Write-Host "Serving $(Split-Path $gguf -Leaf) on http://127.0.0.1:$Port"
& $exe.FullName -m $gguf --host 127.0.0.1 --port $Port -c 4096 -t 4
