# Run from a source checkout in Windows PowerShell 5.1 or PowerShell 7.
[CmdletBinding()]
param([switch]$Install, [switch]$Repair, [switch]$SetupModels, [switch]$PublicOnly, [switch]$CloudOnly, [switch]$ProgressJson)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
function Write-SetupPhase([string]$Stage,[string]$Message){
    if($ProgressJson){@{stage=$Stage;message=$Message}|ConvertTo-Json -Compress|Write-Output}
    else{Write-Host $Message}
}
if (-not ($Install -or $Repair)) {
    Write-Host 'Usage: .\scripts\setup-windows.ps1 -Install [-SetupModels] [-PublicOnly]'
    Write-Host 'Repair: .\scripts\setup-windows.ps1 -Repair'
    Write-Host 'Installs locked Python packages and a private SHA-256-verified FFmpeg 7 shared runtime.'
    Write-Host 'Requires Windows x64, uv, an NVIDIA driver and the Microsoft Visual C++ x64 runtime.'
    Write-Host 'Models download only with -SetupModels; gated models require accepted HF terms/token.'
    exit 0
}
if (-not [Environment]::Is64BitOperatingSystem -or $env:OS -ne 'Windows_NT') {
    throw 'Native Windows x64 is required.'
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw 'Install uv first: winget install --id astral-sh.uv --exact ; open a new terminal.'
}
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    Write-SetupPhase 'python' 'Preparing Python 3.12'
    & uv python install 3.12
    if ($LASTEXITCODE -ne 0) { throw 'Python setup failed.' }
    $syncArgs = @('sync', '--locked', '--python', '3.12', '--no-dev')
    Write-SetupPhase 'dependencies' 'Installing locked Python dependencies'
    if ($Repair) { $syncArgs += @('--reinstall-package', 'torchcodec', '--reinstall-package', 'pyannote-audio') }
    & uv @syncArgs
    if ($LASTEXITCODE -ne 0) { throw 'Locked dependency installation failed.' }
    if($env:EWP_LOCAL_ACCELERATOR -eq 'amd'){
        Write-SetupPhase 'dependencies' 'Preparing AMD ROCm ASR (experimental); CPU alignment and diarization'
        & uv run --locked --no-sync python scripts/setup-amd.py
        if($LASTEXITCODE -ne 0){throw 'Experimental AMD runtime installation failed.'}
    }
    $prefix = if ($env:EWP_FFMPEG_PREFIX) { $env:EWP_FFMPEG_PREFIX } else { Join-Path $env:LOCALAPPDATA 'ewp-transcripts\ffmpeg-7' }
    $dll = Join-Path $prefix 'bin\avutil-59.dll'
    if ($Repair -or -not (Test-Path $dll)) {
        $tempRoot = Join-Path ([IO.Path]::GetTempPath()) ('ewp-windows-setup-' + [Guid]::NewGuid())
        New-Item -ItemType Directory -Path $tempRoot | Out-Null
        try {
            Write-SetupPhase 'media' 'Downloading verified FFmpeg runtime'
            $archive = Join-Path $tempRoot 'ffmpeg.zip'
            $url = 'https://github.com/GyanD/codexffmpeg/releases/download/7.1.1/ffmpeg-7.1.1-full_build-shared.zip'
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            $request=[Net.HttpWebRequest]::Create($url)
            $request.Timeout=600000;$request.ReadWriteTimeout=600000
            $response=$request.GetResponse()
            try {
                $source=$response.GetResponseStream();$target=[IO.File]::Create($archive)
                try {
                    $buffer=New-Object byte[] 1048576
                    $bytes=0L;$clock=[Diagnostics.Stopwatch]::StartNew();$lastReport=0.0
                    while(($count=$source.Read($buffer,0,$buffer.Length)) -gt 0){
                        $target.Write($buffer,0,$count);$bytes+=$count
                        if($ProgressJson -and ($clock.Elapsed.TotalSeconds-$lastReport -ge .5 -or $bytes -eq $response.ContentLength)){
                            $lastReport=$clock.Elapsed.TotalSeconds
                            $rate=$bytes/[Math]::Max(.001,$lastReport)
                            $eta=if($response.ContentLength -gt 0){[Math]::Max(0,($response.ContentLength-$bytes)/$rate)}else{$null}
                            @{stage='download';message='FFmpeg';bytes=$bytes;total=$response.ContentLength;unit='B';rate=$rate;eta_seconds=$eta}|ConvertTo-Json -Compress|Write-Output
                        }
                    }
                } finally {$source.Dispose();$target.Dispose()}
            } finally {$response.Dispose()}
            $expected = '9f28727e8b472a04c1d2e520aaa425dca82721b995139b35710091130ea6e699'
            if ((Get-FileHash -Algorithm SHA256 $archive).Hash.ToLowerInvariant() -ne $expected) {
                throw 'FFmpeg archive SHA-256 mismatch. Nothing will be installed.'
            }
            Expand-Archive -LiteralPath $archive -DestinationPath (Join-Path $tempRoot 'unpacked')
            $build = Join-Path $tempRoot 'unpacked\ffmpeg-7.1.1-full_build-shared'
            New-Item -ItemType Directory -Path $prefix -Force | Out-Null
            Copy-Item -Path (Join-Path $build '*') -Destination $prefix -Recurse -Force
        } finally {
            Remove-Item -LiteralPath $tempRoot -Recurse -Force
        }
    }
    $env:EWP_FFMPEG_PREFIX = $prefix
    Write-SetupPhase 'verify' 'Checking installed native runtime'
    $env:PATH = (Join-Path $prefix 'bin') + ';' + $env:PATH
    if ($SetupModels) {
        $modelArgs = @('run', '--locked', '--no-sync', 'python', 'scripts/setup-models.py')
        if ($PublicOnly) { $modelArgs += '--public-only' }
        & uv @modelArgs
        if ($LASTEXITCODE -ne 0) { throw 'Explicit model setup failed.' }
    }
    $report = & uv run --locked --no-sync transcriber doctor --test-speech-runtime --json-output
    $doctorExit = $LASTEXITCODE
    if ($doctorExit -notin @(0, 3)) { throw 'Dependency diagnostics failed.' }
    $report | Write-Output
    $diagnostics = ($report -join "`n") | ConvertFrom-Json
    $ignored = @('*_model'); if ($CloudOnly) { $ignored += @('gpu', 'cuda', 'speech_runtime') }
    $failedRuntime = @($diagnostics.checks | Where-Object { $code=$_.code; $_.status -eq 'fail' -and !(@($ignored | Where-Object { $code -like $_ }).Count) })
    if ($failedRuntime.Count -gt 0) { throw 'Runtime checks failed. Follow Instructions/WINDOWS_NATIVE.md before local ASR.' }
    Write-Host 'Setup finished. Check doctor results; prepare missing models before local ASR.'
    Write-Host 'Start: uv run --locked transcriber gui'
} finally {
    Pop-Location
}
