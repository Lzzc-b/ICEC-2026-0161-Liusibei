"""Compare old training-session and new blind-session features descriptively.

Run: python src/compare_batches.py
"""

import csv
import statistics
from pathlib import Path

from train_classifier import FEATURES

OLD = Path("results/features/features_corrected.csv")
NEW = Path("results/blind_test/corrected_reanalysis/blind_features_corrected.csv")
OUT = Path("results/blind_test/batch_shift")
LABELS = ["01_cold_low", "02_hot_low", "03_hot_high",
          "04_inlet_block", "05_outlet_block"]


def load(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    old, new = load(OLD), load(NEW)
    OUT.mkdir(parents=True, exist_ok=True)
    comparisons = []
    for label in LABELS:
        a = [r for r in old if r["condition"] == label]
        b = [r for r in new if r["sample_id"].startswith(label + "_B")]
        if len(a) != 15 or len(b) != 5:
            raise ValueError(f"Unexpected sample count for {label}")
        for feature in FEATURES:
            x = [float(r[feature]) for r in a]
            y = [float(r[feature]) for r in b]
            old_median, new_median = statistics.median(x), statistics.median(y)
            comparisons.append({
                "condition": label,
                "feature": feature,
                "old_median": old_median,
                "new_median": new_median,
                "new_minus_old": new_median - old_median,
                "old_min": min(x),
                "old_max": max(x),
                "new_median_outside_old_range": "yes" if new_median < min(x) or new_median > max(x) else "no",
            })
    with (OUT / "batch_shift.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=comparisons[0])
        writer.writeheader()
        writer.writerows(comparisons)
    selected = ["audio_zero_crossing_rate", "audio_band_1000_4000_fraction",
                "accel_zero_crossing_rate", "accel_band_0_5_fraction",
                "accel_band_5_15_fraction"]
    lines = ["# 新旧批次特征差异", "",
             "旧批次每类 15 组；新盲测批次每类 5 组。下表为中位数，不能单独证明差异原因。",
             "", "| 工况 | 特征 | 旧批次 | 新批次 | 新中位数超出旧范围？ |",
             "|---|---|---:|---:|---|"]
    for label in LABELS:
        for feature in selected:
            row = next(r for r in comparisons if r["condition"] == label and r["feature"] == feature)
            lines.append(f"| {label} | {feature} | {row['old_median']:.4g} | {row['new_median']:.4g} | {row['new_median_outside_old_range']} |")
    lines += ["", "## 观察", "",
              "- 冷风低档、热风低档、进风遮挡、出风遮挡的新批次音频过零率中位数均高于各自旧批次最大值或接近其上界；新旧声音特征分布发生变化。",
              "- 冷风低档、热风低档及出风遮挡的 1–4 kHz 音频能量占比下降。",
              "- 两种遮挡工况的新批次加速度过零率降低，0–5 Hz 能量占比提高，说明振动特征也有批次变化。",
              "- 这些变化与盲测准确率下降相符，但不能仅凭特征判断是摆放、环境噪声、设备状态还是标签问题。", "",
              "## 后续处理", "",
              "1. 保存原 9/25 盲测结果，不修改或覆盖。",
              "2. 核对原始照片/视频与录制操作；检查手机距离、朝向、背景噪声、吹风机型号和预热时长。检查表中的“是/照片/视频”依据来自实验者填写，本分析没有独立验证媒体内容。",
              "3. 若工况确实正确，使用旧批次训练并把新批次作为独立测试的失败案例分析；改进特征或采集流程后，另录新的样本评估改进效果。",
              "4. 抗噪报告应先以当前固定模型做噪声扰动实验，分别报告原始与加噪准确率；不要把加噪样本当作新的独立录制。", ""]
    (OUT / "batch_shift_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT / 'batch_shift.csv'} and {OUT / 'batch_shift_report.md'}")


if __name__ == "__main__":
    main()
