"""
Turn the ELPV dataset into the folder-per-class layout train_cnn.py expects.

ELPV (https://github.com/zae-bayern/elpv-dataset, CC BY-NC-SA 4.0) has
2,624 electroluminescence images of single solar cells, each rated by
experts with a probability of being defective: 0, 1/3, 2/3 or 1.
Defects in ELPV are mostly cracks and broken fingers, so:

    probability >= 0.5  ->  Crack
    probability <  0.5  ->  Normal

ELPV has no hotspot or soiling labels, so the CNN trained on it is a crack
detector; the rule-based stage still covers Hotspot and Soiling.

Split is stratified 70 / 15 / 15 (train / val / test) with a fixed seed.
The test split is never seen during training -- evaluate_cnn.py uses it.

Usage:
    git clone --depth 1 https://github.com/zae-bayern/elpv-dataset.git data/elpv-dataset
    python prepare_elpv.py --src data/elpv-dataset --out data/elpv
"""
import argparse
import os
import random
import shutil
from collections import Counter


def read_labels(src: str):
    data_dir = os.path.join(src, "src", "elpv_dataset", "data")
    rows = []
    with open(os.path.join(data_dir, "labels.csv")) as f:
        for line in f:
            parts = line.split()
            if len(parts) < 3:
                continue
            path, prob, kind = parts[0], float(parts[1]), parts[2]
            rows.append((os.path.join(data_dir, path), "Crack" if prob >= 0.5 else "Normal", kind))
    return rows


def main(src: str, out: str, seed: int = 42):
    rows = read_labels(src)
    rng = random.Random(seed)
    if os.path.exists(out):
        shutil.rmtree(out)

    # Stratify on label and cell type (mono/poly) so every split sees both.
    groups = {}
    for r in rows:
        groups.setdefault((r[1], r[2]), []).append(r)

    counts = Counter()
    for items in groups.values():
        rng.shuffle(items)
        n = len(items)
        n_train, n_val = int(n * 0.70), int(n * 0.15)
        splits = {"train": items[:n_train], "val": items[n_train:n_train + n_val], "test": items[n_train + n_val:]}
        for split, chunk in splits.items():
            for path, label, _ in chunk:
                dst = os.path.join(out, split, label)
                os.makedirs(dst, exist_ok=True)
                shutil.copy2(path, dst)
                counts[(split, label)] += 1

    for split in ("train", "val", "test"):
        print(f"{split:5s}  Normal={counts[(split, 'Normal')]:4d}  Crack={counts[(split, 'Crack')]:4d}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default="data/elpv-dataset")
    parser.add_argument("--out", default="data/elpv")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    main(args.src, args.out, args.seed)
