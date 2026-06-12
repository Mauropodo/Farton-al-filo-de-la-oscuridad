param([string]$VaultPath = $PWD.Path)

$obsidian = Join-Path $VaultPath ".obsidian"
$dataPath = Join-Path $obsidian "plugins\obsidian-icon-folder\data.json"
$graphPath = Join-Path $obsidian "graph.json"
$cssPath = Join-Path $obsidian "snippets\colores-carpetas.css"

Write-Host "=== Sincronizando colores desde Iconize ===" -ForegroundColor Cyan

if (-not (Test-Path $dataPath)) { Write-Host "ERROR: no se encuentra data.json" -ForegroundColor Red; exit 1 }

# Leer data.json
$data = Get-Content $dataPath -Raw | ConvertFrom-Json

# Extraer folders con color (excluir 'settings', solo entries con iconColor)
$folders = @()
foreach ($prop in $data.PSObject.Properties) {
  if ($prop.Name -eq "settings") { continue }
  $val = $prop.Value
  if ($val -is [PSCustomObject] -and $val.iconColor) {
    $folders += [PSCustomObject]@{ name=$prop.Name; color=$val.iconColor }
  }
}

$folders = $folders | Sort-Object Name

if ($folders.Count -eq 0) {
  Write-Host "ERROR: ningun folder tiene color asignado en Iconize" -ForegroundColor Red
  exit 1
}

Write-Host "Folders con color: $($folders.Count)" -ForegroundColor Green
foreach ($f in $folders) { Write-Host "  $($f.name) -> $($f.color)" }

function Hex2RgbInt($hex) {
  $h = $hex.Trim('#')
  return ([Convert]::ToInt32($h.Substring(0,2),16) -shl 16) -bor ([Convert]::ToInt32($h.Substring(2,2),16) -shl 8) -bor [Convert]::ToInt32($h.Substring(4,2),16)
}

# Generar grupos JSON manualmente (2-space indent para Obsidian)
$groupLines = @()
$cssBlocks = @()
foreach ($f in $folders) {
  $rgb = Hex2RgbInt $f.color
  $groupLines += "    {
      `"query`": `"path:$($f.name)`",
      `"color`": {
        `"a`": 1,
        `"rgb`": $rgb
      }
    }"
  $cssBlocks += "/* $($f.name) */
.nav-folder-title[data-path^=`"$($f.name)`"] .nav-folder-title-content,
.nav-file-title[data-path^=`"$($f.name)/`"] .nav-file-title-content {
  color: $($f.color) !important;
}"
}

# Escribir graph.json
$graphJson = @"
{
  "collapse-filter": false,
  "search": "",
  "showTags": true,
  "showAttachments": true,
  "hideUnresolved": true,
  "showOrphans": false,
  "collapse-color-groups": false,
  "colorGroups": [
$($groupLines -join ",`r`n")
  ],
  "collapse-display": true,
  "showArrow": false,
  "textFadeMultiplier": 0,
  "nodeSizeMultiplier": 1,
  "lineSizeMultiplier": 1,
  "collapse-forces": true,
  "centerStrength": 0.518713248970312,
  "repelStrength": 10,
  "linkStrength": 1,
  "linkDistance": 250,
  "scale": 1.5,
  "close": false
}
"@
Set-Content -Path $graphPath -Value $graphJson -Encoding UTF8
Write-Host "OK graph.json" -ForegroundColor Green

# Escribir CSS
Set-Content -Path $cssPath -Value ($cssBlocks -join "`r`n`r`n") -Encoding UTF8
Write-Host "OK colores-carpetas.css" -ForegroundColor Green

Write-Host ""
Write-Host "=== COMPLETADO ===" -ForegroundColor Cyan
Write-Host "data.json NO fue modificado (solo lectura)"
Write-Host ""
Write-Host "Pasos en Obsidian:"
Write-Host "  1. Settings > Apariencia > CSS snippets > Recargar"
Write-Host "  2. Vista Grafica > engranaje > expandir 'Color Groups'"
Write-Host "  3. Si no aparecen los grupos, reiniciar Obsidian"
