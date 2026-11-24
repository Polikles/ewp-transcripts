# User entry point and deferred worker. Internal plans are created only by manager.py.
[CmdletBinding()]
param([string]$Plan='', [string]$Root=$PSScriptRoot, [switch]$Yes,
      [switch]$RemoveModels, [switch]$RemoveKey)
$ErrorActionPreference='Stop'
if(!$Plan){
 try {
  $wizard=Join-Path $Root 'uninstall.exe'
  if((Test-Path -LiteralPath $wizard) -and !$Yes -and !$RemoveModels -and !$RemoveKey){
   Start-Process -FilePath $wizard
   exit 0
  }
  $arguments=@('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $Root 'Install-EwP.ps1'),'-Action','uninstall','-Root',$Root)
  if(!$Yes){
   & powershell.exe @arguments
   if($LASTEXITCODE -ne 0){throw 'Cannot prepare removal preview'}
   if((Read-Host 'Remove EwP program files? / Usunac pliki programu? [y/N]') -ne 'y'){exit 0}
  }
  $arguments+='-Yes'
  if($RemoveModels){$arguments+='-RemoveModels'}
  if($RemoveKey){$arguments+='-RemoveKey'}
  & powershell.exe @arguments
  exit $LASTEXITCODE
 } catch {
  Write-Host $_.Exception.Message -ForegroundColor Red
  Read-Host 'Press Enter to close / Nacisnij Enter, aby zamknac'
  exit 2
 }
}
$p=Get-Content -Encoding UTF8 -LiteralPath $Plan -Raw|ConvertFrom-Json
$errorsFound=[Collections.Generic.List[string]]::new()
function Assert-NotLinked([string]$Path){
 if((Get-Item -LiteralPath $Path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked removal target preserved'}
}
function Remove-OwnedTree([string]$Path){
 if(!(Test-Path -LiteralPath $Path)){return}
 $item=Get-Item -LiteralPath $Path -Force
 if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){
  if($item.PSIsContainer){[IO.Directory]::Delete($Path,$false)}else{[IO.File]::Delete($Path)}
  return
 }
 if($item.PSIsContainer){
  foreach($child in [IO.Directory]::EnumerateFileSystemEntries($Path)){Remove-OwnedTree $child}
  [IO.File]::SetAttributes($Path,[IO.FileAttributes]::Directory)
  [IO.Directory]::Delete($Path)
 }else{
  # uv dependency caches/venvs contain read-only hardlinks. Clear attributes before deletion.
  [IO.File]::SetAttributes($Path,[IO.FileAttributes]::Normal)
  [IO.File]::Delete($Path)
 }
}
function Remove-EmptyOwnedDirectories([string]$Folder){
 if(!(Test-Path -LiteralPath $Folder)){return}
 Assert-NotLinked $Folder
 foreach($directory in [IO.Directory]::EnumerateDirectories($Folder)){Remove-EmptyOwnedDirectories $directory}
 if(!@([IO.Directory]::EnumerateFileSystemEntries($Folder)).Count){[IO.Directory]::Delete($Folder)}
}
try {
 foreach($idToWait in $p.pids){Wait-Process -Id $idToWait -ErrorAction SilentlyContinue}
 $prefix=[IO.Path]::GetFullPath($p.root).TrimEnd('\')+'\'
 Assert-NotLinked $p.root
 $ownerPath=Join-Path $p.root 'owner.json'
 $owner=Get-Content -Encoding UTF8 -LiteralPath $ownerPath -Raw|ConvertFrom-Json
 if($owner.kind -ne 'ewp-transcripts-managed-v1' -or $owner.root -ne $p.root -or $owner.id -ne $p.owner_id){throw 'Installation ownership changed'}
 foreach($target in $p.paths){
  $full=[IO.Path]::GetFullPath($target)
  if(!$full.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Removal path escaped installation'}
  $ancestor=[IO.Path]::GetDirectoryName($full)
  while($ancestor -and $ancestor.Length -ge $prefix.TrimEnd('\').Length){Assert-NotLinked $ancestor;$ancestor=[IO.Path]::GetDirectoryName($ancestor)}
 }
 foreach($target in $p.paths){
  if([IO.Path]::GetFileName($target) -eq 'owner.json'){continue}
  $removed=$false
  for($attempt=0;$attempt -lt 4 -and !$removed;$attempt++){
   try {Remove-OwnedTree $target;$removed=$true}
   catch {if($attempt -lt 3){Start-Sleep -Milliseconds 500}else{$errorsFound.Add($target+': '+$_.Exception.GetType().FullName)}}
  }
 }
 if($errorsFound.Count){throw 'Some owned files could not be removed; see removal-error.txt'}
 Remove-OwnedTree $ownerPath
 Remove-EmptyOwnedDirectories (Join-Path $p.root 'versions')
 $reg='HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\EwPTranscripts'
 if((Test-Path $reg) -and (Get-ItemProperty $reg).InstallLocation -eq $p.root){Remove-Item $reg}
 $w=New-Object -ComObject WScript.Shell
 $shortcut=Join-Path ([Environment]::GetFolderPath('Desktop')) 'EwP Transcripts.lnk'
 if(Test-Path -LiteralPath $shortcut){
  $s=$w.CreateShortcut($shortcut)
  if($s.TargetPath -eq (Join-Path $p.root 'EwP.cmd') -or $s.Arguments -eq ('-NoProfile -ExecutionPolicy Bypass -File "'+(Join-Path $p.root 'launch.ps1')+'"')){Remove-Item -LiteralPath $shortcut -Force}
 }
 if((Test-Path -LiteralPath $p.root) -and !@([IO.Directory]::EnumerateFileSystemEntries($p.root)).Count){[IO.Directory]::Delete($p.root)}
 Remove-Item -LiteralPath $PSScriptRoot -Recurse -Force
} catch {
 $stamp=[DateTimeOffset]::UtcNow.ToString('o')
 @($stamp,$_.Exception.GetType().FullName,$errorsFound) | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'removal-error.txt')
 exit 2
}
