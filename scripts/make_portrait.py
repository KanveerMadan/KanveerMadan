"""Photo -> line-art ASCII portrait inside a terminal window SVG (edges, not shading, so it reads small).

Usage: python scripts/make_portrait.py photo.jpg [--cols 64]
Needs: pip install pillow numpy opencv-python-headless "rembg[cpu]"
"""
import argparse
import os
from xml.sax.saxutils import escape

import cv2
import numpy as np
from PIL import Image
from rembg import new_session, remove

W, H = 430, 430                        # window size; matches stats card height
BG, FG, DIM = "#0d1117", "#c9d1d9", "#6e7681"
CHAR_ASPECT = 0.6
FILL = " .:-=+*#"                       # sparse texture ramp for dark masses (hair, beard)
EDGE = "-\\|/"
CROP = 0.8                              # keep top 80% of the figure                          # glyph by edge direction: 0, 45, 90, 135 degrees


def load(path):
    cut = np.array(remove(Image.open(path).convert("RGBA"), session=new_session("u2net_human_seg")))  # 170MB model
    gray = cv2.cvtColor(cut[..., :3], cv2.COLOR_RGB2GRAY)
    mask = cut[..., 3] >= 128
    ys, xs = np.where(mask)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    y1 = y0 + int((y1 - y0) * CROP)  # head + shoulders only
    return gray[y0:y1 + 1, x0:x1 + 1], mask[y0:y1 + 1, x0:x1 + 1]


def to_ascii(gray, mask, cols):
    h, w = gray.shape
    rows = round(cols * h / w * CHAR_ASPECT)
    g = cv2.createCLAHE(2.0, (8, 8)).apply(gray)
    for _ in range(4):  # cartoonize: flatten fabric/turban texture, keep real contours
        g = cv2.bilateralFilter(g, 9, 40, 9)
    gx, gy = cv2.Sobel(g.astype(float), cv2.CV_64F, 1, 0), cv2.Sobel(g.astype(float), cv2.CV_64F, 0, 1)
    edges = cv2.Canny(g, 70, 160) > 0
    edges |= (cv2.Canny(mask.astype(np.uint8) * 255, 50, 150) > 0)  # always draw the silhouette
    ch, cw = h / rows, w / cols
    out = []
    for r in range(rows):
        line = []
        for c in range(cols):
            ys, xs = slice(int(r * ch), max(int((r + 1) * ch), int(r * ch) + 1)), slice(int(c * cw), max(int((c + 1) * cw), int(c * cw) + 1))
            if mask[ys, xs].mean() < 0.3:
                line.append(" ")
                continue
            e = edges[ys, xs]
            if e.mean() > 0.1:
                ang = np.degrees(np.arctan2(gy[ys, xs][e].mean(), gx[ys, xs][e].mean())) + 90  # edge runs perpendicular to gradient
                line.append(EDGE[int(((ang % 180) + 22.5) // 45) % 4])
            else:
                dark = 1 - g[ys, xs].mean() / 255  # only genuinely dark masses (hair, beard) get texture
                line.append(FILL[min(len(FILL) - 1, int(max(0, dark - 0.6) / 0.4 * len(FILL)))])
        out.append("".join(line).rstrip())
    return out


def svg(lines, cols, user):
    pad, top, foot = 18, 40, 30
    fs = min((W - 2 * pad) / (cols * CHAR_ASPECT), (H - top - foot) / len(lines))  # fit both ways, keep aspect
    lh = fs
    pad = (W - max(map(len, lines)) * fs * CHAR_ASPECT) / 2  # centre horizontally
    static = os.environ.get("STATIC") == "1"
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         "" if static else "<style>.r{opacity:0;animation:p .01s forwards}@keyframes p{to{opacity:1}}"
         ".k{animation:b 1s steps(1) infinite}@keyframes b{50%{opacity:0}}</style>",
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="#30363d"/>',
         '<circle cx="18" cy="16" r="5" fill="#ff5f56"/><circle cx="34" cy="16" r="5" fill="#ffbd2e"/><circle cx="50" cy="16" r="5" fill="#27c93f"/>',
         f'<text x="{W / 2}" y="20" text-anchor="middle" font-family="ui-monospace,Menlo,Consolas,monospace" font-size="11" fill="{DIM}">{user}: ~/portrait.sh</text>',
         f'<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="{fs:.2f}" fill="{FG}" xml:space="preserve">']
    x0 = pad
    for i, ln in enumerate(lines):
        if not ln:
            continue
        cls = "" if static else f' class="r" style="animation-delay:{i * 0.035:.2f}s"'  # prints top -> bottom
        ind = len(ln) - len(ln.lstrip())  # renderers drop leading spaces, so indent with x instead
        ln = ln.lstrip()
        o.append(f'<text x="{x0 + ind * fs * CHAR_ASPECT:.2f}" y="{top + lh * (i + 0.8):.2f}" textLength="{len(ln) * fs * CHAR_ASPECT:.2f}" '
                 f'lengthAdjust="spacingAndGlyphs"{cls}>{escape(ln)}</text>')
    o.append("</g>")
    o.append(f'<text x="{pad}" y="{H - 12}" font-family="ui-monospace,Menlo,Consolas,monospace" font-size="11" fill="{DIM}">'
             f'{user} ~ $ render --mode ascii<tspan fill="{FG}"{"" if static else " class=\"k\""}> &#9612;</tspan></text>')
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--cols", type=int, default=64)
    ap.add_argument("--user", default="kanveer@github")
    ap.add_argument("--out", default="portrait.svg")
    a = ap.parse_args()
    gray, mask = load(a.photo)
    lines = to_ascii(gray, mask, a.cols)
    assert any(l.strip() for l in lines), "no figure found in photo"
    with open(a.out, "w") as f:
        f.write(svg(lines, a.cols, a.user))
    print(f"wrote {a.out} ({len(lines)} rows)")
