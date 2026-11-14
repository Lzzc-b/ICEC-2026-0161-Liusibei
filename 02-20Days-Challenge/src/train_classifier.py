"""Plot feature distributions and evaluate a recording-level kNN baseline.

Run: python src/train_classifier.py
Uses only the Python standard library. No windows from a recording are split
between training and test sets; each input row is one complete recording.
"""

import csv
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


INPUT = Path("results/features/features.csv")
OUTPUT = Path("results/classification")
SEED = 2026
TEST_PER_CLASS = 5
FEATURES = [
    "audio_rms", "audio_crest_factor", "audio_zero_crossing_rate",
    "audio_dominant_hz", "audio_band_0_200_fraction",
    "audio_band_200_1000_fraction", "audio_band_1000_4000_fraction",
    "audio_band_4000_10000_fraction", "accel_rms", "accel_crest_factor",
    "accel_zero_crossing_rate", "accel_dominant_hz",
    "accel_band_0_5_fraction", "accel_band_5_15_fraction",
    "accel_band_15_30_fraction", "accel_band_30_50_fraction",
]
PLOT_FEATURES = ["audio_rms", "audio_zero_crossing_rate",
                 "audio_dominant_hz", "audio_band_1000_4000_fraction",
                 "accel_rms", "accel_dominant_hz"]
COLORS = ["#2563eb", "#d97706", "#dc2626", "#059669", "#7c3aed"]


def load_rows():
    with INPUT.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("empty feature table")
    ids = [r["recording_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate recording IDs")
    for row in rows:
        for feature in FEATURES:
            value = float(row[feature])
            if not math.isfinite(value):
                raise ValueError(f"non-finite {feature} in {row['recording_id']}")
            row[feature] = value
    return rows


def split(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["condition"]].append(row)
    rng = random.Random(SEED)
    train, test = [], []
    for label in sorted(groups):
        group = sorted(groups[label], key=lambda r: r["recording_id"])
        if len(group) <= TEST_PER_CLASS:
            raise ValueError(f"too few recordings for {label}")
        rng.shuffle(group)
        test.extend(group[:TEST_PER_CLASS])
        train.extend(group[TEST_PER_CLASS:])
    return train, test


def fit_scaler(rows):
    means = [sum(r[f] for r in rows) / len(rows) for f in FEATURES]
    stds = [math.sqrt(sum((r[f] - m) ** 2 for r in rows) / len(rows)) or 1.0
            for f, m in zip(FEATURES, means)]
    return means, stds


def vector(row, scaler):
    means, stds = scaler
    return [(row[f] - m) / s for f, m, s in zip(FEATURES, means, stds)]


def predict(row, train, scaler, k=3):
    x = vector(row, scaler)
    neighbors = sorted(
        ((sum((a - b) ** 2 for a, b in zip(x, vector(r, scaler))),
          r["condition"], r["recording_id"]) for r in train),
        key=lambda item: (item[0], item[1], item[2]),
    )[:k]
    votes = Counter(label for _, label, _ in neighbors)
    return min(votes, key=lambda label: (-votes[label],
                                          sum(d for d, lab, _ in neighbors if lab == label),
                                          label))


def esc(value):
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def quantile(values, p):
    values = sorted(values)
    position = p * (len(values) - 1)
    lo, hi = int(position), math.ceil(position)
    return values[lo] + (values[hi] - values[lo]) * (position - lo)


def plot_distributions(rows, labels):
    width, height = 1050, 940
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<text x="28" y="34" font-family="Arial" font-size="23" font-weight="bold">Feature distributions by condition</text>',
             '<text x="28" y="57" font-family="Arial" font-size="13" fill="#555">Each box shows 15 complete recordings; line = median, box = Q1–Q3, whiskers = min/max.</text>']
    for panel, feature in enumerate(PLOT_FEATURES):
        x0 = 28 + (panel % 2) * 520
        y0 = 85 + (panel // 2) * 280
        values = [r[feature] for r in rows]
        low, high = min(values), max(values)
        span = high - low or 1
        low -= span * .07
        high += span * .07
        left, right = x0 + 158, x0 + 492
        scale = lambda v: left + (v - low) / (high - low) * (right - left)
        parts.append(f'<text x="{x0}" y="{y0 + 18}" font-family="Arial" font-size="16" font-weight="bold">{esc(feature)}</text>')
        for i, label in enumerate(labels):
            data = [r[feature] for r in rows if r["condition"] == label]
            mn, q1, med, q3, mx = [quantile(data, p) for p in (0, .25, .5, .75, 1)]
            y = y0 + 48 + i * 37
            color = COLORS[i]
            parts += [f'<text x="{x0}" y="{y + 5}" font-family="Arial" font-size="12">{esc(label)}</text>',
                      f'<line x1="{scale(mn):.1f}" y1="{y}" x2="{scale(mx):.1f}" y2="{y}" stroke="{color}"/>',
                      f'<rect x="{scale(q1):.1f}" y="{y-8}" width="{max(1,scale(q3)-scale(q1)):.1f}" height="16" fill="{color}" fill-opacity=".25" stroke="{color}"/>',
                      f'<line x1="{scale(med):.1f}" y1="{y-9}" x2="{scale(med):.1f}" y2="{y+9}" stroke="{color}" stroke-width="2"/>']
        parts += [f'<text x="{left}" y="{y0+250}" font-family="Arial" font-size="11" fill="#555">{low:.3g}</text>',
                  f'<text x="{right}" y="{y0+250}" text-anchor="end" font-family="Arial" font-size="11" fill="#555">{high:.3g}</text>']
    (OUTPUT / "feature_distributions.svg").write_text("\n".join(parts + ["</svg>"]), encoding="utf-8")


def plot_confusion(matrix, labels):
    n = len(labels)
    width, height = 900, 680
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<text x="30" y="35" font-family="Arial" font-size="22" font-weight="bold">Held-out confusion matrix</text>',
             '<text x="30" y="58" font-family="Arial" font-size="13" fill="#555">Rows: true condition. Columns: predicted condition. Five held-out recordings per row.</text>']
    cell, x0, y0 = 86, 275, 165
    for j, label in enumerate(labels):
        parts.append(f'<text x="{x0+j*cell+cell/2}" y="{y0-12}" text-anchor="middle" font-family="Arial" font-size="11">{esc(label)}</text>')
    for i, label in enumerate(labels):
        parts.append(f'<text x="{x0-15}" y="{y0+i*cell+cell/2+4}" text-anchor="end" font-family="Arial" font-size="12">{esc(label)}</text>')
        for j in range(n):
            v = matrix[i][j]
            opacity = .10 + .15 * v
            parts += [f'<rect x="{x0+j*cell}" y="{y0+i*cell}" width="{cell-2}" height="{cell-2}" fill="#2563eb" fill-opacity="{opacity:.2f}"/>',
                      f'<text x="{x0+j*cell+cell/2}" y="{y0+i*cell+cell/2+7}" text-anchor="middle" font-family="Arial" font-size="22">{v}</text>']
    (OUTPUT / "confusion_matrix.svg").write_text("\n".join(parts + ["</svg>"]), encoding="utf-8")


