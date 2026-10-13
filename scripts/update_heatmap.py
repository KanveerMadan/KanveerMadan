"""Fetch the public contribution calendar; render contrib-heatmap.svg and stats-card.svg.

Usage: python scripts/update_heatmap.py [username]            (default: KanveerMadan)
       python scripts/update_heatmap.py --from-json data.json   (render only)
Run daily by .github/workflows/update-profile-art.yml.
"""
import json
import os
import re
import sys
from collections import OrderedDict
from datetime import date, timedelta
from xml.sax.saxutils import escape

import requests
from bs4 import BeautifulSoup

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
BG, BORDER, TILE, DIM, FG, GREEN = "#0d1117", "#30363d", "#161b22", "#6e7681", "#c9d1d9", "#39d353"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
STATIC = os.environ.get("STATIC") == "1"


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


def stats(data):
    days = data["days"]
    counts = [d["count"] for d in days]
    # longest streak (with range)
    best, run, best_end = 0, 0, None
    for i, c in enumerate(counts):
        run = run + 1 if c else 0
        if run > best:
            best, best_end = run, i
    # current streak: today may still be empty, so allow it to start from yesterday
    i = len(counts) - 1
    if i >= 0 and counts[i] == 0:
        i -= 1
    cur_end, cur = i, 0
    while i >= 0 and counts[i]:
        cur, i = cur + 1, i - 1
    active = sum(1 for c in counts if c)
    top = max(days, key=lambda d: d["count"])
    months = OrderedDict()
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
    return {
        "cur": cur, "cur_range": (days[cur_end - cur + 1]["date"], days[cur_end]["date"]) if cur else None,
        "long": best, "long_range": (days[best_end - best + 1]["date"], days[best_end]["date"]) if best else None,
        "total": data["total"], "active": active, "ndays": len(days),
        "best": top["count"], "best_date": top["date"],
        "avg": data["total"] / active if active else 0,
        "months": list(months.items())[-12:],
    }


def fmt(d):
    return date.fromisoformat(d).strftime("%b %-d")


def heatmap(data, cell=13, gap=3):
    days = data["days"]
    first = date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday
    weeks = (offset + len(days) + 6) // 7
    left, top = 34, 26
    width = left + weeks * (cell + gap) - gap + 4
    height = top + 7 * (cell + gap) - gap + 30
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
         "" if STATIC else "<style>.c{opacity:0;animation:d .35s ease-out forwards}"
         "@keyframes d{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}</style>",
         f'<g font-family="{MONO}" font-size="11" fill="{DIM}">']
    for wd, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        o.append(f'<text x="0" y="{top + wd * (cell + gap) + cell - 2}">{name}</text>')
    last_month = None
    for i, d in enumerate(days):
        w, wd = divmod(offset + i, 7)
        m = d["date"][5:7]
        if m != last_month and wd <= 1 and w < weeks - 1:  # label the first column of each month
            o.append(f'<text x="{left + w * (cell + gap)}" y="{top - 9}">{date.fromisoformat(d["date"]).strftime("%b")}</text>')
            last_month = m
    o.append(f'<text x="{left}" y="{height - 8}" fill="{FG}" font-weight="600">'
             f'{data["total"]:,} contributions in the last year</text></g>')
    for i, d in enumerate(days):
        w, wd = divmod(offset + i, 7)
        anim = "" if STATIC else f' class="c" style="animation-delay:{(w + wd) * 0.018:.3f}s"'  # diagonal sweep
        o.append(f'<rect x="{left + w * (cell + gap)}" y="{top + wd * (cell + gap)}" width="{cell}" height="{cell}" '
                 f'rx="2.5" fill="{PALETTE[min(d["level"], 4)]}"{anim}><title>{d["count"]} on {d["date"]}</title></rect>')
    o.append("</svg>")
    return "\n".join(o)


