#!/usr/bin/env python3
"""Generate inline SVG charts for the blog from JSON specs.

Usage:  python3 tools/mkchart.py tools/charts/*.json
Each spec writes _includes/figures/<name>.svg. Charts use CSS classes defined in
assets/css/main.css (.chart .s1 … .s6) so colours live in one place. Every mark
carries a data-tip attribute; assets/js/site.js turns those into hover tooltips.

Spec (JSON):
{
  "name": "fgsm-eps",                # output file name
  "type": "line" | "column" | "bar" | "scatter",
  "title": "...", "subtitle": "...", "source": "Goodfellow et al. 2015, Table 1",
  "x": {"title": "ε", "values": [0, 0.05, ...]}            # line/scatter: numeric; column/bar: category labels
  "y": {"title": "Error rate (%)", "min": 0, "max": 100, "ticks": [0,25,50,75,100], "fmt": "{:.0f}%"}
  "series": [{"name": "MNIST", "values": [...], "label_end": true}, ...]
  "annotations": [{"x": 0.3, "y": 90, "text": "…", "dx": 6, "dy": -6}]
  "ref_lines": [{"y": 50, "label": "chance"}]
  "width": 860, "height": 420
}
For "bar" (horizontal) the x axis carries the categories and values run left→right.
"""
import json, sys, os, math

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_includes", "figures")
CHAR_W = 6.9  # approx px per char at 12.5px Hanken Grotesk


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def fmt_val(v, fmt):
    if v is None:
        return "–"
    if fmt:
        return fmt.format(v)
    if isinstance(v, float) and not v.is_integer():
        return f"{v:g}"
    return f"{int(v):,}" if abs(v) >= 1000 else f"{v:g}"


def nice_ticks(lo, hi, n=5):
    if hi == lo:
        hi = lo + 1
    raw = (hi - lo) / n
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if raw <= step:
            break
    start = math.floor(lo / step) * step
    ticks = []
    t = start
    while t <= hi + 1e-9:
        ticks.append(round(t, 10))
        t += step
    return ticks


