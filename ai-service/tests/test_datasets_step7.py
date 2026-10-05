"""Upgrade step 7 (ai-service): dataset versioning, frozen test set,
near-duplicate detection, and non-activating model registration."""
import os
import sys
import tempfile

os.makedirs("/home/user/.tmp", exist_ok=True)

STORE = tempfile.mkdtemp(prefix="cs-ms7-", dir="/home/user/.tmp")
os.environ["MODEL_STORE"] = STORE
os.environ.setdefault("DINOV2_ENABLED", "false")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from PIL import Image

from app import model_registry as reg
from app.datasets import build_dataset, dhash, hamming, list_datasets, load_manifest, train_val_ids


def make_img(color, seed=0, size=96):
    rng = np.random.default_rng(seed)
    arr = np.zeros((size, size, 3), np.uint8)
    arr[:] = color
    arr += rng.integers(0, 18, arr.shape).astype(np.uint8)
    return Image.fromarray(arr)


def records(tmp_path):
    recs = []
    colors = {"citrus-psyllid": (60, 120, 150), "citrus-leaf-miner": (40, 130, 60), "no-citrus-pest": (200, 200, 200)}
    for cls, col in colors.items():
        for i in range(6):
            p = tmp_path / f"{cls}-{i}.png"
            make_img(col, seed=i).save(p)
            recs.append({"image_id": p.stem, "image_path": str(p), "pest_id": cls})
    return recs


def test_dhash_near_duplicates(tmp_path):
    a = make_img((60, 120, 150), seed=1)
    b = a.copy()
    px = np.array(b)
    px[0:2, 0:2] = px[0:2, 0:2] ^ 1          # 1-LSB noise: perceptually identical
    ha, hb = dhash(a), dhash(Image.fromarray(px))
    assert hamming(ha, hb) <= 6
    c = make_img((200, 200, 200), seed=9)
    assert hamming(ha, dhash(c)) > 6


def test_build_dataset_frozen_test_and_dedupe(tmp_path):
    recs = records(tmp_path)
    dup = recs[0].copy()
    dup["image_id"] = "dup-of-0"
    dup["image_path"] = recs[0]["image_path"]   # exact duplicate
    recs.append(dup)

    m1 = build_dataset(recs, "dataset-v1")
    assert m1["dups_removed"] >= 1
    assert m1["image_count"] == len(recs) - m1["dups_removed"]
    assert m1["test_count"] >= 1 and m1["train_count"] >= 1
    test_ids = set(m1["frozen_test_ids"])
    splits = m1["splits"]
    assert not (test_ids & {i for i, s in splits.items() if s in ("train", "val")}), "test leaked into train/val"
    assert m1["class_distribution"]["citrus-psyllid"] == 6

    # second version inherits the frozen test set
    extra = tmp_path / "extra.png"
    make_img((40, 130, 60), seed=42).save(extra)
    recs2 = [r for r in recs if r["image_id"] != "dup-of-0"] + [
        {"image_id": "extra", "image_path": str(extra), "pest_id": "citrus-leaf-miner"}]
    m2 = build_dataset(recs2, "dataset-v2", previous_frozen_test_ids=m1["frozen_test_ids"])
    assert m2["frozen_inherited"] is True
    assert set(m2["frozen_test_ids"]) <= set(m1["frozen_test_ids"])
    s2 = m2["splits"]
    assert not (set(m2["frozen_test_ids"]) & {i for i, s in s2.items() if s in ("train", "val")})
    assert s2.get("extra") in ("train", "val")

    assert load_manifest("dataset-v1")["version"] == "dataset-v1"
    assert {d["version"] for d in list_datasets()} >= {"dataset-v1", "dataset-v2"}
    assert train_val_ids(m2) == {i for i, s in s2.items() if s in ("train", "val")}


def test_register_does_not_activate_by_default():
    before = reg.active_model().get("version")
    reg.register_model("step7-test-v1", {"accuracy": 0.5}, [{"id": "x"}],
                       checkpoint_path=None, status="testing", activate=False)
    assert reg.active_model().get("version") == before      # production untouched
    versions = {v["version"] for v in reg.list_versions()}
    assert "step7-test-v1" in versions


def test_activate_requires_checkpoint(tmp_path):
    ckpt = tmp_path / "model.pt"
    ckpt.write_bytes(b"fake")
    reg.register_model("step7-test-v2", {"accuracy": 0.6}, [{"id": "x"}],
                       checkpoint_path=str(ckpt), status="testing", activate=False)
    meta = reg.activate_version("step7-test-v2")
    assert reg.active_model().get("version") == "step7-test-v2"
    assert meta["checkpoint_path"] == str(ckpt)
    try:
        reg.activate_version("does-not-exist")
        raise AssertionError("should have raised")
    except ValueError:
        pass
