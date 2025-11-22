# ==========================================
# CONFIGURATION
# ==========================================
$OutputFile = "Codebase_Map.txt"
$TargetExtension = "*.py"

# Folders to strictly IGNORE
$IgnoreList = @("venv", "__pycache__", ".git", ".idea", ".vscode", "site-packages", "node_modules", "cache", "bin", "obj", "Include", "Lib", "Scripts", "share")

# ==========================================
# HELPER FUNCTION: CUSTOM TREE GENERATOR
# ==========================================
function Show-SmartTree {
    param (
        [string]$Path,
        [string]$Indent = "",
        [bool]$IsLast = $true
    )

    $DirName = Split-Path $Path -Leaf
    
    # Use safe ASCII characters instead of special symbols
    $Marker = if ($IsLast) { "\--- " } else { "+--- " }
    
    if ($Indent -eq "") { 
        "$($DirName)" | Out-File -FilePath $OutputFile -Append -Encoding UTF8
    } else {
        "$Indent$Marker$($DirName)" | Out-File -FilePath $OutputFile -Append -Encoding UTF8
    }

    # Prepare indent for children
    $NextIndent = if ($Indent -eq "") { "" } else { $Indent + (if ($IsLast) { "    " } else { "|   " }) }

    try {
        $Items = Get-ChildItem -Path $Path -ErrorAction SilentlyContinue | Sort-Object { $_.PSIsContainer } -Descending
    } catch { return }

    # Filter out ignored folders
    $FilteredItems = @()
    foreach ($Item in $Items) {
        if ($Item.Name -in $IgnoreList) { continue }
        $FilteredItems += $Item
    }

    for ($i = 0; $i -lt $FilteredItems.Count; $i++) {
        $Item = $FilteredItems[$i]
        $IsLastItem = ($i -eq ($FilteredItems.Count - 1))

        if ($Item.PSIsContainer) {
            Show-SmartTree -Path $Item.FullName -Indent $NextIndent -IsLast $IsLastItem
        } else {
            $FileMarker = if ($IsLastItem) { "\--- " } else { "+--- " }
            "$NextIndent$FileMarker$($Item.Name)" | Out-File -FilePath $OutputFile -Append -Encoding UTF8
        }
    }
}

# ==========================================
# SCRIPT EXECUTION
# ==========================================

# 1. Cleanup
if (Test-Path $OutputFile) { Remove-Item $OutputFile }
Write-Host "Generating Smart Map..." -ForegroundColor Cyan

# 2. Generate Structure Header
$Header = @"
################################################################################
# DIRECTORY STRUCTURE (Smart Filtered)
################################################################################
"@
$Header | Out-File -FilePath $OutputFile -Encoding UTF8

# 3. Run Custom Tree Logic
Write-Host "Building Directory Tree (Skipping venv)..." -ForegroundColor Green
Show-SmartTree -Path (Get-Location).Path

# 4. Map File Contents
Write-Host "Mapping Python Files..." -ForegroundColor Green

# Get files recursively, but manually filter path to ensure we skip ignored folders
$Files = Get-ChildItem -Path . -Recurse -Filter $TargetExtension 

foreach ($File in $Files) {
    # Check if file path contains any ignored folder
    $PathParts = $File.FullName.Split([System.IO.Path]::DirectorySeparatorChar)
    $ShouldIgnore = $false
    foreach ($Part in $PathParts) {
        if ($Part -in $IgnoreList) {
            $ShouldIgnore = $true
            break
        }
    }
    
    if ($ShouldIgnore) { continue }
    if ($File.Name -eq $OutputFile) { continue }

    $Block = @"

################################################################################
# FILE START: $($File.FullName)
################################################################################

"@
    $Block | Out-File -FilePath $OutputFile -Append -Encoding UTF8
    Get-Content -Path $File.FullName | Out-File -FilePath $OutputFile -Append -Encoding UTF8
    
    $Footer = @"

# FILE END: $($File.Name)
################################################################################
"@
    $Footer | Out-File -FilePath $OutputFile -Append -Encoding UTF8
}

Write-Host "Success! Clean map saved to: $OutputFile" -ForegroundColor Yellow