def stats_card(s, user, W=430, H=430):
    pad, gap = 14, 10
    tw = (W - 2 * pad - gap) / 2
    th = 62
    tiles = [
        ("current streak", f'{s["cur"]}', "day" if s["cur"] == 1 else "days", f'{fmt(s["cur_range"][0])} – {fmt(s["cur_range"][1])}' if s["cur_range"] else "start one today", True),
        ("longest streak", f'{s["long"]}', "day" if s["long"] == 1 else "days", f'{fmt(s["long_range"][0])} – {fmt(s["long_range"][1])}' if s["long_range"] else "", False),
        ("contributions", f'{s["total"]:,}', "", "in the last year", False),
        ("active days", f'{s["active"]}', f'/ {s["ndays"]}', f'{100 * s["active"] / s["ndays"]:.0f}% of the year', False),
        ("best day", f'{s["best"]}', "", fmt(s["best_date"]), False),
        ("avg / active day", f'{s["avg"]:.1f}', "", "contributions", False),
    ]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         "" if STATIC else "<style>.t{opacity:0;animation:f .4s ease-out forwards}"
         "@keyframes f{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}"
         ".b{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:g .6s ease-out forwards}"
         "@keyframes g{to{transform:scaleY(1)}}</style>",
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
         '<circle cx="18" cy="16" r="5" fill="#ff5f56"/><circle cx="34" cy="16" r="5" fill="#ffbd2e"/><circle cx="50" cy="16" r="5" fill="#27c93f"/>',
         f'<text x="{W / 2}" y="20" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{DIM}">stats</text>',
         f'<g font-family="{MONO}">']
    y0 = 34
    for k, (label, big, unit, sub, hot) in enumerate(tiles):
        x, y = pad + (k % 2) * (tw + gap), y0 + (k // 2) * (th + gap)
        a = "" if STATIC else f' class="t" style="animation-delay:{0.2 + k * 0.1:.1f}s"'
        o.append(f'<g{a}><rect x="{x}" y="{y}" width="{tw}" height="{th}" rx="6" fill="{TILE}" stroke="{BORDER}"/>'
                 f'<text x="{x + 10}" y="{y + 15}" font-size="10" fill="{DIM}">$ {escape(label)}</text>'
                 f'<text x="{x + 10}" y="{y + 40}" font-size="22" font-weight="700" fill="{GREEN if hot else FG}">{escape(big)}'
                 f'<tspan font-size="10" font-weight="400" fill="{DIM}"> {escape(unit)}</tspan></text>'
                 f'<text x="{x + 10}" y="{y + 54}" font-size="9" fill="{DIM}">{escape(sub)}</text></g>')
    # contributions / month bar chart
    cy = y0 + 3 * (th + gap)
    ch = H - cy - pad
    o.append(f'<rect x="{pad}" y="{cy}" width="{W - 2 * pad}" height="{ch}" rx="6" fill="{TILE}" stroke="{BORDER}"/>')
    o.append(f'<text x="{pad + 10}" y="{cy + 15}" font-size="10" fill="{DIM}">$ contributions / month</text>')
    months = s["months"]
    mx = max((v for _, v in months), default=0) or 1
    bx0, bw_all = pad + 14, W - 2 * pad - 28
    slot = bw_all / len(months)
    base = cy + ch - 18
    plot_h = ch - 50
    peak = max(range(len(months)), key=lambda i: months[i][1])
    for i, (ym, v) in enumerate(months):
        bh = max(2, plot_h * v / mx)
        x = bx0 + i * slot + slot * 0.18
        a = "" if STATIC else f' class="b" style="animation-delay:{0.8 + i * 0.05:.2f}s"'
        o.append(f'<rect x="{x:.1f}" y="{base - bh:.1f}" width="{slot * 0.64:.1f}" height="{bh:.1f}" rx="1.5" '
                 f'fill="{GREEN if i == peak else "#26a641"}"{a}><title>{v} in {ym}</title></rect>')
        o.append(f'<text x="{x + slot * 0.32:.1f}" y="{base + 12}" text-anchor="middle" font-size="9" fill="{DIM}">'
                 f'{date.fromisoformat(ym + "-01").strftime("%b")[0]}</text>')
        if i == peak:
            o.append(f'<text x="{x + slot * 0.32:.1f}" y="{base - bh - 4:.1f}" text-anchor="middle" font-size="9" fill="{FG}">{v:,}</text>')
    o.append("</g></svg>")
    return "\n".join(o)


def _selfcheck():
    d0 = date(2025, 1, 1)
    counts = [0, 1, 2, 0, 3, 3, 3, 0, 1, 1]  # longest 3, current 2 (ends on last day)
    data = {"total": sum(counts), "days": [{"date": str(d0 + timedelta(i)), "count": c, "level": min(c, 4)} for i, c in enumerate(counts)]}
    s = stats(data)
    assert (s["long"], s["cur"], s["active"], s["best"]) == (3, 2, 7, 3), s
    data["days"][-1]["count"] = 0  # empty today shouldn't break the streak
    assert stats(data)["cur"] == 1


if __name__ == "__main__":
    _selfcheck()
    args = sys.argv[1:]
    if args[:1] == ["--from-json"]:
        data = json.load(open(args[1]))
    else:
        data = fetch(args[0] if args else "KanveerMadan")
        os.makedirs("data", exist_ok=True)
        json.dump(data, open("data/contributions.json", "w"), indent=1)
    with open("contrib-heatmap.svg", "w") as f:
        f.write(heatmap(data))
    with open("stats-card.svg", "w") as f:
        f.write(stats_card(stats(data), "kanveer@github"))
    print(f"wrote contrib-heatmap.svg + stats-card.svg ({len(data['days'])} days, {data['total']} contributions)")
