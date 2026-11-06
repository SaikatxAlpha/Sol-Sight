"""
Evaluate a trained DefectCNN on the held-out test split and write the
confusion matrix plus per-class precision / recall / F1.

The test images are never used for training or for picking the best epoch,
so these numbers are an honest estimate of performance on new cells from
the same kind of data (ELPV electroluminescence images).

Usage:
    python evaluate_cnn.py --data-dir data/elpv --model ../saved_models/cnn_best.pt
Writes ../saved_models/cnn_metrics.json next to the model.
"""
import argparse
import json
import os
import sys

import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app.models.cnn_model import DefectCNN, IMAGE_SIZE  # noqa: E402


def evaluate(data_dir: str, model_path: str):
    torch.set_num_threads(os.cpu_count() or 4)
    ckpt = torch.load(model_path, map_location="cpu", weights_only=True)
    classes = ckpt["classes"]
    model = DefectCNN(pretrained=False, classes=classes)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()

    tf = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    test_ds = datasets.ImageFolder(os.path.join(data_dir, "test"), transform=tf)
    assert test_ds.classes == classes, f"test classes {test_ds.classes} != model classes {classes}"

    n = len(classes)
    matrix = [[0] * n for _ in range(n)]  # rows = actual, cols = predicted
    with torch.no_grad():
        for imgs, labels in DataLoader(test_ds, batch_size=64):
            preds = model(imgs).argmax(1)
            for a, p in zip(labels.tolist(), preds.tolist()):
                matrix[a][p] += 1

    total = sum(map(sum, matrix))
    per_class = {}
    for i, c in enumerate(classes):
        tp = matrix[i][i]
        fp = sum(matrix[r][i] for r in range(n)) - tp
        fn = sum(matrix[i]) - tp
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[c] = {"precision": round(precision, 3), "recall": round(recall, 3),
                        "f1": round(f1, 3), "support": sum(matrix[i])}

    metrics = {
        "dataset": "ELPV (electroluminescence solar cells), held-out test split",
        "classes": classes,
        "confusion_matrix": {"rows_actual_cols_predicted": matrix},
        "accuracy": round(sum(matrix[i][i] for i in range(n)) / total, 3),
        "per_class": per_class,
        "test_images": total,
        "training": ckpt.get("meta", {}),
    }

    w = max(len(c) for c in classes) + 2
    print(f"\nConfusion matrix ({total} test images; rows = actual, columns = predicted)\n")
    print(" " * w + "".join(f"{c:>{w}}" for c in classes))
    for c, row in zip(classes, matrix):
        print(f"{c:<{w}}" + "".join(f"{v:>{w}}" for v in row))
    print(f"\naccuracy  {metrics['accuracy']:.3f}")
    for c, m in per_class.items():
        print(f"{c:<{w}} precision {m['precision']:.3f}  recall {m['recall']:.3f}  f1 {m['f1']:.3f}  n={m['support']}")

    out = os.path.join(os.path.dirname(model_path), "cnn_metrics.json")
    with open(out, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/elpv")
    parser.add_argument("--model", default="../saved_models/cnn_best.pt")
    args = parser.parse_args()
    evaluate(args.data_dir, args.model)
