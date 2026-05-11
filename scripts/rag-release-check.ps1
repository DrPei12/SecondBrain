[CmdletBinding()]
param(
    [ValidateSet("preflight", "fake", "live")]
    [string]$Mode = "preflight",
    [int]$BackendPort = 8012,
    [int]$FakeProviderPort = 8787,
    [string]$Python = "python",
    [string]$ServerPython = "",
    [int]$SmokeTimeoutSeconds = 300,
    [string]$Report = "",
    [switch]$SkipSecretScan
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$BackendRoot = Join-Path $ProjectRoot "backend"

function Invoke-Checked {
    param([scriptblock]$Command)
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE"
    }
}

if (-not $SkipSecretScan) {
    Invoke-Checked { & $Python (Join-Path $ProjectRoot "scripts\check-rag-secrets.py") }
}

if (-not $ServerPython) {
    $venvPython = Join-Path $ProjectRoot ".tmp\winvenv\Scripts\python.exe"
    $ServerPython = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { $Python }
}

$apiBase = "http://127.0.0.1:$BackendPort/api"
$reportPath = if ($Report) {
    $Report
} elseif ($Mode -eq "fake") {
    Join-Path $ProjectRoot ".tmp\RAG_FAKE_PROVIDER_REPORT.json"
} else {
    Join-Path $ProjectRoot "tests\RAG_LIVE_REPORT.json"
}

$fakeProcess = $null
$backendProcess = $null
$savedEnv = @{}
$envNames = @(
    "LLM_PROVIDER",
    "DASHSCOPE_API_KEY",
    "BAILIAN_API_KEY",
    "BAILIAN_BASE_URL",
    "BAILIAN_LLM_MODEL",
    "BAILIAN_EMBEDDING_MODEL",
    "BAILIAN_EMBEDDING_DIMENSIONS",
    "BAILIAN_ENABLE_THINKING",
    "SECOND_BRAIN_API_KEY",
    "DATABASE_URL",
    "RAG_WORKING_DIR",
    "RAG_VECTOR_STORE_FILE",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy"
)

try {
    foreach ($name in $envNames) {
        $savedEnv[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
    }

    if ($Mode -eq "fake") {
        $fakeProcess = Start-Process `
            -FilePath $Python `
            -ArgumentList @((Join-Path $ProjectRoot "tests\fake_openai_server.py"), "--port", [string]$FakeProviderPort) `
            -WorkingDirectory $ProjectRoot `
            -PassThru `
            -WindowStyle Hidden
        Start-Sleep -Seconds 2

        $env:LLM_PROVIDER = "bailian"
        $env:DASHSCOPE_API_KEY = "fake-provider-key"
        $env:BAILIAN_BASE_URL = "http://127.0.0.1:$FakeProviderPort/v1"
        $env:BAILIAN_LLM_MODEL = "qwen3.6-plus"
        $env:BAILIAN_EMBEDDING_MODEL = "text-embedding-v4"
        $env:BAILIAN_EMBEDDING_DIMENSIONS = "1024"
        $env:BAILIAN_ENABLE_THINKING = "false"
        $env:SECOND_BRAIN_API_KEY = "dev-api-key"
        $env:HTTP_PROXY = ""
        $env:HTTPS_PROXY = ""
        $env:ALL_PROXY = ""
        $env:NO_PROXY = "*"
        $env:http_proxy = ""
        $env:https_proxy = ""
        $env:all_proxy = ""
        $env:no_proxy = "*"
        $fakeDb = Join-Path $ProjectRoot ".tmp\fake_second_brain.db"
        Copy-Item -LiteralPath (Join-Path $BackendRoot "second_brain.db") -Destination $fakeDb -Force
        $env:DATABASE_URL = "sqlite+aiosqlite:///" + ($fakeDb -replace "\\", "/")
        $env:RAG_WORKING_DIR = Join-Path $ProjectRoot ".tmp\fake_rag_data"
        $env:RAG_VECTOR_STORE_FILE = Join-Path $ProjectRoot ".tmp\fake_rag_data\vector_store.json"
    }

    Invoke-Checked { & $Python (Join-Path $ProjectRoot "tests\test_rag_performance.py") --preflight }

    if ($Mode -eq "preflight") {
        exit 0
    }

    $backendProcess = Start-Process `
        -FilePath $ServerPython `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", [string]$BackendPort) `
        -WorkingDirectory $BackendRoot `
        -PassThru `
        -WindowStyle Hidden
    Start-Sleep -Seconds 8

    if ($Mode -eq "fake") {
        Invoke-Checked {
            & $Python `
                (Join-Path $ProjectRoot "tests\test_rag_performance.py") `
                --api-base $apiBase `
                --api-key "dev-api-key" `
                --timeout $SmokeTimeoutSeconds `
                --allow-missing-source-hints `
                --report $reportPath
        }
    } else {
        Invoke-Checked {
            & $Python `
                (Join-Path $ProjectRoot "tests\test_rag_performance.py") `
                --api-base $apiBase `
                --api-key "dev-api-key" `
                --timeout $SmokeTimeoutSeconds `
                --queries (Join-Path $ProjectRoot "tests\rag_quality_questions.json") `
                --report $reportPath
        }
    }
}
finally {
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force
    }
    if ($fakeProcess -and -not $fakeProcess.HasExited) {
        Stop-Process -Id $fakeProcess.Id -Force
    }
    foreach ($name in $envNames) {
        if ($null -eq $savedEnv[$name]) {
            Remove-Item "Env:$name" -ErrorAction SilentlyContinue
        } else {
            [Environment]::SetEnvironmentVariable($name, $savedEnv[$name], "Process")
        }
    }
}
