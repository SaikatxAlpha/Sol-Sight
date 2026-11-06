"""
Train the DefectCNN on a labeled folder-per-class image dataset:

    data/
      train/<Class>/*.png
      val/<Class>/*.png

Class folders must be a subset of DEFECT_CLASSES (Normal, Crack, Hotspot,
Soiling). The class list is saved inside the checkpoint, so a model trained
on only some classes (e.g. Normal/Crack from ELPV, see prepare_elpv.py) is
loaded with the right output size and the app knows what it can detect.

The ImageNet-pretrained ResNet18 backbone is frozen up to `--train-from`
(default layer4), which keeps CPU training practical on a small dataset.

Usage:
    python train_cnn.py --data-dir data/elpv --epochs 8 --out ../saved_models/cnn_best.pt
"""
import argparse
import os
import sys
import time

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app.models.cnn_model import DefectCNN, IMAGE_SIZE, DEFECT_CLASSES  # noqa: E402

NORMALIZE = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
BACKBONE_STAGES = ["conv1", "bn1", "relu", "maxpool", "layer1", "layer2", "layer3", "layer4"]


def get_dataloaders(data_dir: str, batch_size: int = 32, workers: int = 2):
    train_tf = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomRotation(8),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        NORMALIZE,
    ])
    val_tf = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        NORMALIZE,
    ])
    train_ds = datasets.ImageFolder(os.path.join(data_dir, "train"), transform=train_tf)
    val_ds = datasets.ImageFolder(os.path.join(data_dir, "val"), transform=val_tf)
    return (
        DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=workers, persistent_workers=workers > 0),
        DataLoader(val_ds, batch_size=batch_size, num_workers=workers, persistent_workers=workers > 0),
        train_ds,
    )


def freeze_backbone(model: DefectCNN, train_from: str):
    """Freeze every backbone stage before `train_from`; later stages and the head train."""
    trainable = False
    for name, module in zip(BACKBONE_STAGES, model.backbone.children()):
        trainable = trainable or name == train_from
        for p in module.parameters():
            p.requires_grad = trainable


def train(data_dir: str, epochs: int, lr: float, out_path: str, patience: int = 3, train_from: str = "layer4"):
    torch.manual_seed(42)
    torch.set_num_threads(os.cpu_count() or 4)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_loader, val_loader, train_ds = get_dataloaders(data_dir)
    classes = train_ds.classes
    unknown = set(classes) - set(DEFECT_CLASSES)
    assert not unknown, f"Unknown class folders {unknown}; expected a subset of {DEFECT_CLASSES}"
    print(f"classes={classes} train={len(train_ds)} val={len(val_loader.dataset)} device={device}")

    model = DefectCNN(num_classes=len(classes), pretrained=True).to(device)
    freeze_backbone(model, train_from)

    # Weight the loss by inverse class frequency so the minority class isn't ignored.
    counts = torch.bincount(torch.tensor(train_ds.targets), minlength=len(classes)).float()
    weights = (counts.sum() / (len(classes) * counts)).to(device)
    criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", patience=1)

    best_val_loss = float("inf")
    epochs_no_improve = 0

    for epoch in range(1, epochs + 1):
        start = time.time()
        model.train()
        # Frozen BatchNorm layers should keep their ImageNet statistics.
        for name, module in zip(BACKBONE_STAGES, model.backbone.children()):
            if not any(p.requires_grad for p in module.parameters()):
                module.eval()
        running_loss = 0.0
        for imgs, labels in train_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(imgs), labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * imgs.size(0)
        train_loss = running_loss / len(train_loader.dataset)

        model.eval()
        val_loss, correct = 0.0, 0
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(device), labels.to(device)
                logits = model(imgs)
                val_loss += criterion(logits, labels).item() * imgs.size(0)
                correct += (logits.argmax(1) == labels).sum().item()
        val_loss /= len(val_loader.dataset)
        val_acc = correct / len(val_loader.dataset)
        scheduler.step(val_loss)

        print(f"Epoch {epoch}/{epochs} | train_loss={train_loss:.4f} val_loss={val_loss:.4f} "
              f"val_acc={val_acc:.3f} | {time.time() - start:.0f}s", flush=True)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            torch.save({
                "classes": classes,
                "state_dict": model.state_dict(),
                "meta": {"epoch": epoch, "val_loss": round(val_loss, 4), "val_acc": round(val_acc, 4),
                         "dataset": os.path.basename(os.path.normpath(data_dir))},
            }, out_path)
            print(f"  -> saved new best model to {out_path}", flush=True)
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print("Early stopping triggered.")
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/elpv")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--train-from", default="layer4", choices=BACKBONE_STAGES)
    parser.add_argument("--out", default="../saved_models/cnn_best.pt")
    args = parser.parse_args()
    train(args.data_dir, args.epochs, args.lr, args.out, train_from=args.train_from)
