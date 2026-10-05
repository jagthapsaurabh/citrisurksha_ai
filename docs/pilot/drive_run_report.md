# First experimental drive training

```json
{
  "generated_at": "2026-10-05T21:59:02",
  "purpose": "Experimental transfer-learning run on open-licensed (MIT) proxy classes. NOT production.",
  "dataset": {
    "version": "dataset-drive-v2",
    "image_count": 60,
    "train_count": 42,
    "val_count": 7,
    "test_count": 11,
    "dups_removed": 0,
    "classes": [
      "citrus-leaf-miner",
      "no-citrus-pest",
      "citrus-thrips",
      "yellow-citrus-thrips",
      "oriental-spider-mite",
      "cotton-aphid"
    ]
  },
  "cnn": {
    "status": "completed",
    "version": "citrisurksha-dataset-drive-v2-89cdaed9",
    "accuracy": 0.4444444444444444,
    "macro_f1": 0.3277777777777778,
    "per_class": {
      "no-citrus-pest": {
        "precision": 0.6666666666666666,
        "recall": 1.0,
        "f1": 0.8,
        "support": 2
      },
      "citrus-leaf-miner": {
        "precision": 0.3333333333333333,
        "recall": 1.0,
        "f1": 0.5,
        "support": 1
      },
      "citrus-thrips": {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "support": 1
      },
      "cotton-aphid": {
        "precision": 0.5,
        "recall": 1.0,
        "f1": 0.6666666666666666,
        "support": 1
      },
      "oriental-spider-mite": {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "support": 0
      },
      "yellow-citrus-thrips": {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "support": 4
      }
    },
    "seconds": 15.8
  },
  "yolo": {
    "status": "completed",
    "version": "yolo11-dataset-drive-v2-215902",
    "metrics": {
      "epochs": 2,
      "imgsz": 192,
      "duration_seconds": 14.1,
      "precision(B)": 0.591,
      "recall(B)": 0.4831,
      "mAP50(B)": 0.3473,
      "mAP50-95(B)": 0.2509,
      "fitness": 0.2509
    },
    "bootstrap_labels": true,
    "seconds": 14.3
  },
  "honesty": "Proxy classes (generic thrips/aphids + Scirtothrips dorsalis) are transfer data only. Production models require expert-verified images of the 20 citrus pests."
}
```
