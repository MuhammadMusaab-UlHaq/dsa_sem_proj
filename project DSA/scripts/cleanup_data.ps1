# Cleanup Script for NUST Navigation System
# Removes old data files to ensure fresh rebuild

Write-Host "=== NUST Navigation - Data Cleanup ===" -ForegroundColor Cyan
Write-Host ""

$dataFiles = @(
    "nodes.json",
    "edges.json", 
    "pois.json",
    "nust_raw.osm",
    "map.html"
)

$removed = 0
$notFound = 0

foreach ($file in $dataFiles) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "[DELETED] $file" -ForegroundColor Yellow
        $removed++
    } else {
        Write-Host "[SKIP] $file (not found)" -ForegroundColor Gray
        $notFound++
    }
}

Write-Host ""
Write-Host "Cleanup Complete:" -ForegroundColor Green
Write-Host "  - Files Removed: $removed" -ForegroundColor Green
Write-Host "  - Files Not Found: $notFound" -ForegroundColor Gray
Write-Host ""
Write-Host "Ready for fresh data pipeline run!" -ForegroundColor Cyan
