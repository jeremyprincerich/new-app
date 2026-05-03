"""Convert BOOK1/*.heic to BOOK1/_jpg/*.jpg, downscaled for OCR.

Run from new-app/: `python tools/heic_to_jpg.py`
"""
from pathlib import Path
from PIL import Image
import pillow_heif

pillow_heif.register_heif_opener()

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "BOOK1"
DST = SRC / "_jpg"
DST.mkdir(exist_ok=True)

MAX_SIDE = 1800

heics = sorted(SRC.glob("*.heic"))
print(f"Found {len(heics)} .heic files")
for i, p in enumerate(heics, 1):
    out = DST / (p.stem + ".jpg")
    if out.exists():
        print(f"[{i}/{len(heics)}] skip {out.name}")
        continue
    img = Image.open(p)
    img = img.convert("RGB")
    w, h = img.size
    scale = min(1.0, MAX_SIDE / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    img.save(out, "JPEG", quality=85, optimize=True)
    print(f"[{i}/{len(heics)}] {p.name} -> {out.name} ({img.size[0]}x{img.size[1]})")
print("done")
