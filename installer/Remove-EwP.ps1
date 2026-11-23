# Deferred removal runs outside the application after its interpreter/wizard releases Windows files.
param([Parameter(Mandatory=$true)][string]$Plan)
$ErrorActionPreference='Stop'
$p=Get-Content -LiteralPath $Plan -Raw|ConvertFrom-Json
try {
 foreach($idToWait in $p.pids){Wait-Process -Id $idToWait -ErrorAction SilentlyContinue}
 $prefix=[IO.Path]::GetFullPath($p.root).TrimEnd('\')+'\'
 foreach($target in $p.paths){
  $full=[IO.Path]::GetFullPath($target)
  if(!$full.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Removal path escaped installation'}
  if(Test-Path -LiteralPath $full){
   $item=Get-Item -LiteralPath $full -Force
   if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){continue}
   if($item.PSIsContainer){[IO.Directory]::Delete($full,$true)}else{[IO.File]::Delete($full)}
  }
 }
 function Remove-EmptyOwnedDirectories([string]$Folder){
  if(!(Test-Path -LiteralPath $Folder)){return}
  $item=Get-Item -LiteralPath $Folder -Force
  if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){return}
  foreach($directory in [IO.Directory]::EnumerateDirectories($Folder)){Remove-EmptyOwnedDirectories $directory}
  if(!@([IO.Directory]::EnumerateFileSystemEntries($Folder)).Count){[IO.Directory]::Delete($Folder)}
 }
 Remove-EmptyOwnedDirectories (Join-Path $p.root 'versions')
 if((Test-Path -LiteralPath $p.root) -and !@([IO.Directory]::EnumerateFileSystemEntries($p.root)).Count){[IO.Directory]::Delete($p.root)}
 Remove-Item -LiteralPath $PSScriptRoot -Recurse -Force
} catch {
 # Keep a content-free path/error report if locked files or disk problems prevent final removal.
 $_.Exception.GetType().FullName | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'removal-error.txt')
 exit 2
}
