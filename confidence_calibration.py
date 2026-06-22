"""
Confidence calibration analysis for TakeMeter fine-tuned model.

Expects a CSV with columns: text, true_label, predicted_label, confidence
(confidence = probability assigned to the predicted class, 0–1)

Usage:
    python confidence_calibration.py --predictions nba_predictions.csv
"""

import argparse
import csv
from collections import defaultdict


def load_predictions(path: str):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "true_label": row["true_label"].strip(),
                "predicted_label": row["predicted_label"].strip(),
                "confidence": float(row["confidence"]),
                "correct": row["true_label"].strip() == row["predicted_label"].strip(),
            })
    return rows


def calibration_table(rows, n_buckets=5):
    bucket_size = 1.0 / n_buckets
    buckets = defaultdict(list)
    for r in rows:
        bucket = min(int(r["confidence"] / bucket_size), n_buckets - 1)
        buckets[bucket].append(r["correct"])

    print(f"\n{'Confidence range':<22} {'Examples':>9} {'Accuracy':>10}")
    print("-" * 44)
    for i in range(n_buckets):
        lo = i * bucket_size
        hi = (i + 1) * bucket_size
        items = buckets[i]
        if items:
            acc = sum(items) / len(items)
            print(f"{lo:.1f}–{hi:.1f}{'':>12} {len(items):>9} {acc:>9.1%}")
        else:
            print(f"{lo:.1f}–{hi:.1f}{'':>12} {'0':>9} {'N/A':>10}")

    print()
    well_calibrated = True
    prev_acc = None
    for i in range(n_buckets):
        items = buckets[i]
        if not items:
            continue
        acc = sum(items) / len(items)
        if prev_acc is not None and acc < prev_acc - 0.1:
            well_calibrated = False
        prev_acc = acc

    if well_calibrated:
        print("Calibration: higher confidence tends to correspond to higher accuracy.")
    else:
        print("Calibration: confidence does NOT reliably predict accuracy — the model is overconfident in some buckets.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=str, required=True,
                        help="CSV with columns: true_label, predicted_label, confidence")
    args = parser.parse_args()

    rows = load_predictions(args.predictions)
    print(f"Loaded {len(rows)} predictions.")
    print(f"Overall accuracy: {sum(r['correct'] for r in rows)/len(rows):.1%}")
    calibration_table(rows)


if __name__ == "__main__":
    main()
