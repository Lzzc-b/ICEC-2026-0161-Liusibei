# 项目三过程日志

- **项目**：吹风机异常声振诊断
- **设备**：智能手机（麦克风 + 加速度计）、吹风机
- **说明**：主体实验在 2026-11-14 一天内完成；2026-11-15 为文档整理与 AI 协作归档。不虚构额外实验日。

---

## 2026-11-14｜实验日

### 14:30–17:30｜正式采集（5 工况 × 15 组）

**内容**
- 确认 5 种工况并正式采集：
  - `01_cold_low`：冷风低档、无遮挡
  - `02_hot_low`：热风低档、无遮挡
  - `03_hot_high`：热风高档、无遮挡
  - `04_inlet_block`：进风口遮挡（冷风低档）
  - `05_outlet_block`：出风口遮挡（热风低档）
- 每种工况 15 组，共 75 组
- 每组保存 WAV（音频）与 CSV（加速度）
- 同步拍摄实验照片/短视频

**产出**
- `../吹风机实验_raw_data/`（含各工况 wav/csv 与 `photos/`）
- 工况说明写入 `../项目说明.md`

**问题与处理**
- 遮挡工况兼顾安全与可区分度，采用可控遮挡，避免长时间堵住风口过热

### 20:21–21:27｜特征提取与内部留出测试

**内容**
- 运行 `../src/extract_features.py` 提取时域/频域特征
- 运行 `../src/train_classifier.py`：每类 10 组训练、5 组测试
- 查看混淆矩阵与分类报告

**结果**
- 旧数据内部留出测试：**13/25 = 52.0%**
- 详见 `../results/classification/accuracy_report.txt`

**问题与处理**
- 发现加速度低频能量占比计算曾把 DC 频点放入分子、未放入分母
- 已修正，说明见 `../results/blind_test/corrected_reanalysis/corrected_reanalysis_report.md`

### 22:26–23:42｜新样本盲测与抗噪复盘

**内容**
- 另录 25 组新样本（每工况 5 组）到 `../blind_test_data/`
- 使用冻结基线模型先预测，再对照答案表评分
- 录制盲测相关视频
- 运行抗噪分析，整理批次偏移与复盘说明

**结果**
- 首次新样本盲测：**9/25 = 36.0%**
- 详见：
  - `../results/blind_test/blind_accuracy_report.txt`
  - `../results/blind_test/scored_predictions.csv`
  - `../results/blind_test/blind_confusion_matrix.png`
- 视频：
  - `../results/blind_test/actual_screen_recording.mp4`
  - `../results/blind_test/blind_test_video.mp4`
- 抗噪（事后分析）：原始 36% → 20 dB 32% → 10 dB 24% → 0 dB 20%  
  详见 `../results/noise_analysis/anti_noise_report.md`

**当日结论**
1. 数据采集与代码链路完整，可复现
2. 内部测试 52%，跨批次盲测 36%，模型对采集条件敏感
3. 不将事后修正结果称为第二次独立盲测；后续改进应另录未见过样本再评

---

## 2026-11-15｜文档整理与 AI 协作归档

**性质**：非新实验日

**内容**
- 更新 README 选题与项目说明表述
- 整理并上传 `../../03-AI-Collaboration/` 中的关键提问、排障记录与证据截图
- 规范化 AI 协作记录格式（提问、建议、本人判断、验证结果、复盘）
- 核对项目三交付说明，避免把内部测试 52% 误写成盲测准确率

**产出**
- `../../README.md` 更新
- `../../03-AI-Collaboration/` 对话记录与截图归档
- `../项目说明.md` 表述核对

**说明**
- 本日无新增原始 WAV/CSV 采集批次，不改变 11-14 盲测的 9/25 结果。
