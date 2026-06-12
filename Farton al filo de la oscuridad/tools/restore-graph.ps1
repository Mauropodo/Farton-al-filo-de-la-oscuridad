param([string]$VaultPath = $PWD.Path)

# Restaura solo graph.json desde los colores de Iconize
# Ejecutar con Obsidian CERRADO

$obsidian = Join-Path $VaultPath ".obsidian"
$dataPath = Join-Path $obsidian "plugins\obsidian-icon-folder\data.json"
$graphPath = Join-Path $obsidian "graph.json"

if (-not (Test-Path $dataPath)) { Write-Host "ERROR: no se encuentra data.json" -ForegroundColor Red; exit 1 }

$data = Get-Content $dataPath -Raw | ConvertFrom-Json
$folders = @()
foreach ($prop in $data.PSObject.Properties) {
  if ($prop.Name -eq "settings") { continue }
  $val = $prop.Value
  if ($val -is [PSCustomObject] -and $val.iconColor) {
    $folders += [PSCustomObject]@{ name=$prop.Name; color=$val.iconColor }
  }
}
$folders = $folders | Sort-Object Name

function Hex2RgbInt($hex) {
  $h = $hex.Trim('#')
  return ([Convert]::ToInt32($h.Substring(0,2),16) -shl 16) -bor ([Convert]::ToInt32($h.Substring(2,2),16) -shl 8) -bor [Convert]::ToInt32($h.Substring(4,2),16)
}

$groupLines = @()
foreach ($f in $folders) {
  $groupLines += "    {
      `"query`": `"path:$($f.name)`",
      `"color`": {
        `"a`": 1,
        `"rgb`": $(Hex2RgbInt $f.color)
      }
    }"
}

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
Write-Host "OK graph.json restaurado con $($folders.Count) grupos de color" -ForegroundColor Green
Write-Host "Ahora abre Obsidian y revisa la Vista Grafica."
