"""Animated name banner: python scripts/make_banner.py [theme]   (themes: navy, plum, emerald; STATIC=1 = no animation)"""
import os
import sys

NAME, GREET = "Kanveer Madan,", "enchanté!"
ROLE = "AI/ML ENGINEER  ·  PUBLISHED RESEARCHER  ·  SHIPPING ML TO PRODUCTION"
W, H = 860, 230
SERIF = "'Playfair Display','Didot','Bodoni 72',Georgia,'Times New Roman',serif"
THEMES = {  # background gradient stops, gold text stops, accent line
    "navy":    (("#0b1a3a", "#13254f", "#0a1430"), ("#f7e7a1", "#d4af37", "#a8862a")),
    "plum":    (("#2a0d3a", "#3d1457", "#1e0a2b"), ("#f9e6b3", "#e0b450", "#b8862b")),
    "emerald": (("#062b22", "#0b3d30", "#04201a"), ("#f3e3a3", "#cfa84a", "#9c7a2c")),
}


def banner(theme):
    bg, gold = THEMES[theme]
    static = os.environ.get("STATIC") == "1"
    anim = "" if static else (
        "<style>.n{opacity:0;animation:u 1s ease-out forwards}"
        ".g{opacity:0;animation:u 1s ease-out .6s forwards}"
        ".r{opacity:0;animation:u .8s ease-out 1.2s forwards}"
        "@keyframes u{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}</style>")
    shimmer = "" if static else (  # slow gold sheen sweeping across the name
        '<animateTransform attributeName="gradientTransform" type="translate" from="-1 0" to="1 0" '
        'dur="4s" begin="1.5s" repeatCount="indefinite"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{anim}
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{bg[0]}"/><stop offset=".55" stop-color="{bg[1]}"/><stop offset="1" stop-color="{bg[2]}"/></linearGradient>
<linearGradient id="gold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{gold[0]}"/><stop offset=".55" stop-color="{gold[1]}"/><stop offset="1" stop-color="{gold[2]}"/></linearGradient>
<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0"><stop offset=".35" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".55"/><stop offset=".65" stop-color="#fff" stop-opacity="0"/>{shimmer}</linearGradient>
</defs>
<rect width="{W}" height="{H}" rx="14" fill="url(#bg)"/>
<rect x="10" y="10" width="{W - 20}" height="{H - 20}" rx="9" fill="none" stroke="{gold[1]}" stroke-opacity=".55"/>
<rect x="15" y="15" width="{W - 30}" height="{H - 30}" rx="6" fill="none" stroke="{gold[1]}" stroke-opacity=".25"/>
<g class="n"><text x="{W / 2}" y="112" text-anchor="middle" font-family="{SERIF}" font-size="58" font-weight="700" fill="url(#gold)">{NAME}</text>
<text x="{W / 2}" y="112" text-anchor="middle" font-family="{SERIF}" font-size="58" font-weight="700" fill="url(#sheen)">{NAME}</text></g>
<text class="g" x="{W / 2}" y="160" text-anchor="middle" font-family="{SERIF}" font-size="40" font-style="italic" fill="url(#gold)">{GREET}</text>
<g class="r"><line x1="{W / 2 - 150}" y1="180" x2="{W / 2 + 150}" y2="180" stroke="{gold[1]}" stroke-opacity=".5"/>
<text x="{W / 2}" y="202" text-anchor="middle" font-family="{SERIF}" font-size="12.5" letter-spacing="2.5" fill="{gold[0]}" fill-opacity=".85">{ROLE}</text></g>
</svg>'''


if __name__ == "__main__":
    t = sys.argv[1] if len(sys.argv) > 1 else "navy"
    with open("banner.svg", "w") as f:
        f.write(banner(t))
    print(f"wrote banner.svg ({t})")
