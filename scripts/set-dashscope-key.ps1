[CmdletBinding()]
param(
    [string]$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
)

$secretDir = Join-Path $ProjectRoot '.secrets'
$keyPath = Join-Path $secretDir 'dashscope.key'

New-Item -ItemType Directory -Path $secretDir -Force | Out-Null

$secureKey = Read-Host 'Enter DashScope/Bailian API key' -AsSecureString
if ($secureKey.Length -eq 0) {
    throw 'No API key entered.'
}

$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
try {
    $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    $trimmedKey = $plainKey.Trim()
    if ($trimmedKey.Length -eq 0) {
        throw 'No API key entered.'
    }

    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($keyPath, $trimmedKey, $utf8NoBom)

    Write-Host "Wrote provider key to $keyPath"
    Write-Host 'Run: python tests/test_rag_performance.py --preflight'
}
finally {
    if ($bstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}
