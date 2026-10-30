#!/usr/bin/env python3
"""Resize/compress images under static/uploads in place.
Dimension-based skip makes it idempotent (never recompresses the same file
twice), so it is safe to run on every push without quality decay or loops.
Headshots (uploads/team) cap at 1000px; everything else at 2000px.
EXIF (including GPS) is stripped on any file it touches."""
import os
from PIL import Image, ImageOps

ROOT = "static/uploads"
EXTS = {".jpg", ".jpeg", ".png"}

def cap(path):
    return 1000 if "/team/" in path.replace("\\", "/") else 2000

changed = 0
for dp, _, files in os.walk(ROOT):
    for fn in files:
        ext = os.path.splitext(fn)[1].lower()
        if ext not in EXTS:
            continue
        p = os.path.join(dp, fn)
        try:
            im = Image.open(p)
        except Exception as e:
            print("skip (unreadable):", p, e); continue
        w, h = im.size
        mx = cap(p)
        if max(w, h) <= mx:           # already within size -> leave it alone (idempotent)
            continue
        im = ImageOps.exif_transpose(im)
        s = mx / max(w, h)
        im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
        if ext == ".png":
            im.save(p, "PNG", optimize=True)
        else:
            im.convert("RGB").save(p, "JPEG", quality=82, optimize=True, progressive=True)
        changed += 1
        print(f"optimized {p}  {w}x{h} -> {im.size[0]}x{im.size[1]}")
print(f"done — {changed} image(s) optimized")
