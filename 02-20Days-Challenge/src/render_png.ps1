Add-Type -AssemblyName System.Drawing
$outputDir = Join-Path (Get-Location) 'results/classification'
$rows = Import-Csv (Join-Path $outputDir 'test_predictions.csv')
$features = Import-Csv (Join-Path (Get-Location) 'results/features/features_corrected.csv')
$labels = @('01_cold_low','02_hot_low','03_hot_high','04_inlet_block','05_outlet_block')
$font = New-Object System.Drawing.Font('Arial', 12)
$small = New-Object System.Drawing.Font('Arial', 10)
$title = New-Object System.Drawing.Font('Arial', 19, [System.Drawing.FontStyle]::Bold)
$black = [System.Drawing.Brushes]::Black
$gray = [System.Drawing.Brushes]::Gray
$pen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(60,60,60), 1)

$bmp = New-Object System.Drawing.Bitmap(1000, 680)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::White)
$g.DrawString('Held-out confusion matrix', $title, $black, 25, 20)
$g.DrawString('Rows = actual; columns = predicted; five held-out recordings per condition', $font, $gray, 25, 58)
for ($i=0; $i -lt 5; $i++) {
  $g.DrawString($labels[$i], $small, $black, 30, (190 + 83*$i))
  $g.DrawString($labels[$i], $small, $black, (315 + 130*$i), 140)
  for ($j=0; $j -lt 5; $j++) {
    $count = @($rows | Where-Object { $_.true_condition -eq $labels[$i] -and $_.predicted_condition -eq $labels[$j] }).Count
    $shade = [Math]::Max(65, 245 - 34*$count)
    $brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb($shade, $shade, 255))
    $x = 310 + 130*$j; $y = 175 + 83*$i
    $g.FillRectangle($brush, $x, $y, 115, 70)
    $g.DrawRectangle($pen, $x, $y, 115, 70)
    $g.DrawString([string]$count, $title, $black, ($x+47), ($y+20))
    $brush.Dispose()
  }
}
$bmp.Save((Join-Path $outputDir 'confusion_matrix.png'), [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

$plotNames = @('audio_rms','audio_zero_crossing_rate','audio_dominant_hz','audio_band_1000_4000_fraction','accel_rms','accel_dominant_hz')
$colors = @([System.Drawing.Color]::RoyalBlue,[System.Drawing.Color]::DarkOrange,[System.Drawing.Color]::Firebrick,[System.Drawing.Color]::SeaGreen,[System.Drawing.Color]::Purple)
$bmp = New-Object System.Drawing.Bitmap(1200, 1050)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::White)
$g.DrawString('Feature distributions by condition', $title, $black, 25, 15)
$g.DrawString('Box = middle 50%; center line = median; whiskers = minimum and maximum; 15 recordings per condition', $small, $gray, 25, 50)
for ($p=0; $p -lt 6; $p++) {
  $name = $plotNames[$p]
  $baseX = 25 + 590*($p % 2); $baseY = 90 + 315*[Math]::Floor($p/2)
  $g.DrawString($name, $font, $black, $baseX, $baseY)
  $all = @($features | ForEach-Object { [double]($_.$name) } | Sort-Object)
  $min = $all[0]; $max = $all[$all.Count-1]; $span = $max-$min
  if ($span -eq 0) { $span=1 }
  for ($i=0; $i -lt 5; $i++) {
    $vals = @($features | Where-Object { $_.condition -eq $labels[$i] } | ForEach-Object { [double]($_.$name) } | Sort-Object)
    $x = { param($v) [int]($baseX + 175 + 365*($v-$min)/$span) }
    $y = [int]($baseY + 42 + 42*$i)
    $colorPen = New-Object System.Drawing.Pen($colors[$i], 2)
    $colorBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(80,$colors[$i]))
    $v0 = & $x $vals[0]; $v1 = & $x $vals[3]; $vm = & $x $vals[7]; $v3 = & $x $vals[11]; $v4 = & $x $vals[14]
    $g.DrawString($labels[$i], $small, $black, $baseX, ($y-8))
    $g.DrawLine($colorPen, $v0, $y, $v4, $y)
    $g.FillRectangle($colorBrush, $v1, ($y-9), [Math]::Max(1,$v3-$v1), 18)
    $g.DrawRectangle($colorPen, $v1, ($y-9), [Math]::Max(1,$v3-$v1), 18)
    $g.DrawLine($colorPen, $vm, ($y-10), $vm, ($y+10))
    $colorPen.Dispose(); $colorBrush.Dispose()
  }
  $g.DrawString(('{0:G4}' -f $min), $small, $gray, ($baseX+175), ($baseY+260))
  $g.DrawString(('{0:G4}' -f $max), $small, $gray, ($baseX+490), ($baseY+260))
}
$bmp.Save((Join-Path $outputDir 'feature_distributions.png'), [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
$font.Dispose(); $small.Dispose(); $title.Dispose(); $pen.Dispose()
Write-Output 'Created confusion_matrix.png and feature_distributions.png'
