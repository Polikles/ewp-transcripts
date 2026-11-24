# Works from an extracted versioned bundle or a managed installation. No secrets in argv.
[CmdletBinding()]
param(
 [ValidateSet('check','verify-models','models','install','update','repair','rollback','launch','uninstall')][string]$Action='install',
 [string]$Root='',
 [string]$Bundle='', [string]$CancelFile='', [switch]$Local, [switch]$CloudOnly, [switch]$AcceptModelTerms, [switch]$Yes,
 [switch]$RemoveModels, [switch]$RemoveKey, [switch]$SaveOpenRouterKey, [switch]$SecretsStdin,
 [string]$Models='', [switch]$Redownload
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
[Console]::OutputEncoding=New-Object Text.UTF8Encoding $false
$env:PYTHONIOENCODING='utf-8'
if(!$Root){
 if(Test-Path -LiteralPath (Join-Path $PSScriptRoot 'owner.json')){$Root=$PSScriptRoot}
 else{$Root=Join-Path $env:LOCALAPPDATA 'EwPTranscripts'}
}
$manager=Join-Path $PSScriptRoot 'manager.py'
$argsToManager=@($manager,$Action,'--root',$Root)
if($Bundle){$argsToManager+=@('--bundle',(Resolve-Path -LiteralPath $Bundle).Path)}
if($CancelFile){$argsToManager+=@('--cancel-file',$CancelFile)}
foreach($model in $Models.Split(',',[StringSplitOptions]::RemoveEmptyEntries)){$argsToManager+=@('--model',$model)}
if($Redownload){$argsToManager+='--redownload'}
foreach($pair in @(@($Local,'--local'),@($CloudOnly,'--cloud-only'),@($AcceptModelTerms,'--accept-model-terms'),@($Yes,'--yes'),@($RemoveModels,'--remove-models'),@($RemoveKey,'--remove-key'),@($SecretsStdin,'--secrets-stdin'),@($SaveOpenRouterKey,'--save-openrouter-key'))){if($pair[0]){$argsToManager+=$pair[1]}}
$secretLine=if($SecretsStdin){[Console]::ReadLine()}else{$null}
$statePath=Join-Path $Root 'installation.json'
$useInstalled=$false
if((Test-Path -LiteralPath $statePath) -and $Action -in @('uninstall','rollback','launch','verify-models','models')){
 $state=Get-Content -Encoding UTF8 -LiteralPath $statePath -Raw|ConvertFrom-Json
 if($state.kind -ne 'ewp-transcripts-managed-v1' -or $state.active -notmatch '^versions[\\/][a-zA-Z0-9.\-]+$'){throw 'Invalid installation inventory'}
 $python=Join-Path $Root ($state.active+'\app\.venv\Scripts\python.exe')
 $useInstalled=$true
 if($Action -eq 'uninstall'){
  # A prior partial removal may have deleted the app interpreter or its managed base runtime.
  $useInstalled=$false
  if(Test-Path -LiteralPath $python){
   try{& $python -I -c 'import sys' 2>$null;$useInstalled=$LASTEXITCODE -eq 0}catch{}
  }
 }
}
if($useInstalled){
 if($SecretsStdin){$secretLine | & $python @argsToManager}else{& $python @argsToManager}
}else{
 if(Test-Path -LiteralPath (Join-Path $PSScriptRoot 'owner.json')){$uv=Join-Path $PSScriptRoot 'tools\uv.exe'}else{$uv=Join-Path (Split-Path -Parent $PSScriptRoot) 'tools\uv.exe'}
 if(!(Test-Path -LiteralPath $uv)){throw 'Extract the complete installer bundle; bundled uv.exe is missing.'}
 # Installer runtime is private, outside the destination so an empty-root guard is meaningful.
 $ownedRuntime=!$env:EWP_BOOTSTRAP_RUNTIME
 $runtime=if($ownedRuntime){Join-Path ([IO.Path]::GetTempPath()) ('ewp-bootstrap-'+[Guid]::NewGuid())}else{$env:EWP_BOOTSTRAP_RUNTIME}
 $env:UV_PYTHON_INSTALL_DIR=Join-Path $runtime 'python'
 $env:UV_CACHE_DIR=Join-Path $runtime 'cache'
 $env:UV_NO_CONFIG='1'
 $uvArgs=@('run','--no-project','--python','3.12','python')+$argsToManager
 try{if($SecretsStdin){$secretLine | & $uv @uvArgs}else{& $uv @uvArgs};$resultCode=$LASTEXITCODE}
 finally{if($ownedRuntime -and (Test-Path -LiteralPath $runtime)){Remove-Item -LiteralPath $runtime -Recurse -Force}}
 exit $resultCode
}
$secretLine=$null
exit $LASTEXITCODE
