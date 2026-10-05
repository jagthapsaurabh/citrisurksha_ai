"""Dataset source helper for CitriSurksha.

This script intentionally does not auto-download huge datasets by default. It writes a
manifest of approved open-source sources and shows commands for maintainers. Use after
license review, then place curated images into backend/admin upload flow or create a
manifest consumed by /admin/ai/train.
"""
import json
from pathlib import Path

SOURCES = [
    ("Citrus Pest Benchmark", "https://github.com/edsonbollis/Citrus-Pest-Benchmark"),
    ("IP102 Official", "https://github.com/xpwu95/IP102"),
    ("IP102 Kaggle", "https://www.kaggle.com/datasets/rtlmhjbn/ip02-dataset"),
    ("IP102 Annotated", "https://www.kaggle.com/datasets/parserpixy/ip102-dataset"),
    ("PlantVillage", "https://github.com/spMohanty/PlantVillage-Dataset"),
    ("Roboflow Citrus Pest", "https://universe.roboflow.com/search?q=citrus%20pest"),
    ("Roboflow Insect", "https://universe.roboflow.com/search?q=insect"),
    ("Open Images", "https://storage.googleapis.com/openimages/web/index.html"),
    ("TensorFlow Datasets", "https://www.tensorflow.org/datasets"),
    ("Hugging Face Plant Datasets", "https://huggingface.co/datasets?search=plant"),
]

out = Path(__file__).with_name("open_dataset_sources_manifest.json")
out.write_text(json.dumps([{"name": n, "url": u, "status": "registered_source_license_review_required"} for n, u in SOURCES], indent=2))
print(f"Wrote {out}")
print("Next: manually download/curate images, map labels to CitriSurksha 20 pest IDs, then upload via admin or training manifest.")
