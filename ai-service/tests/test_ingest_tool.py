"""Post-step-12 ops tooling test: labelled-drive ingestion with dedupe + provenance."""
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

SPEC = importlib.util.spec_from_file_location(
    "ingest_tool", Path(__file__).resolve().parents[2] / "scripts" / "ingest_labelled_images.py")
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


def make(path: Path, color, seed=0):
    rng = np.random.default_rng(seed)
    arr = np.zeros((64, 64, 3), np.uint8)
    arr[:] = color
    arr = arr + rng.integers(0, 20, arr.shape).astype(np.uint8)
    Image.fromarray(arr).save(path)


def test_ingest_copies_dedupes_and_provenance(tmp_path):
    src = tmp_path / "src"
    (src / "citrus-psyllid").mkdir(parents=True)
    (src / "not-a-pest-class").mkdir()
    make(src / "citrus-psyllid" / "a.jpg", (150, 60, 60), 1)
    make(src / "citrus-psyllid" / "b.jpg", (150, 60, 60), 1)   # same content => dupe
    make(src / "citrus-psyllid" / "c.jpg", (60, 150, 60), 2)
    (src / "citrus-psyllid" / "tiny.jpg").write_bytes(b"\xff\xd8\xff" + b"0" * 10)  # too small
    (src / "not-a-pest-class" / "x.jpg").write_bytes(b"junk")

    dest = tmp_path / "store"
    prov = dest / "provenance.jsonl"
    rep = tool.ingest(src, dest, prov, dry_run=False)

    assert rep["classes"]["citrus-psyllid"]["copied"] == 2      # a + c, b deduped
    assert rep["classes"]["citrus-psyllid"]["dupes"] == 1
    assert rep["classes"]["citrus-psyllid"]["invalid"] == 1
    assert (dest / "citrus-psyllid").exists()
    lines = prov.read_text().strip().splitlines()
    assert len(lines) == 2
    import json
    rec = json.loads(lines[0])
    assert rec["verified"] is False and rec["pest_id"] == "citrus-psyllid"
    assert rec["sha256"] and rec["dhash"] is not None
    assert not (dest / "not-a-pest-class").exists()

    # dry-run writes nothing
    rep2 = tool.ingest(src, tmp_path / "store2", tmp_path / "p2.jsonl", dry_run=True)
    assert rep2["copied"] == 2 and not (tmp_path / "store2" / "citrus-psyllid").exists()
