# Clear all Python cache
Write-Host "[*] Clearing Python cache..."
Get-ChildItem -Path "..\breeding_vat" -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
}

# Clear Streamlit cache (multiple possible locations)
Write-Host "[*] Clearing Streamlit cache..."
$streamlitPaths = @(
    "$env:APPDATA\.streamlit",
    "$HOME\.streamlit",
    ".\.streamlit",
    "~\.streamlit"
)

foreach ($path in $streamlitPaths) {
    $expandedPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($path)
    if (Test-Path $expandedPath -ErrorAction SilentlyContinue) {
        Remove-Item -Path $expandedPath -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "[✓] Cleared: $expandedPath"
    }
}

# Stop any existing containers
Write-Host "[*] Stopping existing UI containers..."
docker ps -a --filter "ancestor=breeding-vat-ui:latest" --format "{{.ID}}" | ForEach-Object {
    docker stop $_ 2>&1 | Out-Null
    docker rm $_ 2>&1 | Out-Null
    Write-Host "[✓] Removed container"
}

Write-Host "[✓] Cache cleared. Restart with: run.bat"
