# First experimental drive training

```json
{
  "generated_at": "2026-10-05T21:34:36",
  "purpose": "Experimental transfer-learning run on open-licensed (MIT) proxy classes. NOT production.",
  "dataset": {
    "version": "dataset-drive-v1",
    "image_count": 32,
    "train_count": 22,
    "val_count": 4,
    "test_count": 6,
    "dups_removed": 0,
    "classes": [
      "yellow-citrus-thrips",
      "citrus-thrips",
      "cotton-aphid"
    ]
  },
  "cnn": {
    "status": "completed",
    "version": "citrisurksha-dataset-drive-v1-3a10ad34",
    "accuracy": 0.6,
    "macro_f1": 0.21428571428571427,
    "per_class": {
      "no-citrus-pest": {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "support": 0
      },
      "citrus-thrips": {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "support": 2
      },
      "cotton-aphid": {
        "precision": 0.75,
        "recall": 1.0,
        "f1": 0.8571428571428571,
        "support": 3
      },
      "yellow-citrus-thrips": {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "support": 0
      }
    },
    "seconds": 6.0
  },
  "yolo": {
    "status": "completed",
    "version": "yolo11-dataset-drive-v1-213436",
    "metrics": {
      "epochs": 1,
      "imgsz": 320,
      "duration_seconds": 10.8,
      "precision(B)": 0.0202,
      "recall(B)": 0.3333,
      "mAP50(B)": 0.0432,
      "mAP50-95(B)": 0.0237,
      "fitness": 0.0237
    },
    "bootstrap_labels": true,
    "seconds": 11.0
  },
  "honesty": "Proxy classes (generic thrips/aphids + Scirtothrips dorsalis) are transfer data only. Production models require expert-verified images of the 20 citrus pests."
}
```
