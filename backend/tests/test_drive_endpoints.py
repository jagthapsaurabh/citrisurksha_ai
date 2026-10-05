"""Drive wiring: status endpoint reads storage + provenance correctly."""
import json
import os
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="cs-drive-"))
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ["UPLOAD_DIR"] = str(TMP / "uploads")
(TMP / "uploads").mkdir(parents=True, exist_ok=True)

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.routers.admin import drive_status  # noqa: E402


def test_drive_status_reads_storage():
    base = TMP / "training_images"
    (base / "citrus-thrips").mkdir(parents=True)
    (base / "citrus-thrips" / "ingested_x.jpg").write_bytes(b"1")
    (base / "citrus-thrips" / "other.jpg").write_bytes(b"2")
    (base / "provenance.jsonl").write_text(
        json.dumps({"source_dataset": "d1", "license": "MIT"}) + "\n" +
        json.dumps({"source_dataset": "d1", "license": "MIT"}) + "\n")
    out = drive_status(_admin=type("A", (), {"id": "x"})())
    assert out["provenance_records"] == 2
    assert {"pest_id": "citrus-thrips", "images": 1} in out["classes"]
    assert out["sources"].get("d1 (MIT)") == 2