class Chart:
    def __init__(self, spec):
        self.s = spec
        self.W = spec.get("width", 860)
        self.H = spec.get("height", 420)
        self.parts = []
        self.ml = spec.get("margin_left", 56)
        self.mr = spec.get("margin_right", 24)
        if any(ser.get("label_end") for ser in spec.get("series", [])):
            self.mr = max(self.mr, 64)
        self.mt = 24
        self.mb = 52
        if spec.get("title"):
            self.mt += 22
        self.sub_lines = []
        if spec.get("subtitle"):
            import textwrap
            self.sub_lines = textwrap.wrap(spec["subtitle"], width=int(self.W / 6.6))
            self.mt += 18 * len(self.sub_lines)
        self.has_legend = len(spec.get("series", [])) > 1 and not spec.get("no_legend")
        if self.has_legend:
            # estimate legend rows for wrapping
            names = [ser.get("name", "") for ser in spec["series"]]
            x, rows = 0, 1
            for nm in names:
                w = 22 + len(nm) * CHAR_W + 22
                if x + w > self.W and x > 0:
                    rows += 1; x = 0
                x += w
            self.legend_rows = rows
            self.mt += 24 * rows
        if spec.get("y", {}).get("title"):
            self.mt += 14
        if spec.get("label_values") or any(ser.get("label_values") for ser in spec.get("series", [])):
            self.mt += 14
        if spec.get("source"):
            import textwrap
            self.mb += 16 + 15 * (len(textwrap.wrap("Source: " + spec["source"], width=int(self.W / 6.6))) - 1)
        if spec.get("x", {}).get("title"):
            self.mb += 4

    # ── helpers ─────────────────────────────────────────────────
    def add(self, s):
        self.parts.append(s)

    def header(self):
        s = self.s
        y = 18
        if s.get("title"):
            self.add(f'<text class="title" x="0" y="{y}">{esc(s["title"])}</text>')
            y += 20
        for ln in self.sub_lines:
            self.add(f'<text class="subtitle" x="0" y="{y}">{esc(ln)}</text>')
            y += 18
        if self.has_legend:
            x = 0
            y += 10
            for i, ser in enumerate(s["series"]):
                cls = ser.get("cls", f"s{i+1}")
                name = ser.get("name", f"Series {i+1}")
                w = 22 + len(name) * CHAR_W + 22
                if x + w > self.W and x > 0:
                    x = 0; y += 22
                if s["type"] in ("line", "scatter"):
                    self.add(f'<g class="legend {cls}"><line class="key" x1="{x}" y1="{y-4}" x2="{x+16}" y2="{y-4}"/>'
                             f'<circle class="dot" cx="{x+8}" cy="{y-4}" r="3.5"/><text x="{x+22}" y="{y}">{esc(name)}</text></g>')
                else:
                    self.add(f'<g class="legend {cls}"><rect class="swatch" x="{x}" y="{y-11}" width="12" height="12" rx="2"/>'
                             f'<text x="{x+18}" y="{y}">{esc(name)}</text></g>')
                x += 22 + len(name) * CHAR_W + 22

    def footer(self):
        if self.s.get("source"):
            import textwrap
            lines = textwrap.wrap("Source: " + self.s["source"], width=int(self.W / 6.6))
            y = self.H - 6 - 15 * (len(lines) - 1)
            for ln in lines:
                self.add(f'<text class="subtitle" x="0" y="{y}">{esc(ln)}</text>')
                y += 15

    def y_axis(self, y0, y1, ticks, fmt, title, grid=True, tick_fmt=None):
        tick_fmt = tick_fmt or fmt
        ph = self.H - self.mt - self.mb
        def Y(v):
            return self.mt + ph - (v - y0) / (y1 - y0) * ph
        self.add('<g class="grid">')
        for t in ticks:
            if grid:
                self.add(f'<line x1="{self.ml}" x2="{self.W-self.mr}" y1="{Y(t):.1f}" y2="{Y(t):.1f}"/>')
        self.add('</g><g class="axis">')
        for t in ticks:
            self.add(f'<text x="{self.ml-8}" y="{Y(t)+4:.1f}" text-anchor="end">{esc(fmt_val(t, tick_fmt))}</text>')
        self.add('</g>')
        if title:
            self.add(f'<text class="axis-title" x="{self.ml}" y="{self.mt-8}" text-anchor="start">{esc(title)}</text>')
        return Y

    # ── line / scatter ──────────────────────────────────────────
    def line(self):
        s = self.s
        series = s["series"]
        xs = s["x"].get("values") or sorted({x for ser in series for x in ser.get("x", [])})
        xlog = s["x"].get("log", False)
        allv = [v for ser in series for v in ser["values"] if v is not None]
        ya = s.get("y", {})
        y0 = ya.get("min", min(0, min(allv)))
        y1 = ya.get("max", max(allv))
        ticks = ya.get("ticks") or nice_ticks(y0, y1)
        y0, y1 = min(y0, ticks[0]), max(y1, ticks[-1])
        Y = self.y_axis(y0, y1, ticks, ya.get("fmt"), ya.get("title"), tick_fmt=ya.get("tick_fmt"))
        pw = self.W - self.ml - self.mr
        xa = s["x"]
        xv = [math.log10(x) for x in xs] if xlog else xs
        x0 = math.log10(xa["min"]) if (xlog and "min" in xa) else xa.get("min", min(xv))
        x1 = math.log10(xa["max"]) if (xlog and "max" in xa) else xa.get("max", max(xv))
        def X(v):
            vv = math.log10(v) if xlog else v
            return self.ml + (vv - x0) / (x1 - x0) * pw
        # x ticks
        xt = xa.get("ticks") or (xs if len(xs) <= 10 else nice_ticks(x0, x1, 6))
        xlabels = xa.get("labels")
        self.add('<g class="axis">')
        self.add(f'<line x1="{self.ml}" x2="{self.W-self.mr}" y1="{Y(y0):.1f}" y2="{Y(y0):.1f}"/>')
        for i, t in enumerate(xt):
            lab = xlabels[i] if xlabels else fmt_val(t, xa.get("fmt"))
            self.add(f'<text x="{X(t):.1f}" y="{Y(y0)+18:.1f}" text-anchor="middle">{esc(lab)}</text>')
        self.add('</g>')
        if xa.get("title"):
            self.add(f'<text class="axis-title" x="{self.W-self.mr}" y="{Y(y0)+36:.1f}" text-anchor="end">{esc(xa["title"])}</text>')
        for rl in s.get("ref_lines", []):
            if "y" in rl:
                self.add(f'<line class="ref" x1="{self.ml}" x2="{self.W-self.mr}" y1="{Y(rl["y"]):.1f}" y2="{Y(rl["y"]):.1f}"/>')
                self.add(f'<text class="annot" x="{self.W-self.mr-4}" y="{Y(rl["y"])-5:.1f}" text-anchor="end">{esc(rl.get("label",""))}</text>')
            if "x" in rl:
                self.add(f'<line class="ref" y1="{self.mt}" y2="{Y(y0):.1f}" x1="{X(rl["x"]):.1f}" x2="{X(rl["x"]):.1f}"/>')
                self.add(f'<text class="annot" x="{X(rl["x"])+5:.1f}" y="{self.mt+12}" text-anchor="start">{esc(rl.get("label",""))}</text>')
        end_labels = []
        for i, ser in enumerate(series):
            cls = ser.get("cls", f"s{i+1}")
            pts = [(X(x), Y(v), x, v) for x, v in zip(ser.get("x", xs), ser["values"]) if v is not None]
            self.add(f'<g class="{cls}">')
            if s["type"] == "line" and len(pts) > 1:
                d = " ".join(f'{"M" if k == 0 else "L"}{px:.1f},{py:.1f}' for k, (px, py, _, _) in enumerate(pts))
                dash = ' stroke-dasharray="5 4"' if ser.get("dashed") else ""
                self.add(f'<path class="line" d="{d}"{dash}/>')
            for px, py, x, v in pts:
                xl = fmt_val(x, xa.get("fmt"))
                if xlabels and x in xs:
                    xl = xlabels[xs.index(x)]
                tip = f'<b>{esc(ser.get("name",""))}</b><br>{esc(xa.get("tip_prefix",""))}{esc(xl)}: {esc(fmt_val(v, ya.get("fmt")))}'
                rr = 5.5 if s["type"] == "scatter" else 4
                self.add(f'<circle class="dot" cx="{px:.1f}" cy="{py:.1f}" r="{rr}" data-tip="{tip}"/>')
            self.add('</g>')
            if ser.get("label_end", False) and pts:
                px, py, _, v = pts[-1]
                end_labels.append((py, px, ser.get("name", ""), fmt_val(v, ya.get("fmt")), ser.get("end_text")))
        # place end labels, resolving collisions
        end_labels.sort()
        placed = []
        for py, px, name, val, custom in end_labels:
            yy = py
            for p in placed:
                if abs(p - yy) < 15:
                    yy = p + 15
            placed.append(yy)
            text = custom if custom else val
            self.add(f'<text class="label" x="{px+8:.1f}" y="{yy+4:.1f}">{esc(text)}</text>')
        for a in s.get("annotations", []):
            anchor = a.get("anchor", "start")
            self.add(f'<text class="annot" x="{X(a["x"])+a.get("dx",6):.1f}" y="{Y(a["y"])+a.get("dy",-6):.1f}" text-anchor="{anchor}">{esc(a["text"])}</text>')

    # ── column (vertical bars, categories on x) ──────────────────
    def column(self):
        s = self.s
        cats = s["x"]["values"]
        series = s["series"]
        allv = [v for ser in series for v in ser["values"] if v is not None]
        ya = s.get("y", {})
        y0 = ya.get("min", 0)
        y1 = ya.get("max", max(allv))
        ticks = ya.get("ticks") or nice_ticks(y0, y1)
        y1 = max(y1, ticks[-1])
        Y = self.y_axis(y0, y1, ticks, ya.get("fmt"), ya.get("title"), tick_fmt=ya.get("tick_fmt"))
        pw = self.W - self.ml - self.mr
        n = len(cats)
        band = pw / n
        k = len(series)
        gap = 2
        bw = min(24, (band * 0.62 - gap * (k - 1)) / k)
        group_w = bw * k + gap * (k - 1)
        self.add('<g class="axis">')
        self.add(f'<line x1="{self.ml}" x2="{self.W-self.mr}" y1="{Y(y0):.1f}" y2="{Y(y0):.1f}"/>')
        for i, c in enumerate(cats):
            cx = self.ml + band * (i + 0.5)
            lines = str(c).split("\n")
            for j, ln in enumerate(lines):
                self.add(f'<text x="{cx:.1f}" y="{Y(y0)+18+j*14:.1f}" text-anchor="middle">{esc(ln)}</text>')
        self.add('</g>')
        if s["x"].get("title"):
            self.add(f'<text class="axis-title" x="{self.W-self.mr}" y="{Y(y0)+40:.1f}" text-anchor="end">{esc(s["x"]["title"])}</text>')
        for rl in s.get("ref_lines", []):
            self.add(f'<line class="ref" x1="{self.ml}" x2="{self.W-self.mr}" y1="{Y(rl["y"]):.1f}" y2="{Y(rl["y"]):.1f}"/>')
            self.add(f'<text class="annot" x="{self.ml+4}" y="{Y(rl["y"])-5:.1f}" text-anchor="start">{esc(rl.get("label",""))}</text>')
        label_all = s.get("label_values", k == 1 and n <= 8)
        for j, ser in enumerate(series):
            cls = ser.get("cls", f"s{j+1}")
            self.add(f'<g class="{cls}">')
            for i, v in enumerate(ser["values"]):
                if v is None:
                    continue
                cx = self.ml + band * (i + 0.5) - group_w / 2 + j * (bw + gap)
                top, base = Y(v), Y(y0)
                h = max(0, base - top)
                r = min(4, h / 2)
                # rounded top only
                d = (f'M{cx:.1f},{base:.1f} V{top+r:.1f} Q{cx:.1f},{top:.1f} {cx+r:.1f},{top:.1f} '
                     f'H{cx+bw-r:.1f} Q{cx+bw:.1f},{top:.1f} {cx+bw:.1f},{top+r:.1f} V{base:.1f} Z')
                tip = f'<b>{esc(ser.get("name", cats[i]))}</b><br>{esc(str(cats[i]).replace(chr(10), " "))}: {esc(fmt_val(v, ya.get("fmt")))}'
                self.add(f'<path class="bar" d="{d}" data-tip="{tip}"/>')
                if label_all or (ser.get("label_values")):
                    self.add(f'<text class="label" x="{cx+bw/2:.1f}" y="{top-6:.1f}" text-anchor="middle">{esc(fmt_val(v, ya.get("fmt")))}</text>')
            self.add('</g>')
        for a in s.get("annotations", []):
            cx = self.ml + band * (a["x"] + 0.5)
            self.add(f'<text class="annot" x="{cx+a.get("dx",0):.1f}" y="{Y(a["y"])+a.get("dy",-6):.1f}" text-anchor="{a.get("anchor","middle")}">{esc(a["text"])}</text>')

    # ── bar (horizontal) ────────────────────────────────────────
    def bar(self):
        s = self.s
        cats = s["x"]["values"]
        series = s["series"]
        allv = [v for ser in series for v in ser["values"] if v is not None]
        ya = s.get("y", {})
        v0 = ya.get("min", 0)
        v1 = ya.get("max", max(allv))
        ticks = ya.get("ticks") or nice_ticks(v0, v1)
        v1 = max(v1, ticks[-1])
        label_w = max(len(str(c)) for c in cats) * CHAR_W + 16
        self.ml = max(self.ml, label_w)
        pw = self.W - self.ml - self.mr - 48
        ph = self.H - self.mt - self.mb
        n = len(cats)
        k = len(series)
        band = ph / n
        gap = 2
        bh = min(22, (band * 0.66 - gap * (k - 1)) / k)
        group_h = bh * k + gap * (k - 1)
        def X(v):
            return self.ml + (v - v0) / (v1 - v0) * pw
        self.add('<g class="grid">')
        for t in ticks:
            self.add(f'<line y1="{self.mt}" y2="{self.mt+ph}" x1="{X(t):.1f}" x2="{X(t):.1f}"/>')
        self.add('</g><g class="axis">')
        for t in ticks:
            self.add(f'<text x="{X(t):.1f}" y="{self.mt+ph+18}" text-anchor="middle">{esc(fmt_val(t, ya.get("tick_fmt", ya.get("fmt"))))}</text>')
        for i, c in enumerate(cats):
            cy = self.mt + band * (i + 0.5)
            self.add(f'<text x="{self.ml-10}" y="{cy+4:.1f}" text-anchor="end" style="fill:var(--ink-2)">{esc(c)}</text>')
        self.add('</g>')
        if ya.get("title"):
            self.add(f'<text class="axis-title" x="{self.ml+pw}" y="{self.mt+ph+36}" text-anchor="end">{esc(ya["title"])}</text>')
        for rl in s.get("ref_lines", []):
            self.add(f'<line class="ref" y1="{self.mt}" y2="{self.mt+ph}" x1="{X(rl["y"]):.1f}" x2="{X(rl["y"]):.1f}"/>')
            right = X(rl["y"]) > self.ml + pw * 0.6
            self.add(f'<text class="annot" x="{X(rl["y"]) + (-5 if right else 5):.1f}" y="{self.mt+ph-6}" text-anchor="{"end" if right else "start"}">{esc(rl.get("label",""))}</text>')
        label_all = s.get("label_values", True)
        for j, ser in enumerate(series):
            cls = ser.get("cls", f"s{j+1}")
            self.add(f'<g class="{cls}">')
            for i, v in enumerate(ser["values"]):
                if v is None:
                    continue
                cy = self.mt + band * (i + 0.5) - group_h / 2 + j * (bh + gap)
                x0, x1 = X(v0), X(v)
                w = max(0, x1 - x0)
                r = min(4, w / 2)
                d = (f'M{x0:.1f},{cy:.1f} H{x1-r:.1f} Q{x1:.1f},{cy:.1f} {x1:.1f},{cy+r:.1f} V{cy+bh-r:.1f} '
                     f'Q{x1:.1f},{cy+bh:.1f} {x1-r:.1f},{cy+bh:.1f} H{x0:.1f} Z')
                tip = f'<b>{esc(ser.get("name", cats[i]))}</b><br>{esc(cats[i])}: {esc(fmt_val(v, ya.get("fmt")))}'
                self.add(f'<path class="bar" d="{d}" data-tip="{tip}"/>')
                if label_all:
                    lab = fmt_val(v, ya.get("fmt"))
                    self.add(f'<text class="label" x="{x1+6:.1f}" y="{cy+bh/2+4:.1f}">{esc(lab)}</text>')
            self.add('</g>')

    def render(self):
        self.header()
        t = self.s["type"]
        if t in ("line", "scatter"):
            self.line()
        elif t == "column":
            self.column()
        elif t == "bar":
            self.bar()
        else:
            raise SystemExit(f"unknown type {t}")
        self.footer()
        body = "\n".join(self.parts)
        return (f'<svg class="chart" viewBox="0 0 {self.W} {self.H}" width="{self.W}" height="{self.H}" '
                f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{esc(self.s.get("title", self.s["name"]))}">\n'
                f'{body}\n</svg>\n')


def main(paths):
    os.makedirs(OUT_DIR, exist_ok=True)
    for p in paths:
        with open(p) as f:
            spec = json.load(f)
        svg = Chart(spec).render()
        out = os.path.join(OUT_DIR, spec["name"] + ".svg")
        with open(out, "w") as f:
            f.write(svg)
        print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1:])
