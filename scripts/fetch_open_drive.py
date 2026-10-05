"""Collect open-licensed transfer-class images for experimental training runs.

Sources (licenses recorded in provenance):
  * IP102-format insect-pest dataset (MIT) - proxy classes:
      93 Scirtothrips dorsalis -> yellow-citrus-thrips (true citrus thrips)
      55 Thrips                -> citrus-thrips  (proxy, marked)
      33 longlegged spider mite-> oriental-spider-mite (proxy, marked)
      25 Aphids                -> cotton-aphid  (proxy, marked)
  * someoneskilled/leafminer (Apache-2.0) - real citrus leaf miner damage and
    healthy citrus leaves (negative class).

Production models still require expert-verified citrus images per
docs/RELEASE_RUNBOOK.md.

  python3 scripts/fetch_open_drive.py <out_dir> [--per-class N] [--source ip102|leafminer|all]
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

DATASET = "EnmmmmOvO/insect-pest-dataset"
LABEL_MAP = {93: ("yellow-citrus-thrips", "Scirtothrips dorsalis (true citrus thrips)"),
             55: ("citrus-thrips", "generic Thrips (proxy, marked)"),
             33: ("oriental-spider-mite", "longlegged spider mite (proxy, marked)"),
             25: ("cotton-aphid", "generic aphids (proxy, marked)")}

LEAFMINER_BASE = "https://huggingface.co/datasets/someoneskilled/leafminer/resolve/main/train"
LEAFMINER_MAP = {"leafminer": "citrus-leaf-miner", "healthy": "no-citrus-pest"}


def fetch_rows(offset: int, length: int = 100):
    url = (f"https://datasets-server.huggingface.co/rows?dataset={DATASET}"
           f"&config=default&split=validation&offset={offset}&length={length}")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(10 * (attempt + 1))


def fetch_ip102(out: Path, per_class: int, prov: list, offset: int = 0, max_pages: int = 40) -> dict:
    counts = {v[0]: len(list((out / v[0]).glob("*.jpg"))) for v in LABEL_MAP.values()}
    off = offset
    for _ in range(max_pages):
        try:
            data = fetch_rows(off)
        except Exception as exc:
            print("rows fetch failed at", off, exc)
            break
        rows = data.get("rows", [])
        if not rows:
            break
        for item in rows:
            row = item["row"]
            label = int(row["label"])
            if label not in LABEL_MAP:
                continue
            our_id, note = LABEL_MAP[label]
            if counts[our_id] >= per_class:
                continue
            dest = out / our_id / f"{our_id}_{counts[our_id]:02d}.jpg"
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                urllib.request.urlretrieve(row["image"]["src"], dest)
            except Exception as exc:
                print("download failed", str(row["image"]["src"])[:80], exc)
                continue
            counts[our_id] += 1
            prov.append({"file": str(dest), "source_dataset": DATASET, "license": "MIT",
                         "ip102_label": label, "mapped_to": our_id, "note": note,
                         "source_url": row["image"]["src"],
                         "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")})
        off += len(rows)
        if all(c >= per_class for c in counts.values()):
            break
        time.sleep(2.0)
    return counts


def fetch_leafminer(out: Path, per_class: int, prov: list) -> dict:
    counts = {v: len(list((out / v).glob("*.jpg"))) for v in LEAFMINER_MAP.values()}
    for folder, our_id in LEAFMINER_MAP.items():
        if counts[our_id] >= per_class:
            continue
        url = f"https://huggingface.co/api/datasets/someoneskilled/leafminer/tree/main/train/{folder}"
        with urllib.request.urlopen(url, timeout=60) as r:
            entries = [e for e in json.load(r) if e["type"] == "file"]
        for e in entries:
            if counts[our_id] >= per_class:
                break
            fname = urllib.parse.quote(e["path"].split("/")[-1])
            dest = out / our_id / f"{our_id}_lm{counts[our_id]:02d}.jpg"
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                urllib.request.urlretrieve(f"{LEAFMINER_BASE}/{folder}/{fname}", dest)
            except Exception as exc:
                print("download failed", e["path"], exc)
                continue
            counts[our_id] += 1
            prov.append({"file": str(dest), "source_dataset": "someoneskilled/leafminer",
                         "license": "Apache-2.0", "mapped_to": our_id,
                         "note": "citrus leaf miner damage" if folder == "leafminer" else "healthy citrus (negative)",
                         "source_url": f"{LEAFMINER_BASE}/{folder}/{fname}",
                         "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")})
            time.sleep(0.3)
    return counts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--per-class", type=int, default=12)
    ap.add_argument("--max-pages", type=int, default=40)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--source", choices=["ip102", "leafminer", "all"], default="all")
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    prov: list = []
    if args.source in ("leafminer", "all"):
        print("leafminer collected:", fetch_leafminer(out, args.per_class, prov))
    if args.source in ("ip102", "all"):
        print("collected:", fetch_ip102(out, args.per_class, prov, offset=args.offset, max_pages=args.max_pages))
    (out / "open_drive_provenance.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in prov) + "\n", encoding="utf-8")
    return 0 if prov else 1


if __name__ == "__main__":
    raise SystemExit(main())