def main():
    rows = load_rows()
    labels = sorted({r["condition"] for r in rows})
    OUTPUT.mkdir(parents=True, exist_ok=True)
    train, test = split(rows)
    scaler = fit_scaler(train)  # The held-out set never influences normalization.
    predictions = [(r, predict(r, train, scaler)) for r in test]
    matrix = [[sum(r["condition"] == actual and guess == predicted
                   for r, guess in predictions) for predicted in labels]
              for actual in labels]
    correct = sum(r["condition"] == guess for r, guess in predictions)
    plot_distributions(rows, labels)
    plot_confusion(matrix, labels)
    with (OUTPUT / "test_predictions.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["recording_id", "true_condition", "predicted_condition", "correct"])
        for row, guess in sorted(predictions, key=lambda item: item[0]["recording_id"]):
            writer.writerow([row["recording_id"], row["condition"], guess,
                             int(row["condition"] == guess)])
    lines = ["Recording-level held-out evaluation", f"Random seed: {SEED}",
             f"Model: standardized Euclidean kNN, k=3, {len(FEATURES)} features",
             f"Split: {len(train)} training and {len(test)} test recordings; {TEST_PER_CLASS} test recordings per class",
             "Scaling fitted on training recordings only.",
             f"Overall accuracy: {correct}/{len(test)} = {correct/len(test):.1%}", "",
             "Per-class recall (correct / test recordings):"]
    for i, label in enumerate(labels):
        lines.append(f"{label}: {matrix[i][i]}/{sum(matrix[i])} = {matrix[i][i]/sum(matrix[i]):.1%}")
    lines += ["", "Confusion matrix (rows=true, columns=predicted):",
              ",".join(["true\\pred"] + labels)]
    lines += [",".join([label] + [str(v) for v in matrix[i]])
              for i, label in enumerate(labels)]
    lines += ["", "Limitations: one fixed holdout split, 15 recordings per class,",
              "and all data from the same experimental setup. This is an internal",
              "test estimate, not a blind or cross-device accuracy claim."]
    (OUTPUT / "accuracy_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"Outputs: {OUTPUT}")


if __name__ == "__main__":
    main()
