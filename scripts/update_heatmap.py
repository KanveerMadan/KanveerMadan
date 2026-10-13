"""Fetch the public contribution calendar and render an animated heatmap SVG.

Usage: python scripts/update_heatmap.py [username]          (default: KanveerMadan)
       python scripts/update_heatmap.py --from-json data.json  (render only)
Writes data/contributions.json and contrib-heatmap.svg. Run daily by the GitHub Action.
"""
import json
import os
import re
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
CELL, GAP, PAD, TOP = 12, 3, 20, 46
BG, DIM, FG = "#0d1117", "#6e7681", "#c9d1d9"


def fetch(user):
    # shortcut: scrapes GitHub's undocumented calendar HTML (no token needed). If the markup changes
    # and this raises, switch to the GraphQL contributionsCollection API with the Action's GITHUB_TOKEN.
    r = requests.get(f"https://github.com/users/{user}/contributions", timeout=30,
                     headers={"User-Agent": "profile-heatmap"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tips = {t.get("for"): t.get_text(" ", strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        m = re.match(r"([\d,]+) contribution", tips.get(td.get("id"), ""))
        days.append({"date": td["data-date"], "level": int(td.get("data-level", 0)),
                     "count": int(m.group(1).replace(",", "")) if m else 0})
    if not days:
        raise RuntimeError("no calendar cells found: GitHub markup changed")
    days.sort(key=lambda d: d["date"])
    h2 = soup.find("h2", string=re.compile("contribution"))
    total = int(re.sub(r"\D", "", h2.get_text())) if h2 else sum(d["count"] for d in days)
    return {"user": user, "total": total, "days": days}


def render(data):
    days = data["days"]
    first = date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday
    weeks = (offset + len(days) + 6) // 7
    width = 2 * PAD + weeks * (CELL + GAP) - GAP
    height = TOP + 7 * (CELL + GAP) - GAP + 34
    static = os.environ.get("STATIC") == "1"
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           "" if static else "<style>.c{opacity:0;animation:d .35s ease-out forwards}"
           "@keyframes d{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}</style>",
           f'<rect width="100%" height="100%" rx="8" fill="{BG}"/>',
           f'<text x="{PAD}" y="28" font-family="ui-monospace,Menlo,Consolas,monospace" font-size="13" fill="{FG}">'
           f'{data["total"]:,} contributions in the last year</text>']
    for i, d in enumerate(days):
        w, wd = divmod(offset + i, 7)
        x, y = PAD + w * (CELL + GAP), TOP + wd * (CELL + GAP)
        anim = "" if static else f' class="c" style="animation-delay:{(w + wd) * 0.018:.3f}s"'  # diagonal sweep
        out.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                   f'fill="{PALETTE[min(d["level"], 4)]}"{anim}><title>{d["count"]} on {d["date"]}</title></rect>')
    ly = height - 16
    sx = width - PAD - 36 - 5 * (CELL + GAP)  # leave room for "More" on the right
    out.append(f'<text x="{sx - 6}" y="{ly + 10}" text-anchor="end" font-family="ui-monospace,Menlo,monospace" '
               f'font-size="11" fill="{DIM}">Less</text>')
    for j, c in enumerate(PALETTE):
        out.append(f'<rect x="{sx + j * (CELL + GAP)}" y="{ly}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>')
    out.append(f'<text x="{width - PAD}" y="{ly + 10}" text-anchor="end" font-family="ui-monospace,Menlo,monospace" '
               f'font-size="11" fill="{DIM}">More</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--from-json"]:
        data = json.load(open(args[1]))
    else:
        data = fetch(args[0] if args else "KanveerMadan")
        os.makedirs("data", exist_ok=True)
        json.dump(data, open("data/contributions.json", "w"), indent=1)
    with open("contrib-heatmap.svg", "w") as f:
        f.write(render(data))
    print(f"wrote contrib-heatmap.svg ({len(data['days'])} days, {data['total']} contributions)")
