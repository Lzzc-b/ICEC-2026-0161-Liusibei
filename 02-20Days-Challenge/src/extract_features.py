"""Extract one row of audio and acceleration features per paired recording.

Run: python src/extract_features.py --data-root D:/ --output results/features/features_corrected.csv
"""

import argparse
import csv
import math
import struct
import wave
from pathlib import Path


CONDITIONS = (
    "01_cold_low", "02_hot_low", "03_hot_high",
    "04_inlet_block", "05_outlet_block",
)


def fft_power(samples, sample_rate):
    """Return positive-frequency power bins from a Hann-windowed radix-2 FFT."""
    n = len(samples)
    a = [complex(x * (0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1))))
         for i, x in enumerate(samples)]
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            a[i], a[j] = a[j], a[i]
    size = 2
    while size <= n:
        half = size // 2
        step = complex(math.cos(-2 * math.pi / size), math.sin(-2 * math.pi / size))
        for start in range(0, n, size):
            w = 1 + 0j
            for k in range(half):
                u, v = a[start + k], w * a[start + k + half]
                a[start + k], a[start + k + half] = u + v, u - v
                w *= step
        size *= 2
    return [abs(z) ** 2 for z in a[:n // 2 + 1]]


def summarize(values, sample_rate, bands, prefix, include_legacy_dc=False):
    n = len(values)
    if n < 64:
        raise ValueError("too few samples")
    mean = sum(values) / n
    rms = math.sqrt(sum(x * x for x in values) / n)
    std = math.sqrt(sum((x - mean) ** 2 for x in values) / n)
    peak = max(abs(x) for x in values)
    zcr = sum((values[i - 1] < mean) != (values[i] < mean)
              for i in range(1, n)) / (n - 1)
    result = {
        prefix + "_rms": rms, prefix + "_std": std,
        prefix + "_peak": peak,
        prefix + "_crest_factor": peak / rms if rms else 0,
        prefix + "_zero_crossing_rate": zcr,
    }
    size = 4096 if n >= 4096 else 2 ** int(math.log2(n))
    # Evenly spaced windows represent the whole recording without an expensive full FFT.
    starts = [round(i * (n - size) / 9) for i in range(10)] if n > size else [0]
    power = [0.0] * (size // 2 + 1)
    for start in starts:
        window = fft_power([x - mean for x in values[start:start + size]], sample_rate)
        for i, p in enumerate(window):
            power[i] += p
    power = [p / len(starts) for p in power]
    max_bin = max(range(1, len(power)), key=power.__getitem__)
    result[prefix + "_dominant_hz"] = max_bin * sample_rate / size
    total = sum(power[1:])
    for low, high in bands:
        energy = sum(p for i, p in enumerate(power)
                     if (i >= 1 or include_legacy_dc) and low <= i * sample_rate / size < high)
        result[f"{prefix}_band_{low}_{high}_fraction"] = energy / total if total else 0
    return result


def read_wav(path):
    with wave.open(str(path), "rb") as f:
        rate, channels, width = f.getframerate(), f.getnchannels(), f.getsampwidth()
        if width not in (1, 2, 3, 4):
            raise ValueError(f"unsupported WAV sample width: {width}")
        raw = f.readframes(f.getnframes())
    if width == 3:
        integers = [int.from_bytes(raw[i:i + 3], "little", signed=True)
                    for i in range(0, len(raw), 3)]
    elif width == 1:
        integers = [x - 128 for x in raw]
    else:
        fmt = "<" + {2: "h", 4: "i"}[width] * (len(raw) // width)
        integers = struct.unpack(fmt, raw)
    scale = float(2 ** (8 * width - 1))
    mono = [sum(integers[i:i + channels]) / (channels * scale)
            for i in range(0, len(integers), channels)]
    return mono, rate


def read_acceleration(path):
    times, axes = [], [[], [], []]
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        columns = ("Linear Acceleration x (m/s^2)",
                   "Linear Acceleration y (m/s^2)",
                   "Linear Acceleration z (m/s^2)")
        for row in reader:
            times.append(float(row["Time (s)"]))
            for axis, column in zip(axes, columns):
                axis.append(float(row[column]))
    if len(times) < 64 or times[-1] <= times[0]:
        raise ValueError("invalid acceleration time series")
    rate = (len(times) - 1) / (times[-1] - times[0])
    # Dynamic magnitude keeps the three axes while removing static sensor offset.
    means = [sum(axis) / len(axis) for axis in axes]
    magnitude = [math.sqrt(sum((axes[j][i] - means[j]) ** 2 for j in range(3)))
                 for i in range(len(times))]
    return magnitude, rate, times[-1] - times[0]


def find_pairs(root, condition):
    csv_dir, wav_dir = root / (condition + "_csv"), root / (condition + "_wav")
    csv_files = {p.stem: p for p in csv_dir.glob("*.csv")}
    wav_files = {p.stem: p for p in wav_dir.glob("*.wav")}
    if csv_files.keys() != wav_files.keys() or not csv_files:
        raise ValueError(f"{condition}: CSV/WAV names do not pair exactly")
    return [(name, csv_files[name], wav_files[name]) for name in sorted(csv_files)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("D:/"))
    parser.add_argument("--output", type=Path,
                        default=Path("results/features/features_corrected.csv"))
    args = parser.parse_args()
    rows = []
    for condition in CONDITIONS:
        for name, csv_path, wav_path in find_pairs(args.data_root, condition):
            audio, audio_rate = read_wav(wav_path)
            accel, accel_rate, accel_duration = read_acceleration(csv_path)
            row = {"condition": condition, "recording_id": name,
                   "csv_path": str(csv_path), "wav_path": str(wav_path),
                   "audio_duration_s": len(audio) / audio_rate,
                   "accel_duration_s": accel_duration,
                   "audio_sample_rate_hz": audio_rate,
                   "accel_sample_rate_hz": accel_rate}
            row.update(summarize(audio, audio_rate,
                                 [(0, 200), (200, 1000), (1000, 4000),
                                  (4000, 10000)], "audio"))
            row.update(summarize(accel, accel_rate,
                                 [(0, 5), (5, 15), (15, 30), (30, 50)], "accel"))
            rows.append(row)
            print(f"Processed {name}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
