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

# A burst of 8 photos in the original capture session were saved upside-down.
# Rotate them 180° so the JPGs come out upright on every re-conversion.
UPSIDE_DOWN_180 = {
    "20260503_115225",
    "20260503_115229",
    "20260503_115239",
    "20260503_115243",
    "20260503_115254",
    "20260503_115259",
    "20260503_115313",
    "20260503_115327",
}

heics = sorted(SRC.glob("*.heic"))
print(f"Found {len(heics)} .heic files")
for i, p in enumerate(heics, 1):
    out = DST / (p.stem + ".jpg")
    if out.exists():
        print(f"[{i}/{len(heics)}] skip {out.name}")
        continue
    img = Image.open(p)
    img = img.convert("RGB")
    if p.stem in UPSIDE_DOWN_180:
        img = img.rotate(180, expand=True)
    w, h = img.size
    scale = min(1.0, MAX_SIDE / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    img.save(out, "JPEG", quality=85, optimize=True)
    print(f"[{i}/{len(heics)}] {p.name} -> {out.name} ({img.size[0]}x{img.size[1]})")
print("done")
