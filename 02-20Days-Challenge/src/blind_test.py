"""Predict new recordings with the frozen baseline, then score separately.

Run in order:
  python src/blind_test.py predict
  python src/blind_test.py score

The predict stage does not open the answer key. The model is the original
50-recording training split, 16 features, standardized Euclidean 3-NN.
"""

import argparse
import csv
import hashlib
from pathlib import Path

from extract_features import read_wav, read_acceleration, summarize
from train_classifier import FEATURES, fit_scaler, predict, split


ROOT = Path("blind_test_data")
OUT = Path("results/blind_test")
KEY = ROOT / "answer_key_checked.csv"
TRAIN_FEATURES = Path("results/legacy/features_v1_dc_bug.csv")


def samples():
    wavs = sorted(ROOT.glob("*/*_B_wav/*.wav"))
    if len(wavs) != 25:
        raise ValueError(f"Expected 25 blind WAV files, found {len(wavs)}")
    result = []
    for wav in wavs:
        condition_folder = wav.parent.parent
        sample_id = wav.stem
        csv_path = condition_folder / (condition_folder.name + "_B_csv") / (sample_id + ".csv")
        if not csv_path.is_file():
            raise ValueError(f"Missing CSV for {sample_id}")
        result.append((sample_id, wav, csv_path))
    if len({s[0] for s in result}) != 25:
        raise ValueError("Duplicate blind sample IDs")
    return result


def extract_one(sample_id, wav_path, csv_path, legacy=False):
    audio, audio_rate = read_wav(wav_path)
    accel, accel_rate, _ = read_acceleration(csv_path)
    row = {"sample_id": sample_id}
    row.update(summarize(audio, audio_rate,
                         [(0, 200), (200, 1000), (1000, 4000), (4000, 10000)], "audio"))
    row.update(summarize(accel, accel_rate,
                         [(0, 5), (5, 15), (15, 30), (30, 50)], "accel",
                         include_legacy_dc=legacy))
    return row


def predict_stage():
    OUT.mkdir(parents=True, exist_ok=True)
    predictions_path = OUT / "predictions.csv"
    if predictions_path.exists():
        raise FileExistsError(f"Predictions already exist: {predictions_path}; preserving the first run")
    with TRAIN_FEATURES.open(newline="", encoding="utf-8-sig") as f:
        original_rows = list(csv.DictReader(f))
    for row in original_rows:
        for feature in FEATURES:
            row[feature] = float(row[feature])
    training, _ = split(original_rows)
    scaler = fit_scaler(training)
    blind_rows = []
    for sample_id, wav_path, csv_path in samples():
        row = extract_one(sample_id, wav_path, csv_path, legacy=True)
        blind_rows.append(row)
        print("Extracted", sample_id, flush=True)
    with (OUT / "blind_features.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["sample_id"] + FEATURES)
        writer.writeheader()
        writer.writerows({k: row[k] for k in ["sample_id"] + FEATURES} for row in blind_rows)
    with predictions_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["sample_id", "predicted_condition"])
        for row in blind_rows:
            writer.writerow([row["sample_id"], predict(row, training, scaler, k=3)])
    digest = hashlib.sha256(predictions_path.read_bytes()).hexdigest()
    (OUT / "prediction_sha256.txt").write_text(digest + "  predictions.csv\n", encoding="ascii")
    print(f"Saved 25 predictions before scoring. SHA256: {digest}")


def score_stage():
    predictions_path = OUT / "predictions.csv"
    if not predictions_path.is_file():
        raise FileNotFoundError("Run predict stage first")
    with predictions_path.open(newline="", encoding="utf-8-sig") as f:
        predictions = list(csv.DictReader(f))
    with KEY.open(newline="", encoding="utf-8-sig") as f:
        answers = list(csv.DictReader(f))
    predicted = {r["sample_id"]: r["predicted_condition"] for r in predictions}
    actual = {r["sample_id"]: r["true_condition"] for r in answers}
    if len(predicted) != 25 or len(actual) != 25 or predicted.keys() != actual.keys():
        raise ValueError("Prediction/answer IDs do not match exactly")
    labels = sorted(set(actual.values()))
    if set(predicted.values()) - set(labels):
        raise ValueError("Unknown predicted condition")
    scored = [(sid, actual[sid], predicted[sid], int(actual[sid] == predicted[sid]))
              for sid in sorted(actual)]
    with (OUT / "scored_predictions.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["sample_id", "true_condition", "predicted_condition", "correct"])
        writer.writerows(scored)
    matrix = [[sum(a == truth and p == guess for _, a, p, _ in scored)
               for guess in labels] for truth in labels]
    correct = sum(row[3] for row in scored)
    lines = ["NEW-RECORDING BLIND TEST (frozen baseline)",
             "Model: original 50-training-recording standardized Euclidean 3-NN, 16 features",
             "Prediction stage did not read the answer key.",
             f"Prediction SHA256: {hashlib.sha256(predictions_path.read_bytes()).hexdigest()}",
             f"Overall accuracy: {correct}/25 = {correct/25:.1%}", "",
             "Per-condition recall:"]
    for i, label in enumerate(labels):
        lines.append(f"{label}: {matrix[i][i]}/{sum(matrix[i])} = {matrix[i][i]/sum(matrix[i]):.1%}")
    lines += ["", "Confusion matrix (rows=actual, columns=predicted):",
              ",".join(["actual\\pred"] + labels)]
    lines += [",".join([label] + list(map(str, matrix[i])))
              for i, label in enumerate(labels)]
    lines += ["", "This is a single new-session evaluation. The class labels in",
              "the answer key are based on the experimenter's recording log and",
              "should be confirmed against the actual switch/obstruction settings."]
    (OUT / "blind_accuracy_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["predict", "score"])
    args = parser.parse_args()
    if args.stage == "predict":
        predict_stage()
    else:
        score_stage()
