"""Collect open-licensed (MIT) transfer-class images for the FIRST experimental
training run, from the IP102-format insect-pest dataset on Hugging Face.

Mapping (documented honestly - transfer classes, NOT citrus-field verified):
  IP102 93  Scirtothrips dorsalis  -> yellow-citrus-thrips  (true citrus thrips)
  IP102 55  Thrips                 -> citrus-thrips         (proxy, marked)
  IP102 25  Aphids                 -> cotton-aphid          (proxy, marked)

Downloads into <out>/<our_class>/* plus provenance jsonl. Production models
still require expert-verified citrus images per docs/RELEASE_RUNBOOK.md.

  python3 scripts/fetch_open_drive.py <out_dir> [--per-class 12]
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path

DATASET = "EnmmmmOvO/insect-pest-dataset"
LABEL_MAP = {93: ("yellow-citrus-thrips", "Scirtothrips dorsalis (true citrus thrips)"),
             55: ("citrus-thrips", "generic Thrips (proxy, marked)"),
             25: ("cotton-aphid", "generic aphids (proxy, marked)")}


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--per-class", type=int, default=12)
    ap.add_argument("--max-pages", type=int, default=40)
    ap.add_argument("--offset", type=int, default=0)
    args = ap.parse_args()
    out = Path(args.out_dir)
    counts = {v[0]: len(list((out / v[0]).glob("*.jpg"))) for v in LABEL_MAP.values()}
    prov = []
    offset = args.offset
    for page in range(args.max_pages):
        try:
            data = fetch_rows(offset)
        except Exception as exc:
            print("rows fetch failed at", offset, exc)
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
            if counts[our_id] >= args.per_class:
                continue
            src = row["image"]["src"]
            dest = out / our_id / f"{our_id}_{counts[our_id]:02d}.jpg"
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                urllib.request.urlretrieve(src, dest)
            except Exception as exc:
                print("download failed", src[:80], exc)
                continue
            counts[our_id] += 1
            prov.append({"file": str(dest), "source_dataset": DATASET, "license": "MIT",
                         "ip102_label": label, "mapped_to": our_id, "note": note,
                         "source_url": src, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")})
        offset += len(rows)
        if all(c >= args.per_class for c in counts.values()):
            break
        time.sleep(2.0)
    (out.parent if not out.exists() else out).mkdir(parents=True, exist_ok=True)
    (out / "open_drive_provenance.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in prov) + "\n", encoding="utf-8")
    print("collected:", counts)
    return 0 if sum(counts.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
