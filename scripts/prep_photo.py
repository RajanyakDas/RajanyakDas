#!/usr/bin/env python3
"""
prep_photo.py — turn a normal photo into a clean, high-contrast grayscale
source ready for ASCII conversion.

Steps:
  1. Remove the background with rembg so only the subject remains.
  2. Boost local contrast with CLAHE (adaptive histogram equalization) —
     this is what gives a flatly-lit face real highlights and shadows.
  3. Composite onto pure white so the background maps to the blank end
     of the ASCII ramp (white -> space).

Usage:
    python scripts/prep_photo.py source-photo.jpg
Writes:
    source-prepped.png
"""
import sys
import numpy as np
import cv2
from PIL import Image
from rembg import remove


def prep(in_path: str, out_path: str = "source-prepped.png") -> None:
    with open(in_path, "rb") as f:
        input_bytes = f.read()

    # 1. Remove background -> RGBA with alpha mask around the subject
    cutout_bytes = remove(input_bytes)
    cutout = Image.open(__import__("io").BytesIO(cutout_bytes)).convert("RGBA")

    # 2. Composite onto pure white background
    white_bg = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, cutout).convert("RGB")

    # 3. Boost local contrast with CLAHE on the L channel (Lab color space)
    arr = np.array(composited)
    lab = cv2.cvtColor(arr, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l_eq = clahe.apply(l)
    lab_eq = cv2.merge((l_eq, a, b))
    contrasted = cv2.cvtColor(lab_eq, cv2.COLOR_LAB2RGB)

    # 4. Convert to grayscale, keep background pure white
    gray = cv2.cvtColor(contrasted, cv2.COLOR_RGB2GRAY)

    # Use the alpha mask from the cutout to force background back to white
    # (CLAHE can slightly grey flat white regions)
    alpha = np.array(cutout)[:, :, 3]
    gray[alpha < 10] = 255

    Image.fromarray(gray).save(out_path)
    print(f"wrote {out_path}  ({gray.shape[1]}x{gray.shape[0]})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python prep_photo.py <source-photo.jpg>")
        sys.exit(1)
    prep(sys.argv[1])
