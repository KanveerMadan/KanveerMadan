"""Photo -> monochrome ASCII portrait SVG that types itself in row by row.

Usage: python scripts/make_ascii_svg.py photo.jpg [--cols 100] [--out ascii-portrait.svg]
Background removal uses rembg if installed (pip install rembg); otherwise the photo is used as-is,
so shoot against a plain light wall if you skip it.
"""
import argparse
import os
from xml.sax.saxutils import escape

import cv2
import numpy as np
from PIL import Image

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); leading space clears the background
WIDTH = 370             # px, matches the left column in README.md
CHAR_ASPECT = 0.6       # monospace glyph width / font size
BG, FG = "#0d1117", "#c9d1d9"


def prep(path):
    img = Image.open(path).convert("RGBA")
    try:
        from rembg import remove
        img = remove(img)
    except ImportError:
        print("rembg not installed: skipping background removal")
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    gray = np.array(Image.alpha_composite(white, img).convert("L"))
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)


def to_rows(gray, cols):
    h, w = gray.shape
    rows = max(1, round(cols * h / w * CHAR_ASPECT))  # glyphs are taller than wide
    small = cv2.resize(gray, (cols, rows), interpolation=cv2.INTER_AREA)
    idx = ((255 - small.astype(int)) * (len(RAMP) - 1) // 255)  # dark pixel -> dense glyph
    lines = ["".join(RAMP[i] for i in row) for row in idx]
    # crop empty rows top/bottom so the face fills the frame
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def render(lines, cols):
    pad = 12
    fs = (WIDTH - 2 * pad) / (cols * CHAR_ASPECT)
    lh = fs * 1.0
    height = round(2 * pad + lh * len(lines))
    static = os.environ.get("STATIC") == "1"
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}">',
           f'<rect width="100%" height="100%" rx="8" fill="{BG}"/>',
           f'<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="{fs:.2f}" fill="{FG}" xml:space="preserve">']
    for i, line in enumerate(lines):
        y = pad + lh * (i + 0.8)
        top = pad + lh * i
        text = f'<text x="{pad}" y="{y:.2f}" textLength="{WIDTH - 2 * pad}" lengthAdjust="spacingAndGlyphs">{escape(line)}</text>'
        if static:
            out.append(text)
            continue
        # each row is revealed by a clip that wipes left -> right, rows staggered top -> bottom
        out.append(f'<clipPath id="r{i}"><rect x="0" y="{top:.2f}" width="0" height="{lh + 1:.2f}">'
                   f'<animate attributeName="width" from="0" to="{WIDTH}" begin="{i * 0.04:.2f}s" dur="0.35s" fill="freeze"/>'
                   f'</rect></clipPath>')
        out.append(f'<g clip-path="url(#r{i})">{text}</g>')
    out.append("</g></svg>")
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--cols", type=int, default=100)
    ap.add_argument("--out", default="ascii-portrait.svg")
    a = ap.parse_args()
    lines = to_rows(prep(a.photo), a.cols)
    assert lines, "image converted to all blank rows: check lighting / background"
    with open(a.out, "w") as f:
        f.write(render(lines, a.cols))
    print(f"wrote {a.out} ({len(lines)} rows)")
