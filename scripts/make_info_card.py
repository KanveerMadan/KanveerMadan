"""Neofetch-style info card SVG. Edit INFO below, then: python scripts/make_info_card.py
STATIC=1 disables the fade-in.
"""
import os
from xml.sax.saxutils import escape

USER = "kanveer@github"
INFO = [
    ("Role", "B.Tech AI/ML @ VIPS Delhi, class of '27"),
    ("Now", "GeoWatch Copilot: satellite intelligence (CPS Lab)"),
    ("Research", "2 published papers"),
    ("Stack", "Python, PyTorch, FastAPI, React, Earth Engine"),
    ("Live", "GaitScan, GreenPrint, ResQBot"),
    ("Building", "Vaulta: AI personal finance for India"),
    ("Into", "Remote sensing, CV, LLM agents, RAG"),
    ("Next", "MS in AI/ML"),
]
WIDTH, PAD, LH, FS = 490, 22, 24, 14
BG, FG, KEY, DIM = "#0d1117", "#c9d1d9", "#39d353", "#6e7681"
SWATCHES = ["#ff7b72", "#ffa657", "#d29922", "#39d353", "#58a6ff", "#bc8cff", "#c9d1d9"]


def render():
    static = os.environ.get("STATIC") == "1"
    body_top = 44
    rows = [(USER, None), ("-" * len(USER), None)] + INFO
    height = body_top + LH * (len(rows) + 1) + 30
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}">',
           "<style>.l{opacity:0;animation:in .4s ease-out forwards}"
           "@keyframes in{from{opacity:0;transform:translateX(-6px)}to{opacity:1;transform:none}}</style>"
           if not static else "",
           f'<rect width="100%" height="100%" rx="8" fill="{BG}"/>',
           # title bar
           f'<circle cx="20" cy="18" r="6" fill="#ff5f56"/><circle cx="40" cy="18" r="6" fill="#ffbd2e"/>'
           f'<circle cx="60" cy="18" r="6" fill="#27c93f"/>',
           f'<text x="{WIDTH / 2}" y="22" text-anchor="middle" font-family="ui-monospace,Menlo,Consolas,monospace" '
           f'font-size="12" fill="{DIM}">~ $ neofetch</text>',
           f'<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="{FS}" xml:space="preserve">']
    for i, (k, v) in enumerate(rows):
        y = body_top + LH * (i + 1)
        cls = "" if static else f' class="l" style="animation-delay:{0.6 + i * 0.12:.2f}s"'
        if v is None:  # header + underline
            out.append(f'<text x="{PAD}" y="{y}" fill="{KEY if i == 0 else DIM}"{cls}>{escape(k)}</text>')
        else:
            out.append(f'<text x="{PAD}" y="{y}"{cls}><tspan fill="{KEY}">{escape(k)}</tspan>'
                       f'<tspan fill="{FG}">: {escape(v)}</tspan></text>')
    y = body_top + LH * (len(rows) + 1) - 4
    cls = "" if static else f' class="l" style="animation-delay:{0.6 + len(rows) * 0.12:.2f}s"'
    out.append(f'<g{cls}>' + "".join(
        f'<rect x="{PAD + j * 26}" y="{y}" width="22" height="14" rx="2" fill="{c}"/>' for j, c in enumerate(SWATCHES)) + "</g>")
    out.append("</g></svg>")
    return "\n".join(out)


if __name__ == "__main__":
    with open("info-card.svg", "w") as f:
        f.write(render())
    print("wrote info-card.svg")
