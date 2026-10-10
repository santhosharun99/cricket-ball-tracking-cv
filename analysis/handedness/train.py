"""
Bowling-arm (left/right) classifier trained on the corrected_all_data sample
(600 clips, 100 per class, 1800 cropped frames total -- crop removes the top
12% / bottom 15% of each frame to cut out scoreboard/logo overlays, since we
found some clips are horizontally mirrored to balance the dataset and don't
want the model cheating off backwards on-screen text).

Split is by CLIP, not by frame, so all 3 frames of a clip land on the same
side of the train/val split -- otherwise the model could "leak" clip identity
across the split and look better than it really is.

Honest framing: this predicts LEFT-ARM vs RIGHT-ARM bowling action from a
single frame near release. It says nothing about ball position; it's a
separate sub-task aimed at telling the release-detection script which wrist
to trust before it starts tracking.
"""
import csv
import os
import random

import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

random.seed(42)
torch.manual_seed(42)

ROOT = "analysis/handedness"
FRAMES = os.path.join(ROOT, "frames_train")

with open(os.path.join(ROOT, "manifest.csv")) as f:
    rows = list(csv.DictReader(f))

# split by clip_id, stratified per class
by_class = {}
for r in rows:
    by_class.setdefault(r["class"], []).append(r)

train_rows, val_rows = [], []
for cls, items in by_class.items():
    items = items[:]
    random.shuffle(items)
    n_val = max(1, int(len(items) * 0.15))
    val_rows.extend(items[:n_val])
    train_rows.extend(items[n_val:])

print(f"clips: {len(rows)} total, {len(train_rows)} train, {len(val_rows)} val")


def expand(rows):
    samples = []
    for r in rows:
        label = 0 if r["arm"] == "left" else 1
        for fname in r["frames"].split(";"):
            samples.append((os.path.join(FRAMES, fname), label, r["clip_id"]))
    return samples


train_samples = expand(train_rows)
val_samples = expand(val_rows)
print(f"frames: {len(train_samples)} train, {len(val_samples)} val")

IMG_SIZE = 160
train_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
# NOTE: deliberately NO random horizontal flip augmentation -- flipping would
# swap left<->right and corrupt the label.
val_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


class FrameDataset(Dataset):
    def __init__(self, samples, tf):
        self.samples = samples
        self.tf = tf

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label, clip_id = self.samples[idx]
        img = Image.open(path).convert("RGB")
        return self.tf(img), label, clip_id


train_ds = FrameDataset(train_samples, train_tf)
val_ds = FrameDataset(val_samples, val_tf)
train_dl = DataLoader(train_ds, batch_size=32, shuffle=True, num_workers=2)
val_dl = DataLoader(val_ds, batch_size=32, shuffle=False, num_workers=2)

device = torch.device("cpu")

# NOTE: torchvision's pretrained mobilenet weights are hosted on
# download.pytorch.org, which this sandbox's network allowlist blocks (same
# wall hit earlier trying to get mediapipe's heavier model file). Rather than
# fight the network again, train a small CNN from scratch instead -- honest
# tradeoff: no ImageNet head start, but it keeps this fully offline and the
# task (left-arm vs right-arm swing direction) is simple enough that a small
# from-scratch model is a fair thing to try first.
class SmallCNN(nn.Module):
    def __init__(self):
        super().__init__()
        def block(cin, cout):
            return nn.Sequential(
                nn.Conv2d(cin, cout, 3, padding=1), nn.BatchNorm2d(cout), nn.ReLU(inplace=True),
                nn.Conv2d(cout, cout, 3, padding=1), nn.BatchNorm2d(cout), nn.ReLU(inplace=True),
                nn.MaxPool2d(2),
            )
        self.features = nn.Sequential(
            block(3, 32),    # 160 -> 80
            block(32, 64),   # 80 -> 40
            block(64, 128),  # 40 -> 20
            block(128, 128), # 20 -> 10
        )
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Sequential(
            nn.Flatten(), nn.Dropout(0.3), nn.Linear(128, 64), nn.ReLU(inplace=True), nn.Linear(64, 2)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.pool(x)
        return self.classifier(x)

model = SmallCNN().to(device)
opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
crit = nn.CrossEntropyLoss()

EPOCHS = 18
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
best_val_acc = 0.0
history = []

for epoch in range(EPOCHS):
    model.train()
    total, correct, loss_sum = 0, 0, 0.0
    for imgs, labels, _ in train_dl:
        imgs, labels = imgs.to(device), labels.to(device)
        opt.zero_grad()
        out = model(imgs)
        loss = crit(out, labels)
        loss.backward()
        opt.step()
        loss_sum += loss.item() * imgs.size(0)
        preds = out.argmax(1)
        correct += (preds == labels).sum().item()
        total += imgs.size(0)
    train_acc = correct / total
    train_loss = loss_sum / total

    model.eval()
    val_total, val_correct = 0, 0
    clip_votes = {}
    clip_truth = {}
    with torch.no_grad():
        for imgs, labels, clip_ids in val_dl:
            imgs, labels = imgs.to(device), labels.to(device)
            out = model(imgs)
            preds = out.argmax(1)
            val_correct += (preds == labels).sum().item()
            val_total += imgs.size(0)
            for cid, p, l in zip(clip_ids, preds.tolist(), labels.tolist()):
                clip_votes.setdefault(cid, []).append(p)
                clip_truth[cid] = l
    val_acc = val_correct / val_total
    scheduler.step()

    # clip-level accuracy: majority vote across a clip's frames
    clip_correct = 0
    for cid, votes in clip_votes.items():
        maj = 1 if sum(votes) * 2 > len(votes) else 0
        if maj == clip_truth[cid]:
            clip_correct += 1
    clip_acc = clip_correct / len(clip_votes)

    print(f"epoch {epoch+1}/{EPOCHS}  train_loss={train_loss:.4f} train_acc={train_acc:.3f}  "
          f"val_frame_acc={val_acc:.3f}  val_clip_acc={clip_acc:.3f}")
    history.append({"epoch": epoch+1, "train_loss": train_loss, "train_acc": train_acc,
                     "val_frame_acc": val_acc, "val_clip_acc": clip_acc})

    if clip_acc > best_val_acc:
        best_val_acc = clip_acc
        torch.save(model.state_dict(), os.path.join(ROOT, "best_model.pt"))

import json
with open(os.path.join(ROOT, "training_history.json"), "w") as f:
    json.dump({"history": history, "best_val_clip_acc": best_val_acc,
                "n_train_clips": len(train_rows), "n_val_clips": len(val_rows)}, f, indent=2)

print(f"\nBest val clip-level accuracy: {best_val_acc:.3f}")
