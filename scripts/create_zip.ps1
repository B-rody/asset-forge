$ErrorActionPreference = "Stop"

$outputDir = "dist"
$stagingDir = "dist/AssetFurnace"
$zipFile = "$outputDir/AssetFurnace-Portable.zip"

# Clean up previous build
if (Test-Path $outputDir) { Remove-Item $outputDir -Recurse -Force }

# Create directories
New-Item -ItemType Directory -Path $stagingDir -Force | Out-Null

# Copy Executable
Write-Host "Copying AssetFurnace.exe..."
Copy-Item "src-tauri/target/release/AssetFurnace.exe" -Destination $stagingDir

# Copy Backend (main.dist)
# Tauri places resources in the same directory as the executable on Windows
Write-Host "Copying backend/bin/main.dist..."
Copy-Item "backend/bin/main.dist" -Destination "$stagingDir/main.dist" -Recurse

# Create ZIP
Write-Host "Creating $zipFile..."
Compress-Archive -Path "$stagingDir/*" -DestinationPath $zipFile

# Cleanup staging to leave only the ZIP
Remove-Item $stagingDir -Recurse -Force

Write-Host "Done! Portable ZIP created at $zipFile"
