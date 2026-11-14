Add-Type -AssemblyName System.Drawing
$root = Join-Path (Get-Location) 'results/blind_test'
$out = Join-Path $root 'video_frames'
New-Item -ItemType Directory -Path $out -Force | Out-Null
$pred = Import-Csv (Join-Path $root 'predictions.csv')
$scored = Import-Csv (Join-Path $root 'scored_predictions.csv')
$answer = Import-Csv (Join-Path (Get-Location) 'blind_test_data/answer_key_checked.csv')
$fontTitle = New-Object System.Drawing.Font('Microsoft YaHei', 30, [System.Drawing.FontStyle]::Bold)
$fontSub = New-Object System.Drawing.Font('Microsoft YaHei', 19)
$fontRow = New-Object System.Drawing.Font('Consolas', 17)
$fontSmall = New-Object System.Drawing.Font('Microsoft YaHei', 15)
$white = [System.Drawing.Brushes]::White
$muted = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(185,201,225))
$accent = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(85,185,255))
$green = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(85,220,165))
$red = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255,130,130))
function New-Slide($name,$title,$subtitle) {
  $bmp = New-Object System.Drawing.Bitmap(1280,720)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $g.Clear([System.Drawing.Color]::FromArgb(16,25,43))
  $g.DrawString($title,$fontTitle,$white,55,35)
  $g.DrawString($subtitle,$fontSub,$muted,58,105)
  return @{Bitmap=$bmp;Graphics=$g;Name=$name}
}
function Save-Slide($slide) {
  $slide.Graphics.DrawString('吹风机异常声振诊断  |  结果复现演示', $fontSmall, $muted, 55, 677)
  $slide.Bitmap.Save((Join-Path $out $slide.Name),[System.Drawing.Imaging.ImageFormat]::Png)
  $slide.Graphics.Dispose();$slide.Bitmap.Dispose()
}
$s=New-Slide '01_title.png' '吹风机项目三 · 盲测结果复现' '已保存的首次预测与答案核对；不是首次实时预测录屏'
$s.Graphics.DrawString('25 组新录制样本  /  五种工况各 5 组', $fontSub, $accent, 60, 245)
$s.Graphics.DrawString('固定模型：旧批次 50 组训练，16 项特征，3-NN', $fontSub, $white, 60, 305)
$s.Graphics.DrawString('先保存预测，再读取答案表核对', $fontSub, $white, 60, 365)
$s.Graphics.DrawString('首次盲测：9 / 25 = 36%', $fontTitle, $green, 60, 475)
Save-Slide $s
$s=New-Slide '02_method.png' '盲测流程' '展示已保存的证据文件与结果顺序'
$steps=@('1. 25 对新 WAV / CSV 文件：五种工况各 5 组','2. 预测阶段未读取答案表','3. predictions.csv 先保存全部 25 条预测','4. answer_key_checked.csv 后用于核对','5. scored_predictions.csv 与混淆矩阵记录所有错判')
for($i=0;$i -lt $steps.Count;$i++){$s.Graphics.DrawString($steps[$i],$fontSub,$white,65,(205+75*$i))}
$s.Graphics.DrawString('文件名本身含工况；此处展示软件预测与结果复核。',$fontSmall,$muted,65,605)
Save-Slide $s
$s=New-Slide '03_files.png' '25 对新样本文件' 'blind_test_data：每个编号均有对应 WAV 和 CSV'
for($i=0;$i -lt $answer.Count;$i++){
  $col=[Math]::Floor($i/13);$row=$i%13
  $x=55+620*$col;$y=170+36*$row
  $item=$answer[$i]
  $wav=Join-Path (Get-Location) ('blind_test_data/'+$item.wav_file)
  $csv=Join-Path (Get-Location) ('blind_test_data/'+$item.csv_file)
  $mark=if((Test-Path -LiteralPath $wav) -and (Test-Path -LiteralPath $csv)){'WAV + CSV'}else{'MISSING'}
  $s.Graphics.DrawString(($item.sample_id+'  '+$mark),$fontRow,$white,$x,$y)
}
Save-Slide $s
$s=New-Slide '03_predictions.png' '第一阶段：已保存的 25 条预测' 'predictions.csv 仅含 sample_id 与 predicted_condition'
for($i=0;$i -lt $pred.Count;$i++){
  $col=[Math]::Floor($i/13);$row=$i%13
  $x=55+620*$col;$y=170+36*$row
  $s.Graphics.DrawString(($pred[$i].sample_id+'  →  '+$pred[$i].predicted_condition),$fontRow,$white,$x,$y)
}
Save-Slide $s
$s=New-Slide '04_answer_key.png' '随后核对答案表' 'answer_key_checked.csv：sample_id 与 true_condition'
for($i=0;$i -lt $answer.Count;$i++){
  $col=[Math]::Floor($i/13);$row=$i%13
  $x=55+620*$col;$y=170+36*$row
  $item=$answer[$i]
  $s.Graphics.DrawString(($item.sample_id+'  =  '+$item.true_condition),$fontRow,$white,$x,$y)
}
Save-Slide $s
$s=New-Slide '04_scored.png' '第二阶段：核对真实工况' 'scored_predictions.csv 保留正确与错误的全部 25 条记录'
for($i=0;$i -lt $scored.Count;$i++){
  $col=[Math]::Floor($i/13);$row=$i%13
  $x=55+620*$col;$y=170+36*$row
  $item=$scored[$i];$brush=if($item.correct -eq '1'){$green}else{$red}
  $mark=if($item.correct -eq '1'){'OK'}else{'X '}
  $s.Graphics.DrawString(($mark+'  '+$item.sample_id+'  →  '+$item.predicted_condition),$fontRow,$brush,$x,$y)
}
Save-Slide $s
$s=New-Slide '05_report.png' '准确率报告' 'blind_accuracy_report.txt：原第一次盲测结果'
$report=Get-Content (Join-Path $root 'blind_accuracy_report.txt')
$shown=@($report | Where-Object { $_ -match 'Overall accuracy:|01_cold_low:|02_hot_low:|03_hot_high:|04_inlet_block:|05_outlet_block:' })
for($i=0;$i -lt $shown.Count;$i++){$s.Graphics.DrawString($shown[$i],$fontRow,$white,65,(200+60*$i))}
Save-Slide $s
$s=New-Slide '05_matrix.png' '五类混淆矩阵' '行是真实工况，列是预测工况；保留所有错判'
$matrix=[System.Drawing.Image]::FromFile((Join-Path $root 'blind_confusion_matrix.png'))
$s.Graphics.DrawImage($matrix,180,155,900,490)
$matrix.Dispose()
Save-Slide $s
$s=New-Slide '06_summary.png' '结果与限制' '首次新样本盲测成绩：9 / 25 = 36%'
$s.Graphics.DrawString('冷风低档 0/5   热风低档 3/5   热风高档 3/5', $fontSub, $white, 65, 225)
$s.Graphics.DrawString('进风口遮挡 1/5   出风口遮挡 2/5', $fontSub, $white, 65, 285)
$s.Graphics.DrawString('原预测与核对结果均已保存，未删除错判。', $fontSub, $accent, 65, 390)
$s.Graphics.DrawString('后续特征修正和加噪实验属于事后分析，非本次首次盲测。', $fontSmall, $muted, 65, 455)
$s.Graphics.DrawString('本片由已保存结果制作，为结果复现演示。', $fontSmall, $muted, 65, 510)
$s.Graphics.DrawString('固定模型先生成预测，再核对答案；25 组正确 9 组，准确率 36%。', $fontSmall, $accent, 65, 555)
Save-Slide $s
$fontTitle.Dispose();$fontSub.Dispose();$fontRow.Dispose();$fontSmall.Dispose();$muted.Dispose();$accent.Dispose();$green.Dispose();$red.Dispose()
Write-Output "Created six frames in $out"
