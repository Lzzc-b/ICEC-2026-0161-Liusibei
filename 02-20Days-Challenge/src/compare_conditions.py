"""Descriptive matched-setting comparisons; no model fitting or test scoring.

Run: python src/compare_conditions.py
"""

import csv
import statistics
from pathlib import Path

SOURCE = Path("results/features/features.csv")
OUT = Path("results/condition_comparison")
PAIRS = [
    ("01_cold_low", "04_inlet_block", "冷风低档：进风口遮挡"),
    ("02_hot_low", "05_outlet_block", "热风低档：出风口遮挡"),
    ("02_hot_low", "03_hot_high", "热风低档与热风高档：档位变化"),
]
FEATURES = [
    "audio_rms", "audio_crest_factor", "audio_zero_crossing_rate",
    "audio_dominant_hz", "audio_band_0_200_fraction",
    "audio_band_200_1000_fraction", "audio_band_1000_4000_fraction",
    "audio_band_4000_10000_fraction", "accel_rms", "accel_crest_factor",
    "accel_zero_crossing_rate", "accel_dominant_hz",
    "accel_band_0_5_fraction", "accel_band_5_15_fraction",
    "accel_band_15_30_fraction", "accel_band_30_50_fraction",
]


def separation(a, b):
    """Probability that a random b exceeds a random a; ties count half."""
    return sum(1 if y > x else 0.5 if y == x else 0
               for x in a for y in b) / (len(a) * len(b))


def main():
    with SOURCE.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for baseline, comparison, title in PAIRS:
        for feature in FEATURES:
            a = [float(r[feature]) for r in rows if r["condition"] == baseline]
            b = [float(r[feature]) for r in rows if r["condition"] == comparison]
            if len(a) != 15 or len(b) != 15:
                raise ValueError(f"Expected 15 recordings for {baseline} and {comparison}")
            probability = separation(a, b)
            results.append({
                "comparison": title, "baseline": baseline,
                "target": comparison, "feature": feature,
                "baseline_median": statistics.median(a),
                "target_median": statistics.median(b),
                "median_difference_target_minus_baseline": statistics.median(b) - statistics.median(a),
                "probability_target_greater": probability,
                "separation_strength": max(probability, 1 - probability),
            })
    with (OUT / "feature_comparisons.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=results[0])
        writer.writeheader()
        writer.writerows(results)

    lines = ["# 吹风机工况对照分析", "",
             "每种工况有 15 次完整录制。本分析使用全部录制，仅用于探索差异，不能当作独立测试准确率。",
             "", "## 实验标签", "",
             "| 标签 | 档位 | 状态 |", "|---|---|---|",
             "| 01_cold_low | 冷风低档 | 无遮挡 |",
             "| 02_hot_low | 热风低档 | 无遮挡 |",
             "| 03_hot_high | 热风高档 | 无遮挡 |",
             "| 04_inlet_block | 冷风低档 | 进风口遮挡 |",
             "| 05_outlet_block | 热风低档 | 出风口遮挡 |", "",
             "## 同档位对照", "",
             "表中“较大概率”表示随机取一条目标工况录制和一条基线录制时，目标特征较大的比例；0.5 表示无明显方向，接近 0 或 1 表示区分较稳定。它不是分类准确率。", ""]
    for baseline, target, title in PAIRS:
        subset = sorted((r for r in results if r["baseline"] == baseline and r["target"] == target),
                        key=lambda r: r["separation_strength"], reverse=True)
        lines += [f"### {title}", "",
                  f"对照：`{target}` 与 `{baseline}`。按特征分离程度列出前五项：", "",
                  "| 特征 | 基线中位数 | 目标中位数 | 目标较大概率 |",
                  "|---|---:|---:|---:|"]
        for r in subset[:5]:
            lines.append(f"| {r['feature']} | {r['baseline_median']:.4g} | {r['target_median']:.4g} | {r['probability_target_greater']:.1%} |")
        lines.append("")
    lines += ["## 解释与下一步", "",
              "- 进风口遮挡应与冷风低档无挡比较；出风口遮挡应与热风低档无挡比较。两种遮挡状态本身使用不同冷热档位，不能直接比较来归因遮挡位置。",
              "- 当前五分类内部留出测试为 13/25（52%）；热风高档 5 组全部错判为热风低档。该结果记录在 `results/classification/accuracy_report.txt`。",
              "- `accel_dominant_hz` 多数接近 0.1 Hz，属于当前加速度幅值处理下的低频主峰；暂不把它解释成电机转速。应重新检查三轴原始频谱，并增加转速相关的谱峰/谐波特征。",
              "- 已查看全部特征和原留出测试表现，因此若据此改特征或模型，原 25 组不能再被当作完全未见过的最终测试。应另录新的独立样本进行盲测。", ""]
    (OUT / "comparison_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT / 'feature_comparisons.csv'}")
    print(f"Wrote {OUT / 'comparison_report.md'}")


if __name__ == "__main__":
    main()
