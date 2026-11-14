Add-Type -AssemblyName System.Drawing
$folder = Join-Path (Get-Location) 'results/blind_test'
$rows = Import-Csv (Join-Path $folder 'scored_predictions.csv')
$labels = @('01_cold_low','02_hot_low','03_hot_high','04_inlet_block','05_outlet_block')
$bmp = New-Object System.Drawing.Bitmap(1000, 680)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::White)
$title = New-Object System.Drawing.Font('Arial', 19, [System.Drawing.FontStyle]::Bold)
$body = New-Object System.Drawing.Font('Arial', 11)
$small = New-Object System.Drawing.Font('Arial', 10)
$pen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(70,70,70), 1)
$g.DrawString('New-recording blind test: 9/25 = 36%', $title, [System.Drawing.Brushes]::Black, 25, 20)
$g.DrawString('Rows = actual; columns = predicted; five recordings per condition', $body, [System.Drawing.Brushes]::Gray, 25, 60)
for ($i=0; $i -lt 5; $i++) {
  $g.DrawString($labels[$i], $small, [System.Drawing.Brushes]::Black, 30, (190 + 83*$i))
  $g.DrawString($labels[$i], $small, [System.Drawing.Brushes]::Black, (315 + 130*$i), 140)
  for ($j=0; $j -lt 5; $j++) {
    $count = @($rows | Where-Object { $_.true_condition -eq $labels[$i] -and $_.predicted_condition -eq $labels[$j] }).Count
    $shade = [Math]::Max(65, 245 - 34*$count)
    $brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb($shade, $shade, 255))
    $x = 310 + 130*$j; $y = 175 + 83*$i
    $g.FillRectangle($brush, $x, $y, 115, 70)
    $g.DrawRectangle($pen, $x, $y, 115, 70)
    $g.DrawString([string]$count, $title, [System.Drawing.Brushes]::Black, ($x+47), ($y+20))
    $brush.Dispose()
  }
}
$bmp.Save((Join-Path $folder 'blind_confusion_matrix.png'), [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose(); $title.Dispose(); $body.Dispose(); $small.Dispose(); $pen.Dispose()
Write-Output 'Created blind_confusion_matrix.png'
