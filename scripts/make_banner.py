"""Name banner, wave style: python scripts/make_banner.py"""
TEXT = "Kanveer Madan, enchanté!"
W, H = 860, 210
SANS = "-apple-system,BlinkMacSystemFont,'Inter','Segoe UI',Helvetica,Arial,sans-serif"
BURGUNDY = ("#4a0d1c", "#7a1a33", "#a8344f")  # left -> right gradient

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="{BURGUNDY[0]}"/><stop offset=".5" stop-color="{BURGUNDY[1]}"/><stop offset="1" stop-color="{BURGUNDY[2]}"/>
</linearGradient></defs>
<path d="M0 0H{W}V172C700 190 560 205 420 200C280 196 140 192 0 206Z" fill="url(#bg)"/>
<path d="M0 182C160 196 300 204 470 196C620 189 760 178 {W} 168V196C700 206 520 214 360 210C220 206 100 200 0 196Z" fill="url(#bg)" opacity=".35"/>
<text x="{W / 2}" y="116" text-anchor="middle" font-family="{SANS}" font-size="58" font-weight="800" letter-spacing="-1.5" fill="#f6f3f4">{TEXT}</text>
</svg>'''

with open("banner.svg", "w") as f:
    f.write(svg)
print("wrote banner.svg")
