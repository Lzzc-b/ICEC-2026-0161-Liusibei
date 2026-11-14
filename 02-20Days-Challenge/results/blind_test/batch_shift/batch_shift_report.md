# 新旧批次特征差异

旧批次每类 15 组；新盲测批次每类 5 组。下表为中位数，不能单独证明差异原因。

| 工况 | 特征 | 旧批次 | 新批次 | 新中位数超出旧范围？ |
|---|---|---:|---:|---|
| 01_cold_low | audio_zero_crossing_rate | 0.1462 | 0.195 | yes |
| 01_cold_low | audio_band_1000_4000_fraction | 0.5437 | 0.4434 | yes |
| 01_cold_low | accel_zero_crossing_rate | 0.1501 | 0.1229 | no |
| 01_cold_low | accel_band_0_5_fraction | 0.6639 | 0.8977 | yes |
| 01_cold_low | accel_band_5_15_fraction | 0.1811 | 0.06157 | yes |
| 02_hot_low | audio_zero_crossing_rate | 0.1692 | 0.1851 | yes |
| 02_hot_low | audio_band_1000_4000_fraction | 0.5192 | 0.4532 | yes |
| 02_hot_low | accel_zero_crossing_rate | 0.2834 | 0.1626 | no |
| 02_hot_low | accel_band_0_5_fraction | 0.5193 | 0.719 | no |
| 02_hot_low | accel_band_5_15_fraction | 0.1848 | 0.1105 | yes |
| 03_hot_high | audio_zero_crossing_rate | 0.1721 | 0.1846 | no |
| 03_hot_high | audio_band_1000_4000_fraction | 0.482 | 0.4523 | no |
| 03_hot_high | accel_zero_crossing_rate | 0.2632 | 0.2243 | no |
| 03_hot_high | accel_band_0_5_fraction | 0.5279 | 0.5924 | no |
| 03_hot_high | accel_band_5_15_fraction | 0.1895 | 0.2677 | no |
| 04_inlet_block | audio_zero_crossing_rate | 0.1623 | 0.1919 | yes |
| 04_inlet_block | audio_band_1000_4000_fraction | 0.5069 | 0.4379 | no |
| 04_inlet_block | accel_zero_crossing_rate | 0.3208 | 0.192 | yes |
| 04_inlet_block | accel_band_0_5_fraction | 0.3564 | 0.6245 | yes |
| 04_inlet_block | accel_band_5_15_fraction | 0.3166 | 0.2463 | yes |
| 05_outlet_block | audio_zero_crossing_rate | 0.1648 | 0.1835 | yes |
| 05_outlet_block | audio_band_1000_4000_fraction | 0.5356 | 0.4903 | yes |
| 05_outlet_block | accel_zero_crossing_rate | 0.2946 | 0.172 | yes |
| 05_outlet_block | accel_band_0_5_fraction | 0.4282 | 0.6633 | yes |
| 05_outlet_block | accel_band_5_15_fraction | 0.2541 | 0.2097 | no |

## 观察

- 冷风低档、热风低档、进风遮挡、出风遮挡的新批次音频过零率中位数均高于各自旧批次最大值或接近其上界；新旧声音特征分布发生变化。
- 冷风低档、热风低档及出风遮挡的 1–4 kHz 音频能量占比下降。
- 两种遮挡工况的新批次加速度过零率降低，0–5 Hz 能量占比提高，说明振动特征也有批次变化。
- 这些变化与盲测准确率下降相符，但不能仅凭特征判断是摆放、环境噪声、设备状态还是标签问题。

## 后续处理

1. 保存原 9/25 盲测结果，不修改或覆盖。
2. 核对原始照片/视频与录制操作；检查手机距离、朝向、背景噪声、吹风机型号和预热时长。检查表中的“是/照片/视频”依据来自实验者填写，本分析没有独立验证媒体内容。
3. 若工况确实正确，使用旧批次训练并把新批次作为独立测试的失败案例分析；改进特征或采集流程后，另录新的样本评估改进效果。
4. 抗噪报告应先以当前固定模型做噪声扰动实验，分别报告原始与加噪准确率；不要把加噪样本当作新的独立录制。
