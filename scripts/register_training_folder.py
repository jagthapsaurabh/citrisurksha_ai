"""Register images placed in storage/training_images/<pest_id>/ as verified TrainingImage rows.

Run from project root or backend folder:
  python scripts/register_training_folder.py

This does not copy files; it stores their paths in DB for Train AI.
"""
from pathlib import Path
import sys, os
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.db import SessionLocal, Base, engine
from app.models import TrainingImage, Pest

IMG_EXT={'.jpg','.jpeg','.png','.webp'}
BASE=ROOT/'storage'/'training_images'
Base.metadata.create_all(bind=engine)
db=SessionLocal()
try:
    count=0
    for folder in BASE.iterdir() if BASE.exists() else []:
        if not folder.is_dir(): continue
        pest_id=folder.name
        if pest_id!='no-citrus-pest' and not db.get(Pest,pest_id):
            print('Skipping unknown pest folder', pest_id); continue
        for img in folder.rglob('*'):
            if img.suffix.lower() not in IMG_EXT: continue
            path=str(img.resolve())
            exists=db.query(TrainingImage).filter(TrainingImage.image_path==path).first()
            if not exists:
                db.add(TrainingImage(image_path=path,pest_id=pest_id,stage='unknown',verified=True,source='folder-import'))
                count+=1
    db.commit()
    print('Registered images:', count)
finally:
    db.close()
