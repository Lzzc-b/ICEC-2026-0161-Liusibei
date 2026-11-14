"""Retrospective reanalysis after fixing the DC-bin energy-ratio bug.

Run: python src/corrected_reanalysis.py
The new recordings and original blind score have already been seen; this is
not a second independent blind test.
"""

import csv
from pathlib import Path

from blind_test import KEY, OUT as BLIND_OUT, extract_one, samples
from train_classifier import FEATURES, fit_scaler, predict, split

OLD = Path("results/features/features_corrected.csv")
OUT = BLIND_OUT / "corrected_reanalysis"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with OLD.open(newline="", encoding="utf-8-sig") as f:
        training_all = list(csv.DictReader(f))
    for row in training_all:
        for feature in FEATURES:
            row[feature] = float(row[feature])
    training, holdout = split(training_all)
    scaler = fit_scaler(training)
    blind = [extract_one(sid, wav, acc) for sid, wav, acc in samples()]
    with (OUT / "blind_features_corrected.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["sample_id"] + FEATURES)
        writer.writeheader()
        writer.writerows({k: row[k] for k in ["sample_id"] + FEATURES} for row in blind)
    with KEY.open(newline="", encoding="utf-8-sig") as f:
        answer = {r["sample_id"]: r["true_condition"] for r in csv.DictReader(f)}
    predictions = [(r["sample_id"], answer[r["sample_id"]],
                    predict(r, training, scaler, k=3)) for r in blind]
    with (OUT / "scored_predictions_corrected.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["sample_id", "true_condition", "predicted_condition", "correct"])
        writer.writerows((sid, actual, guess, int(actual == guess))
                         for sid, actual, guess in predictions)
    internal_correct = sum(predict(r, training, scaler, k=3) == r["condition"]
                           for r in holdout)
    blind_correct = sum(actual == guess for _, actual, guess in predictions)
    labels = sorted(set(answer.values()))
    lines = ["# 特征修正后的事后复核", "",
             "原特征提取代码在计算 0–5 Hz 加速度能量占比时把 DC 频点放入分子，却没有放入分母，导致占比可能大于 1。现已排除 DC 频点；全部频带占比应在 0 到 1 之间。",
             "", f"- 修正后旧数据内部留出测试：**{internal_correct}/25 = {internal_correct/25:.1%}**。",
             f"- 修正后新录制数据事后复核：**{blind_correct}/25 = {blind_correct/25:.1%}**。",
             "- 原第一次盲测为 **9/25 = 36.0%**，保留在上级文件夹；修正后结果不能称为第二次独立盲测，因为已查看这些样本及原结果。", "",
             "| 真实工况 | 修正后正确数 / 5 |", "|---|---:|"]
    for label in labels:
        count = sum(actual == guess and actual == label for _, actual, guess in predictions)
        lines.append(f"| {label} | {count}/5 |")
    lines += ["", "后续若要证明修正后模型的独立准确率，需固定代码后另录一批未见过的样本。"]
    (OUT / "corrected_reanalysis_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
