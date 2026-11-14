"""Controlled synthetic white-noise robustness study on new WAV recordings.

Run: python src/noise_analysis.py
This is a post-hoc perturbation study, not a new independent blind test.
"""

import csv
import math
import random
from pathlib import Path

from blind_test import KEY, samples
from extract_features import read_acceleration, read_wav, summarize
from train_classifier import FEATURES, fit_scaler, predict, split

TRAIN = Path("results/features/features_corrected.csv")
OUT = Path("results/noise_analysis")
SNRS = ("clean", 20, 10, 0)


def noisy_audio(audio, snr_db, seed):
    signal_rms = math.sqrt(sum(x*x for x in audio) / len(audio))
    target_noise_rms = signal_rms / (10 ** (snr_db / 20))
    rng = random.Random(seed)
    # Uniform white noise scaled to the requested realized RMS.
    noise = [rng.random() * 2 - 1 for _ in audio]
    noise_rms = math.sqrt(sum(x*x for x in noise) / len(noise))
    factor = target_noise_rms / noise_rms
    return [x + factor*n for x, n in zip(audio, noise)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with TRAIN.open(newline="", encoding="utf-8-sig") as f:
        original = list(csv.DictReader(f))
    for row in original:
        for feature in FEATURES:
            row[feature] = float(row[feature])
    train, _ = split(original)
    scaler = fit_scaler(train)
    with KEY.open(newline="", encoding="utf-8-sig") as f:
        answers = {r["sample_id"]: r["true_condition"] for r in csv.DictReader(f)}
    results = []
    for sample_id, wav_path, csv_path in samples():
        audio, audio_rate = read_wav(wav_path)
        accel, accel_rate, _ = read_acceleration(csv_path)
        accel_features = summarize(accel, accel_rate,
                                   [(0, 5), (5, 15), (15, 30), (30, 50)], "accel")
        for level in SNRS:
            signal = audio if level == "clean" else noisy_audio(
                audio, level, seed=2026 + sum(ord(c) for c in sample_id) * 100 + level)
            row = {"sample_id": sample_id}
            row.update(accel_features)
            row.update(summarize(signal, audio_rate,
                                 [(0, 200), (200, 1000), (1000, 4000),
                                  (4000, 10000)], "audio"))
            guess = predict(row, train, scaler, k=3)
            actual = answers[sample_id]
            results.append({"sample_id": sample_id, "snr_db": level,
                            "true_condition": actual, "predicted_condition": guess,
                            "correct": int(actual == guess)})
        print(sample_id, flush=True)
    with (OUT / "noise_predictions.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=results[0])
        writer.writeheader()
        writer.writerows(results)
    labels = sorted(set(answers.values()))
    lines = ["# 模拟白噪声抗噪分析", "",
             "使用修正后的特征算法与固定的 50 组旧数据训练模型，在 25 组新录音上分别测试原始声音和 20/10/0 dB 信噪比的加性白噪声。加速度 CSV 保持不变；噪声只加到音频特征计算中，不改写原 WAV。", "",
             "| 条件 | 正确数 | 准确率 |", "|---|---:|---:|"]
    for level in SNRS:
        subset = [r for r in results if r["snr_db"] == level]
        correct = sum(r["correct"] for r in subset)
        label = "原始声音" if level == "clean" else f"{level} dB"
        lines.append(f"| {label} | {correct}/25 | {correct/25:.1%} |")
    lines += ["", "## 各工况正确数", "",
              "| 工况 | 原始 | 20 dB | 10 dB | 0 dB |",
              "|---|---:|---:|---:|---:|"]
    for label in labels:
        counts = [sum(r["correct"] for r in results
                      if r["true_condition"] == label and r["snr_db"] == level)
                  for level in SNRS]
        lines.append("| " + label + " | " + " | ".join(f"{n}/5" for n in counts) + " |")
    lines += ["", "## 方法与局限", "",
              "- 信噪比按音频 RMS 幅度定义：`SNR = 20 log10(RMS(signal)/RMS(noise))`；每段噪声按实际 RMS 缩放，随机种子固定以便复现。",
              "- 这是模拟白噪声，不能代表人声、交通声或其他真实环境噪声；也没有扰动手机加速度。",
              "- 同一批 25 组样本在不同噪声条件下重复使用，所得准确率彼此相关，不能视为四个独立盲测。",
              "- 这批样本及第一次盲测结果已被查看；本实验是事后抗噪分析，不是新的独立准确率证明。", ""]
    (OUT / "anti_noise_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
