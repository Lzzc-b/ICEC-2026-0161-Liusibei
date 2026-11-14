"""Explore raw-axis vibration and audio spectra for complete recordings.

Run: python src/analyze_spectra.py
This is descriptive analysis, not independent model evaluation.
"""

import csv
import math
import statistics
from pathlib import Path

from extract_features import CONDITIONS, fft_power, find_pairs, read_wav


DATA_ROOT = Path("D:/")
OUT = Path("results/spectral_analysis")


def spectrum(values, rate, size):
    mean = sum(values) / len(values)
    starts = [round(i * (len(values) - size) / 9) for i in range(10)] if len(values) > size else [0]
    result = [0.0] * (size // 2 + 1)
    for start in starts:
        power = fft_power([v - mean for v in values[start:start + size]], rate)
        for i, p in enumerate(power):
            result[i] += p / len(starts)
    return result


def band_features(power, rate, size, low, high, prefix):
    bins = [i for i in range(1, len(power)) if low <= i * rate / size < high]
    if not bins:
        return {prefix + "_peak_hz": 0.0, prefix + "_power_fraction": 0.0}
    peak = max(bins, key=lambda i: power[i])
    total = sum(power[1:])
    return {prefix + "_peak_hz": peak * rate / size,
            prefix + "_power_fraction": sum(power[i] for i in bins) / total if total else 0.0}


def acceleration_axes(path):
    axes = [[], [], []]
    times = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            times.append(float(row["Time (s)"]))
            for axis, name in zip(axes, ("x", "y", "z")):
                axis.append(float(row[f"Linear Acceleration {name} (m/s^2)"]))
    rate = (len(times) - 1) / (times[-1] - times[0])
    return axes, rate


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for condition in CONDITIONS:
        for name, csv_path, wav_path in find_pairs(DATA_ROOT, condition):
            audio, audio_rate = read_wav(wav_path)
            axes, accel_rate = acceleration_axes(csv_path)
            row = {"condition": condition, "recording_id": name}
            audio_size = 4096
            audio_power = spectrum(audio, audio_rate, audio_size)
            for low, high in ((100, 600), (600, 2000), (2000, 6000)):
                row.update(band_features(audio_power, audio_rate, audio_size,
                                         low, high, f"audio_{low}_{high}"))
            total_audio = sum(audio_power[1:])
            row["audio_spectral_centroid_hz"] = (
                sum(i * audio_rate / audio_size * p for i, p in enumerate(audio_power)) / total_audio
                if total_audio else 0.0)
            for axis_name, values in zip(("x", "y", "z"), axes):
                size = 1024 if len(values) >= 1024 else 2 ** int(math.log2(len(values)))
                power = spectrum(values, accel_rate, size)
                for low, high in ((5, 20), (20, 45)):
                    row.update(band_features(power, accel_rate, size,
                                             low, high, f"accel_{axis_name}_{low}_{high}"))
                axis_mean = statistics.mean(values)
                row[f"accel_{axis_name}_rms"] = math.sqrt(
                    sum((v - axis_mean) ** 2 for v in values) / len(values))
            rows.append(row)
            print(name, flush=True)
    with (OUT / "spectral_features.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)

    groups = {condition: [r for r in rows if r["condition"] == condition]
              for condition in CONDITIONS}
    lines = ["# 原始三轴与录音频谱分析", "",
             "每种工况 15 条录制。下表是探索性中位数，不能作为独立盲测准确率。", "",
             "| 特征 | 热风低档 | 热风高档 | 进风遮挡（冷风低档） | 出风遮挡（热风低档） |",
             "|---|---:|---:|---:|---:|"]
    selected = ["audio_spectral_centroid_hz", "audio_100_600_peak_hz",
                "audio_600_2000_peak_hz", "audio_100_600_power_fraction",
                "audio_600_2000_power_fraction",
                "accel_x_5_20_peak_hz", "accel_y_5_20_peak_hz",
                "accel_z_5_20_peak_hz", "accel_x_20_45_power_fraction",
                "accel_y_20_45_power_fraction", "accel_z_20_45_power_fraction"]
    for feature in selected:
        medians = [statistics.median(float(r[feature]) for r in groups[c])
                   for c in ("02_hot_low", "03_hot_high", "04_inlet_block", "05_outlet_block")]
        lines.append("| " + feature + " | " + " | ".join(f"{v:.3g}" for v in medians) + " |")
    lines += ["", "## 阅读提示", "",
              "- 热风低档与热风高档的音频 100–600 Hz 主峰中位数都为约 293 Hz，600–2000 Hz 主峰也只相差约 10 Hz；当前峰值特征没有给出清晰的档位分界。可优先核查档位记录、录音位置和是否在稳定运行后开始录制。",
              "- 三轴峰值只在 5–20 Hz 范围内寻找，避免把低频漂移当成电机转速。采样率约 100 Hz，无法观察高于约 50 Hz 的振动；这些峰值也不能直接认定为电机真实转速。",
              "- 音频使用 4096 点 FFT、10 个均匀分布的窗平均，频率分辨率约 11.7 Hz。",
              "- 进风遮挡与冷风低档无挡比较；出风遮挡与热风低档无挡比较。完整逐条结果见 `spectral_features.csv`。",
              "- 已查看原测试集与全量数据。若利用本分析选择新特征，最终性能须用新录制的独立盲测样本报告。", ""]
    (OUT / "spectral_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(rows)} recordings to {OUT}")


if __name__ == "__main__":
    main()
