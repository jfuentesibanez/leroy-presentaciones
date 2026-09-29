# -*- coding: utf-8 -*-
import html, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from slides import S
try:
    from slides import META
except ImportError:
    META = {}

import base64
HERE      = pathlib.Path(__file__).resolve().parent      # deck/build
PROJECT   = HERE.parent                                  # deck
LOGODIR   = HERE / 'logos'
POSTERDIR = HERE / 'poster'
OUTFILE   = None   # set below from META['file']

def datauri_any(path, mime):
    return 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode()

# Logos are optional: drop logos/left.png (cover, left), logos/right.png (cover right and footer)
# and logos/right-dark.png (footer on dark slides). Missing files simply leave the slot out.
def _logo(name):
    f = LOGODIR / name
    return ('url("' + datauri_any(f, 'image/png') + '")') if f.exists() else 'none'
LOGO_CDP, LOGO_HS, LOGO_HSD = _logo('left.png'), _logo('right.png'), _logo('right-dark.png')
if LOGO_HSD == 'none': LOGO_HSD = LOGO_HS

# Each illustration ships twice: the still frame is embedded in the HTML so the
# deck renders instantly, the ~150-frame loop stays in img/ and is fetched when
# its slide comes up. See CLAUDE.md.
ART, ANIM = {}, {}
for _f in sorted(POSTERDIR.glob('*.webp')):
    _key = _f.stem.split('-', 1)[1]
    ART[_key]  = datauri_any(_f, 'image/webp')
    ANIM[_key] = 'img/' + _f.name
TITLE = META.get("title", "Untitled talk")
FOOT  = META.get("foot", TITLE)
DATE  = META.get("date", "")
AUTHOR = META.get("author", "Javier Fuentes Ibáñez")
OUTNAME = META.get("file", "deck.html")
TOTAL = len(S)
ACTS = []                                   # (act name, index of its first slide), talk order
for _i, _s in enumerate(S):
    _a = _s.get('act')
    if _a and _a != 'Close' and all(_a != x for x, _ in ACTS):
        ACTS.append((_a, _i))
ROMAN = ['I','II','III','IV','V','VI','VII','VIII','IX','X']

def rail(act):
    """The breadcrumb: every act in small caps across the top, the current one lit."""
    spans = ''.join(f'<span class="{"cur" if a == act else ""}" data-go="{i}">{a}</span>'
                    for a, i in ACTS)
    return f'<nav class="rail" aria-label="Secciones">{spans}</nav>'
_lg = ([] if LOGO_CDP == 'none' else ['<div class="lg lg-cdp" role="img" aria-label="Logo"></div>']) + \
      ([] if LOGO_HS  == 'none' else ['<div class="lg lg-hs" role="img" aria-label="Logo"></div>'])
LOGO = ('<div class="logorow' + (' solo' if len(_lg) == 1 else '') + '">'
        + '<span class="lg-rule"></span>'.join(_lg) + '</div>')
FOOTLOGO = '<span class="foot-logo" aria-hidden="true"></span>' if (LOGODIR / 'right.png').exists() else ''


# Photos for polaroid stacks: build/photos/<slug>.webp, credits in photos/credits.json
import json as _json
PHOTODIR = HERE / 'photos'
PHOTO, PHOTOCRED = {}, {}
if (PHOTODIR / 'credits.json').exists():
    for _c in _json.loads((PHOTODIR / 'credits.json').read_text()):
        PHOTO[_c['slug']] = datauri_any(PHOTODIR / (_c['slug'] + '.webp'), 'image/webp')
        PHOTOCRED[_c['slug']] = _c
# scattered resting places for up to seven prints: left %, top %, rotation
PILE = [(2,-1,-7), (56,-2,6), (-4,26,5), (29,22,-3), (62,25,-6), (8,53,-4), (51,54,7)]

def polaroids(slugs):
    cards = ''
    for j, sl in enumerate(slugs):
        x, y, r = PILE[j]
        cards += (f'<figure class="pol" style="left:{x}%;top:{y}%;--r:{r}deg;--d:{0.35+j*0.45:.2f}s">'
                  f'<img src="{PHOTO[sl]}" alt="{html.escape(PHOTOCRED[sl]["caption"])}">'
                  f'<figcaption>{PHOTOCRED[sl]["caption"]}</figcaption></figure>')
    return f'<div class="art pile">{cards}</div>'

def photo_credits(slugs):
    return 'fotos: Wikimedia Commons · ' + ' · '.join(
        f'{PHOTOCRED[s]["author"]}, {PHOTOCRED[s]["license"]}' for s in slugs)

def art_block(name, pin=None):
    uri = ART[name]
    extra = ''
    if pin:                                   # one polaroid pinned over the corner, arrives late
        extra = (f'<figure class="pol pin" style="--r:-8deg;--d:1.1s">'
                 f'<img src="{PHOTO[pin]}" alt="{html.escape(PHOTOCRED[pin]["caption"])}">'
                 f'<figcaption>{PHOTOCRED[pin]["caption"]}</figcaption></figure>')
    return (f'<div class="art{" has-pin" if pin else ""}"><img class="art-img" src="{uri}" '
            f'data-anim="{ANIM[name]}" alt="">{extra}</div>')

MAPDIR = HERE / 'maps'
def map_svg(code):
    """A country outline from maps/<code>.geo.json (Natural Earth 10m), as a brass line.
    Equirectangular with the latitude corrected by cos(mid-lat), tiny islets dropped."""
    import json, math
    g = json.loads((MAPDIR / f'{code}.geo.json').read_text())['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    def area(r): return abs(sum(x0*y1 - x1*y0 for (x0,y0),(x1,y1) in zip(r, r[1:]+r[:1]))) / 2
    rings = sorted((p[0] for p in polys), key=area, reverse=True)
    big = rings[0]; rings = [r for r in rings if area(r) > area(big) * 0.003]
    lat0 = sum(p[1] for p in big) / len(big); k = math.cos(math.radians(lat0))
    pts = [(x*k, -y) for r in rings for x, y in r]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    W, H, pad = 600, 720, 18
    sc = min((W-2*pad)/(max(xs)-min(xs)), (H-2*pad)/(max(ys)-min(ys)))
    ox = (W - (max(xs)-min(xs))*sc)/2 - min(xs)*sc; oy = (H - (max(ys)-min(ys))*sc)/2 - min(ys)*sc
    d = ''
    for r in rings:
        d += 'M' + 'L'.join(f'{x*k*sc+ox:.1f},{-y*sc+oy:.1f}' for x, y in r) + 'Z'
    return (f'<svg class="map" viewBox="0 0 {W} {H}" role="img" aria-label="{code} outline">'
            f'<path d="{d}"/></svg>')

def chart_svg(s):
    """Line chart, one highlighted series in rust, the rest as grey context with
    direct labels at the line end. Static SVG, house fonts, no script."""
    W, H = 1060, 440
    L, R, T, B = 96, 210, 28, 52          # plot margins: room for y labels and end labels
    ys, ser, hl = s['years'], s['series'], s['highlight']
    top = max(max(v) for v in ser.values()); rnd, step = s.get('round', 50000), s.get('grid', 100000)
    ymax = int((top // rnd) + 1) * rnd
    px = lambda i: L + i * (W - L - R) / (len(ys) - 1)
    py = lambda v: T + (H - T - B) * (1 - v / ymax)
    o = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(s["title"])}">']
    for g in range(0, ymax + 1, step):           # recessive grid + y labels
        y = py(g)
        o.append(f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" class="grid"/>')
        o.append(f'<text x="{L-14}" y="{y+5:.1f}" class="ax" text-anchor="end">{g:,}</text>')
    for i, yr in enumerate(ys):                     # x labels every third year, plus the last
        if (yr - ys[0]) % 3 == 0 or yr == ys[-1]:
            o.append(f'<text x="{px(i):.1f}" y="{H-18}" class="ax" text-anchor="middle">{yr}</text>')
    o.append(f'<line x1="{L}" y1="{py(0):.1f}" x2="{W-R}" y2="{py(0):.1f}" class="axis"/>')
    # context series first so the highlight sits on top; labels stacked without collisions
    ends = sorted(((v[-1], k) for k, v in ser.items() if k != hl), reverse=True)
    slots, last = [], -1e9
    for v, k in ends:
        y = max(py(v), last + 24); slots.append((k, py(v), y)); last = y
    for k, v in ser.items():
        if k == hl: continue
        pts = ' '.join(f'{px(i):.1f},{py(y):.1f}' for i, y in enumerate(v))
        o.append(f'<polyline points="{pts}" class="ctx"/>')
    for k, y0, y in slots:
        x0 = px(len(ys)-1)
        o.append(f'<line x1="{x0+6}" y1="{y0:.1f}" x2="{x0+22}" y2="{y:.1f}" class="lead"/>')
        o.append(f'<text x="{x0+28}" y="{y+5:.1f}" class="lbl">{k}</text>')
    v = ser[hl]; pts = ' '.join(f'{px(i):.1f},{py(y):.1f}' for i, y in enumerate(v))
    o.append(f'<polyline points="{pts}" class="hl"/>')
    o.append(f'<circle cx="{px(len(ys)-1):.1f}" cy="{py(v[-1]):.1f}" r="7" class="dot"/>')
    o.append(f'<text x="{px(len(ys)-1)+28:.1f}" y="{py(v[-1])+7:.1f}" class="hll">{hl}</text>')
    if s.get('note'):
        o.append(f'<text x="{px(len(ys)-1)-10:.1f}" y="{py(v[-1])-22:.1f}" class="note" text-anchor="end">{s["note"]}</text>')
    o.append('</svg>')
    return ''.join(o)

def timechart_svg(s):
    """Dated points on a linear scale: grey dots for every model, the frontier as a line,
    labels on the named points. For growth that is close to exponential, linear shows it."""
    W, H = 1060, 440
    L, R, T, B = 80, 150, 24, 52
    pts = s['points']                                  # (fractional year, value, label or '')
    x0, x1 = s.get('xmin', int(pts[0][0])), s.get('xmax', int(pts[-1][0]) + 1)
    ymax, step = s['ymax'], s['grid']
    px = lambda x: L + (x - x0) / (x1 - x0) * (W - L - R)
    py = lambda v: T + (H - T - B) * (1 - v / ymax)
    o = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(s["title"])}">']
    g = 0
    while g <= ymax:
        o.append(f'<line x1="{L}" y1="{py(g):.1f}" x2="{W-R}" y2="{py(g):.1f}" class="grid"/>')
        o.append(f'<text x="{L-14}" y="{py(g)+5:.1f}" class="ax" text-anchor="end">{g:g} {s.get("unit","")}</text>')
        g += step
    for yr in range(int(x0), int(x1) + 1):
        o.append(f'<text x="{px(yr):.1f}" y="{H-18}" class="ax" text-anchor="middle">{yr}</text>')
    o.append(f'<line x1="{L}" y1="{py(0):.1f}" x2="{W-R}" y2="{py(0):.1f}" class="axis"/>')
    front, best = [], -1
    for x, v, _ in pts:
        if v > best: front.append((x, v)); best = v
    o.append('<polyline points="' + ' '.join(f'{px(x):.1f},{py(v):.1f}' for x, v in front) + '" class="hl"/>')
    for x, v, lb in pts:
        on = (x, v) in front
        o.append(f'<circle cx="{px(x):.1f}" cy="{py(v):.1f}" r="{6 if on else 4.5}" class="{"dot" if on else "gdot"}"/>')
        if lb:
            o.append(f'<text x="{px(x)-12:.1f}" y="{py(v)+6:.1f}" class="lbl" text-anchor="end">{lb}</text>')
    if s.get('note'):
        o.append(f'<text x="{L+16}" y="{T+22}" class="hll">{s["note"]}</text>')
    o.append('</svg>')
    return ''.join(o)

def src_line(s):
    out = f'<p class="src">{s["src"]}</p>' if s.get('src') else ''
    if s.get('links'):                        # external links, small, under the source line
        out += '<p class="xlinks">' + ''.join(
            f'<a href="{u}" target="_blank" rel="noopener">{html.escape(tx)} &#8599;</a>'
            for tx, u in s['links']) + '</p>'
    return out

def render(s, i):
    if s.get('art') and s['art'] not in ART:   # illustration not generated yet: slide renders without it
        s = {x: v for x, v in s.items() if x != 'art'}
    n, k = i + 1, s['kind']
    cls = ['slide', f'k-{k}'] + (['dark'] if s.get('dark') else [])
    body = ''
    if k == 'cover':
        if s.get('art'): cls.append('has-art')
        logos = LOGO if (LOGO_CDP != 'none' or LOGO_HS != 'none') else ''
        body = (f'<div class="col">{logos}'
                f'<h1 class="cover-title">{s["title"]}</h1>'
                f'<p class="cover-meta">{s["who"]}<br><span>{s["date"]}</span></p></div>'
                + (art_block(s['art']) if s.get('art') else ''))
    elif k == 'quote':
        body = f'<blockquote>{s["text"]}</blockquote><p class="attrib">{s["src"]}</p>'
        if s.get('art'):                     # quote beside an illustration
            cls.append('has-art')
            body = f'<div class="col">{body}</div>' + art_block(s['art'])
        elif s.get('portrait'):              # a cut-out portrait standing on the footer rule
            cls.append('has-portrait')
            uri = datauri_any(PHOTODIR / (s['portrait'] + '.webp'), 'image/webp')
            body = (f'<div class="col">{body}'
                    + (f'<p class="src cred">{s["credit"]}</p>' if s.get('credit') else '')
                    + f'</div><img class="portrait" src="{uri}" alt="">')
    elif k == 'anchor':
        kick = f'<p class="kicker">{s["kicker"]}</p>' if s.get('kicker') else ''
        wide = ' wide' if s.get('wide') else ''
        body = f'{kick}<p class="anchor{wide}">{s["text"]}</p>'
    elif k == 'data':
        body = (f'<p class="figure">{s["figure"]}</p><p class="figcap">{s["cap"]}</p>'
                + src_line(s))
        if s.get('map'):                     # a country outline on the right, brass line
            cls.append('has-art')
            body = f'<div class="col">{body}</div><div class="art">{map_svg(s["map"])}</div>'
    elif k == 'agenda':
        TIMES = META.get('times', {})
        lis = ''.join(f'<li><span class="num">{TIMES.get(a) or ROMAN[j]}</span><span class="nm" data-go="{i}">{META.get('long', {}).get(a, a)}</span></li>'
                      for j, (a, i) in enumerate(ACTS))
        if TIMES: cls.append('timed')
        body = f'<h2>{s["title"]}</h2><ol class="agenda">{lis}</ol>'
    elif k == 'breath':                      # illustration only: a pause between two heavy slides
        cls.append('has-art')
        body = art_block(s['art'])
    elif k == 'compare':
        def col(side):
            notes = ''.join(f'<li>{x}</li>' for x in s.get('notes_'+side, []))
            return (f'<div class="cmp-col"><p class="cmp-fig">{s["fig_"+side]}</p>'
                    f'<p class="cmp-lbl">{s["lbl_"+side]}</p><ul class="cmp-notes">{notes}</ul></div>')
        body = (f'<div class="cmp">{col("a")}<span class="cmp-rule"></span>{col("b")}</div>'
                f'<p class="cmp-cap">{s["cap"]}</p>' + src_line(s))
    elif k == 'chart':
        body = f'<h2>{s["title"]}</h2>{chart_svg(s)}' + src_line(s)
    elif k == 'table':                       # a small table: header row + rows, optional status column colouring
        head = ''.join(f'<th>{h}</th>' for h in s['head'])
        def cell(c):
            cl = {'verificado': 'ok', 'sin verificar': 'no', 'deducido': 'warn'}.get(str(c).lower(), '')
            return f'<td class="{cl}">{c}</td>'
        rows = ''.join('<tr>' + ''.join(cell(c) for c in r) + '</tr>' for r in s['rows'])
        cap = f'<p class="tcap">{s["cap"]}</p>' if s.get('cap') else ''
        body = f'<h2>{s["title"]}</h2><table class="tbl"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>{cap}' + src_line(s)
    elif k == 'prompt':                      # text to paste into a tool, with a copy button
        txt = html.escape(s['text'].strip())
        where = f'<p class="pwhere">{s["where"]}</p>' if s.get('where') else ''
        body = (f'<h2>{s["title"]}</h2>{where}<div class="pbox"><button class="pcopy" type="button">copiar</button>'
                f'<pre>{txt}</pre></div>' + src_line(s))
    elif k == 'figure':                      # a chart or screenshot from build/figures/, full width, with its source
        uri = datauri_any(HERE / 'figures' / s['img'], 'image/webp')
        body = (f'<h2>{s["title"]}</h2><img class="fig" src="{uri}" alt="{html.escape(s["title"])}">'
                + (f'<p class="tcap">{s["cap"]}</p>' if s.get('cap') else '') + src_line(s))
    elif k == 'timechart':
        body = f'<h2>{s["title"]}</h2>{timechart_svg(s)}' + src_line(s)
    elif k == 'video':
        cls.append('k-video')
        vid  = s.get('vid', '')
        link = s.get('link') or ('https://www.youtube.com/watch?v=' + vid)
        ltxt = 'abrir en youtube &#8599;' if vid else 'abrir la página de origen &#8599;'
        body = (f'<div class="vwrap" data-vid="{vid}" data-link="{link}" data-slug="{s["slug"]}"'
                f' data-start="{s.get("start", "")}" data-end="{s.get("end", "")}">'
                f'<h2>{s["title"]}</h2>'
                f'<div class="vstage">'
                f'<video class="vplayer" playsinline preload="metadata">'
                f'<source src="video/{s["slug"]}.mp4" type="video/mp4">'
                f'<source src="video/{s["slug"]}.webm" type="video/webm">'
                f'</video>'
                f'<button class="play" aria-label="Reproducir vídeo"><span></span></button>'
                f'</div>'
                f'<p class="vlabel">{s["label"]}</p>'
                f'<p class="vhint"></p>'
                f'<a class="vlink" href="{link}" target="_blank" rel="noopener">{ltxt}</a></div>')
    elif k == 'bullets':
        lis = ''.join(f'<li>{b}</li>' for b in s['items'])
        pol = s.get('polaroids')
        has = bool(s.get('art') or pol)
        if has: cls.append('has-art')
        src = src_line(s)
        if pol:
            src += f'<p class="src cred">{photo_credits(pol)}</p>'
        if s.get('pin'):
            src += f'<p class="src cred">{PHOTOCRED[s["pin"]]["credit"]}</p>'
        body = (f'<div class="col"><h2>{s["title"]}</h2><ul>{lis}</ul>{src}</div>'
                + (polaroids(pol) if pol else art_block(s['art'], s.get('pin')) if has else ''))
    elif k == 'close':
        body = (f'<h1 class="cover-title">{s["title"]}</h1>'
                f'<p class="mail"><a href="mailto:{s["mail"]}">{s["mail"]}</a></p>'
                f'<p class="cover-meta">{s["who"]} · {s["org"]}</p>')
    act = s.get('act', '')
    foot = ('' if k in ('cover',) else
            f'<footer><span class="fl-wrap">{FOOTLOGO}{act or FOOT} · {DATE}</span>'
            f'<span>{n} / {TOTAL}</span></footer>')
    nav = rail(act) if k not in ('cover', 'agenda', 'close') else ''
    return (f'<section class="{" ".join(cls)}" id="s{n}">'
            f'{nav}<div class="inner">{body}</div>{foot}</section>')

sections = '\n'.join(render(s, i) for i, s in enumerate(S))

CSS = r"""
:root{
  --paper:#F7F4EE; --ink:#1B1B1B; --brass:#4A8512; --leroy:#78BE20; --rust:#4A8512;
  --grey:#8A8378; --line:#DED6C7;
  --logo-cdp:LOGOCDP;
  --logo-hs:LOGOHS;
  --logo-hs-dark:LOGOHSD;
  --sans:"Optima","Gill Sans","Gill Sans MT","Segoe UI","Helvetica Neue",Helvetica,Arial,sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{background:var(--paper);font-family:var(--sans);color:var(--ink);transition:background .25s;
  /* the page colour follows the current slide, so on wide screens the paper (or ink) runs edge to edge */
  display:flex;align-items:center;justify-content:center;overflow:hidden}
#stage{position:relative;width:1280px;height:720px;transform-origin:center center;flex:none}
body.dark{background:var(--ink)}
body.dark #help{color:#9A9287}
.slide{position:absolute;inset:0;background:var(--paper);padding:64px 84px 76px;
  display:none;align-items:center}
.slide.on{display:flex}
.inner{width:100%;display:flex;flex-direction:column;justify-content:center}
.has-art .inner{flex-direction:row;align-items:center;gap:36px}
.inner .col{flex:1 1 55%;min-width:0}
.art{flex:0 1 41%;display:flex;align-items:center;justify-content:center;
  max-height:520px;align-self:center}
.art img,.art svg{width:100%;height:auto;max-height:500px;display:block}
.art-img{display:block;border-radius:2px}
.art-svg{width:100%}

h1.cover-title{font-size:68px;max-width:12ch;line-height:1.04;font-weight:600;letter-spacing:-.02em}
h2{font-size:42px;font-weight:600;line-height:1.1;margin-bottom:34px;letter-spacing:-.01em}
h2::after{content:"";display:block;width:64px;height:3px;background:var(--leroy);
  margin-top:18px;border-radius:2px}
.kicker{font-size:15px;letter-spacing:.22em;text-transform:uppercase;color:var(--brass);
  margin-bottom:22px;font-weight:600}
.cover-meta{font-size:22px;color:var(--grey);margin-top:38px;line-height:1.5}
.cover-meta span{font-size:18px}

ul{list-style:none}
li{font-size:27px;line-height:1.38;margin-bottom:19px;padding-left:30px;position:relative;
  max-width:29ch}
.slide:not(.has-art) li{max-width:none;font-size:29px;margin-bottom:24px}
li::before{content:"";position:absolute;left:1px;top:.56em;width:9px;height:9px;
  border:2px solid var(--leroy);border-radius:50%;background:transparent}
.slide:not(.has-art) li::before{width:10px;height:10px;top:.55em}
li b{font-weight:700}
li i{font-style:italic}

.anchor{font-size:58px;line-height:1.18;font-weight:600;letter-spacing:-.015em;max-width:22ch}
.anchor.wide{max-width:none;font-size:50px;line-height:1.24;white-space:nowrap}  /* one sentence per line, no wrapping */
blockquote{font-size:44px;line-height:1.28;font-weight:400;font-style:italic;max-width:24ch}
.attrib{margin-top:34px;font-size:20px;color:var(--grey)}
.figure{font-size:104px;font-weight:700;letter-spacing:-.03em;line-height:1;color:var(--brass)}
.figcap{font-size:30px;line-height:1.35;margin-top:30px;max-width:26ch}
.src{margin-top:30px;font-size:15px;color:var(--grey);letter-spacing:.01em}
.dark{background:var(--ink);color:var(--paper)}
.dark .figure{color:#8FD13F}
.dark .src,.dark footer,.dark .attrib,.dark .cover-meta{color:#9A9287}
.dark li::before{border-color:#8FD13F}
.dark h2::after{background:#8FD13F}

.k-breath .inner{justify-content:center}
.k-breath .art{flex:0 1 52%;max-height:560px}
.k-breath .art img{max-height:540px}
.map{width:100%;height:auto;max-height:520px;display:block}
.map path{fill:#EFE9DB;stroke:var(--brass);stroke-width:2.5;stroke-linejoin:round;
  vector-effect:non-scaling-stroke}
.dark .map path{fill:#25221E;stroke:#8FD13F}
.k-data.has-art .art{flex:0 1 36%}
/* compare slides: two figures that are NOT the same thing, kept visibly apart */
.cmp{display:flex;align-items:flex-start;gap:0 56px;width:100%}
.cmp-col{flex:1 1 0;min-width:0}
.cmp-rule{flex:0 0 1px;align-self:stretch;background:var(--line);margin-top:10px}
.dark .cmp-rule{background:#3A362F}
.cmp-fig{font-size:84px;font-weight:700;letter-spacing:-.03em;line-height:1;color:var(--brass)}
.dark .cmp-fig{color:#8FD13F}
.cmp-lbl{font-size:26px;font-weight:600;line-height:1.25;margin-top:18px}
.cmp-notes{margin-top:12px}
.cmp-notes li{font-size:19px;line-height:1.4;margin-bottom:6px;padding-left:0;color:#5E5850;max-width:none}
.cmp-notes li::before{display:none}
.dark .cmp-notes li{color:#B5AD9F}
.cmp-cap{font-size:24px;line-height:1.35;margin-top:34px;max-width:60ch}
.k-compare .src{margin-top:18px}
/* polaroid stack: prints drop in one after another and settle into a loose pile */
.pile{position:relative;height:540px;align-self:center;flex:0 1 46%!important;max-height:none!important}
.pol{position:absolute;width:37%;margin:0;background:#FDFCF8;padding:6% 6% 19%;
  box-shadow:0 1px 2px rgba(0,0,0,.12),0 8px 22px rgba(40,30,15,.18);
  transform:rotate(var(--r));animation:drop .7s cubic-bezier(.2,.8,.3,1.05) var(--d) both}
.pol img{display:block;width:100%;aspect-ratio:1;object-fit:cover;filter:saturate(.9) contrast(1.02)}
.pol figcaption{position:absolute;left:6%;right:6%;bottom:4%;text-align:center;
  font-family:"Bradley Hand","Noteworthy","Segoe Print","Comic Sans MS",cursive;
  font-size:16px;color:#3A3630;line-height:1.1;white-space:nowrap}
@keyframes drop{
  0%{opacity:0;transform:translate(60px,-140px) rotate(calc(var(--r) + 22deg)) scale(1.3)}
  65%{opacity:1;transform:translate(0,5px) rotate(calc(var(--r) - 1.5deg)) scale(.98)}
  100%{opacity:1;transform:translate(0,0) rotate(var(--r)) scale(1)}}
.pile .pol{opacity:0;animation:none;visibility:hidden}
.pile .pol.shown{visibility:visible;opacity:1;animation:drop .6s cubic-bezier(.2,.8,.3,1.05) both}
@media (prefers-reduced-motion:reduce){.pol,.pile .pol.shown{animation:none}}
.src.cred{margin-top:6px;font-size:12px}
.art.has-pin{position:relative}
.pol.pin{width:36%;left:-8%;bottom:2%;top:auto;padding:5% 5% 16%}
.pol.pin figcaption{font-size:15px}
/* quote with a cut-out portrait on the right, standing on the footer rule */
.has-portrait .col{max-width:60%}
.has-portrait blockquote{max-width:20ch}
.k-quote.has-art blockquote{max-width:20ch;font-size:40px}
.portrait{position:absolute;right:70px;bottom:58px;height:560px;width:auto;pointer-events:none;
  -webkit-mask-image:linear-gradient(to bottom,#000 78%,transparent 100%);
  mask-image:linear-gradient(to bottom,#000 78%,transparent 100%);
  filter:sepia(.18) contrast(1.04);animation:rise 1.1s ease-out both}
@keyframes rise{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.portrait{animation:none}}
/* chart slides: house-style SVG line chart, rust highlight on grey context */
.k-chart h2,.k-timechart h2{margin-bottom:10px}
.k-chart .src,.k-timechart .src{margin-top:12px}
.chart{width:100%;height:auto;display:block;font-family:var(--sans)}
.chart .grid{stroke:var(--line);stroke-width:1;stroke-dasharray:3 5}
.chart .axis{stroke:#C9C1B2;stroke-width:1.5}
.chart .ax{font-size:15px;fill:var(--grey);letter-spacing:.02em}
.chart .ctx{fill:none;stroke:#A9A297;stroke-width:2.5;stroke-linejoin:round;stroke-linecap:round}
.chart .lead{stroke:#C9C1B2;stroke-width:1}
.chart .lbl{font-size:16px;fill:#5E5850}
.chart .hl{fill:none;stroke:var(--rust);stroke-width:4;stroke-linejoin:round;stroke-linecap:round}
.chart .dot{fill:var(--rust);stroke:var(--paper);stroke-width:2.5}
.tbl{border-collapse:collapse;width:100%;max-width:1060px;font-size:21px;margin-top:6px}
.tbl th{text-align:left;font-size:13px;letter-spacing:.16em;text-transform:uppercase;color:var(--grey);
  font-weight:600;padding:0 18px 10px 0;border-bottom:2px solid var(--line)}
.tbl td{padding:11px 18px 11px 0;border-bottom:1px solid var(--line);line-height:1.3}
.tbl td.ok{color:var(--brass);font-weight:600}
.tbl td.no{color:#B0412A;font-weight:600}
.tbl td.warn{color:#A67A00;font-weight:600}
.fig{display:block;width:100%;max-width:1100px;max-height:470px;width:auto;max-width:100%;border:1px solid var(--line);border-radius:2px}
.tcap{font-size:19px;color:#5E5850;margin-top:16px;max-width:1000px;line-height:1.4}
.pwhere{font-size:18px;color:#5E5850;margin:-6px 0 12px}
.pbox{position:relative;background:#FDFCF8;border:1px solid var(--line);border-left:4px solid var(--leroy);
  border-radius:3px;padding:16px 22px;max-width:1080px}
.pbox pre{margin:0;white-space:pre-wrap;font-family:"SF Mono",Menlo,Consolas,monospace;font-size:16.5px;
  line-height:1.5;color:var(--ink)}
.pcopy{position:absolute;top:10px;right:10px;font:600 12px var(--sans);letter-spacing:.12em;text-transform:uppercase;
  color:var(--brass);background:transparent;border:1px solid var(--line);border-radius:2px;padding:5px 10px;cursor:pointer}
.pcopy:hover{border-color:var(--leroy)}
.chart .gdot{fill:#B5AD9F;stroke:var(--paper);stroke-width:2}
.chart .hll{font-size:19px;font-weight:600;fill:var(--rust)}
.chart .note{font-size:16px;fill:var(--ink)}
.k-video .inner{align-items:flex-start}
.vwrap{width:100%}
.vstage{position:relative;margin-top:6px;width:100%;max-width:980px;aspect-ratio:16/9;
  background:#14120F;border-radius:3px;overflow:hidden;display:flex;
  align-items:center;justify-content:center;cursor:pointer}
.vstage.noclip{background:transparent;border:2px solid var(--line);max-width:760px}
.vplayer{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;background:#14120F}
.vstage.noclip .vplayer{display:none}
.vstage:fullscreen,.vstage:-webkit-full-screen{max-width:none;aspect-ratio:auto;border-radius:0;background:#000;border:0}
.vstage.playing{cursor:default}
.vstage.playing:hover .play{transform:none}
.play{position:relative;z-index:2;width:112px;height:112px;border-radius:50%;
  border:3px solid rgba(247,244,238,.92);background:rgba(20,18,15,.35);cursor:pointer;
  display:flex;align-items:center;justify-content:center;transition:background .18s,transform .18s;
  backdrop-filter:blur(2px)}
.play span{width:0;height:0;border-left:30px solid #F7F4EE;border-top:19px solid transparent;
  border-bottom:19px solid transparent;margin-left:9px}
.vstage:hover .play{background:var(--leroy);transform:scale(1.05)}
.vstage.noclip .play{border-color:var(--ink);background:transparent}
.vstage.noclip .play span{border-left-color:var(--ink)}
.vstage.noclip:hover .play span{border-left-color:#F7F4EE}
.vlabel{margin-top:22px;font-size:21px;color:var(--ink);max-width:52ch;line-height:1.4}
.vhint{margin-top:8px;font-size:14px;color:var(--grey);letter-spacing:.03em}
.vhint a{color:var(--grey)}
.vlink{display:inline-block;margin-top:10px;font-size:14px;color:var(--grey);
  letter-spacing:.04em;text-decoration:none;border-bottom:1px solid var(--line)}
.vlink:hover{color:var(--brass);border-color:var(--brass)}
.xlinks{margin-top:14px;display:flex;flex-wrap:wrap;gap:6px 22px}
.xlinks a{font-size:14px;color:var(--brass);text-decoration:none;border-bottom:1px solid var(--line)}
.xlinks a:hover{border-color:var(--leroy)}
.dark .xlinks a{color:#8FD13F;border-color:#3A362F}
.k-video h2{margin-bottom:22px;font-size:38px}
.k-video h2::after{margin-top:14px}
.mail{margin-top:26px;font-size:34px}
.mail a{color:var(--brass);text-decoration:none;border-bottom:2px solid var(--line)}

.rail{position:absolute;left:84px;right:84px;top:26px;display:flex;gap:0 22px;flex-wrap:wrap;
  font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#B5AD9F;line-height:1}
.rail span{cursor:pointer;padding-bottom:6px;border-bottom:2px solid transparent;white-space:nowrap}
.rail span.cur{color:var(--brass);border-color:var(--brass);font-weight:600}
.rail span:hover{color:var(--ink)}
.dark .rail{color:#5E5850}
.dark .rail span.cur{color:#8FD13F;border-color:#8FD13F}
.dark .rail span:hover{color:var(--paper)}
ol.agenda{list-style:none;columns:2;column-gap:60px;max-width:960px}
ol.agenda li{font-size:30px;line-height:1.25;margin-bottom:22px;padding-left:0;display:flex;
  align-items:baseline;gap:18px;break-inside:avoid;max-width:none}
ol.agenda li::before{display:none}
ol.agenda .num{font-size:15px;letter-spacing:.14em;color:var(--brass);font-weight:600;min-width:34px}
ol.agenda .nm{cursor:pointer;border-bottom:1px solid transparent}
ol.agenda .nm:hover{border-color:var(--brass)}
.timed ol.agenda{columns:1;max-width:1000px}
.timed ol.agenda li{font-size:27px;margin-bottom:15px;align-items:baseline}
.timed ol.agenda .num{min-width:88px;font-variant-numeric:tabular-nums}
footer{position:absolute;left:84px;right:84px;bottom:30px;display:flex;
  justify-content:space-between;font-size:13px;color:var(--grey);
  border-top:1px solid var(--line);padding-top:14px;letter-spacing:.04em}
.dark footer{border-color:#3A362F}


.logorow{display:flex;align-items:center;gap:24px;margin-bottom:38px}
.lg{background-position:left center;background-size:contain;background-repeat:no-repeat}
.lg-cdp{width:79px;height:44px;background-image:var(--logo-cdp)}
.lg-hs{width:110px;height:66px;background-image:var(--logo-hs)}
.lg-rule{width:1px;height:38px;background:var(--line)}
.solo .lg-hs{width:150px;height:90px}
.foot-logo{display:inline-block;width:34px;height:20px;margin-right:13px;
  background:var(--logo-hs) left center/contain no-repeat;opacity:.9}
.dark .foot-logo{background-image:var(--logo-hs-dark);opacity:.95}
footer .fl-wrap{display:flex;align-items:center}
#bar{position:fixed;left:0;bottom:0;height:3px;background:var(--leroy);
  width:0;transition:width .22s ease;z-index:9}
#help{position:fixed;right:14px;top:12px;font-size:11px;color:#5E5850;
  letter-spacing:.08em;z-index:9;opacity:.75}
@media print{
  body{display:block;background:#fff;overflow:visible}
  #stage{width:auto;height:auto;transform:none!important}
  .slide{position:relative;display:flex!important;width:1280px;height:720px;
    page-break-after:always;break-after:page}
  #bar,#help{display:none}
  .pol{animation:none}
  .rail{display:none}
  .pile .pol{visibility:visible;opacity:1}
}
"""

JS = r"""
const slides=[...document.querySelectorAll('.slide')];let i=0;
const bar=document.getElementById('bar'),stage=document.getElementById('stage');
function fit(){const s=Math.min(innerWidth/1280,innerHeight/720);stage.style.transform='scale('+s+')';}
function fitSlide(s){
  const inner=s.querySelector('.inner'); if(!inner) return;
  inner.style.zoom=1;
  const avail=s.clientHeight-parseFloat(getComputedStyle(s).paddingTop)
             -parseFloat(getComputedStyle(s).paddingBottom);
  let k=1;
  while(inner.scrollHeight*k>avail && k>0.62){k-=0.02;}
  if(k<1) inner.style.zoom=k.toFixed(2);
}
// ---- illustrations: still frame is embedded, the animated loop lives in img/ ----
// Each loop is fetched once, then swapped in. show() fetches the current and next
// slide at once; prefetchAll() then walks the whole deck one file at a time so every
// loop is cached long before its slide comes up, even on hotel wifi.
function animate(n,done){
  const s=slides[n]; if(!s){done&&done();return;}
  const img=s.querySelector('.art-img[data-anim]'); if(!img){done&&done();return;}
  const url=img.dataset.anim; delete img.dataset.anim;
  const pre=new Image();
  pre.onload=()=>{img.src=url; done&&done();};
  pre.onerror=()=>{done&&done();};   // no img/ next to the deck: the still stays
  pre.src=url;
}
let prefetching=false;
function prefetchAll(){
  if(prefetching) return; prefetching=true;
  const order=[]; for(let k=0;k<slides.length;k++) order.push((i+k)%slides.length);
  const next=()=>{ const n=order.shift(); if(n===undefined) return; animate(n,next); };
  next();
}
// ---- step reveals: a polaroid pile shows one print per click before the deck moves on ----
function pileOf(k){ return slides[k] && slides[k].querySelector('.pile'); }
function revealNext(){ const p=pileOf(i); if(!p) return false;
  const nx=p.querySelector('.pol:not(.shown)'); if(!nx) return false;
  nx.classList.add('shown'); return true; }
function hideLast(){ const p=pileOf(i); if(!p) return false;
  const sh=p.querySelectorAll('.pol.shown'); if(!sh.length) return false;
  sh[sh.length-1].classList.remove('shown'); return true; }
function next(){ if(!revealNext()) show(i+1); }
function prev(){ if(!hideLast()) show(i-1, true); }
function show(n, back){
  i=Math.max(0,Math.min(slides.length-1,n));
  slides.forEach((s,k)=>s.classList.toggle('on',k===i));
  const pl=pileOf(i);                 // arriving forwards: empty pile; backwards: the full pile
  if(pl) pl.querySelectorAll('.pol').forEach(p=>p.classList.toggle('shown', !!back));
  document.body.classList.toggle('dark', slides[i].classList.contains('dark'));
  fitSlide(slides[i]);
  animate(i); animate(i+1);
  bar.style.width=((i+1)/slides.length*100)+'%';
  location.hash='#s'+(i+1);
  document.querySelectorAll('.ytframe').forEach(f=>{
    if(!f.closest('.slide').classList.contains('on')) f.remove();});
  document.querySelectorAll('.vplayer').forEach(v=>{
    if(!v.closest('.slide').classList.contains('on')){try{v.pause()}catch(e){}}});
  document.querySelectorAll('.vwrap .play').forEach(p=>{
    if(!p.closest('.vstage').querySelector('.ytframe')) p.style.display='flex';});
}
// ---- video ----
const FILE = location.protocol === 'file:';
function fsStage(){ const el=document.fullscreenElement||document.webkitFullscreenElement;
  return el && el.classList && el.classList.contains('vstage') ? el : null; }
function stopVideo(stage){
  const v=stage.querySelector('.vplayer'); if(v){try{v.pause()}catch(e){} v.controls=false;}
  stage.querySelectorAll('.ytframe').forEach(f=>f.remove());
  stage.classList.remove('playing');
  const p=stage.querySelector('.play'); if(p) p.style.display='flex';
  const w=stage.closest('.vwrap'); if(w) w.querySelector('.vhint').textContent =
    (v && v.readyState>0) ? 'pulsa v · vídeo local, pantalla completa'
    : FILE ? 'pulsa v · se abre en youtube, pantalla completa' : 'pulsa v · se reproduce aquí, pantalla completa';
}
function goFull(el){
  const r=el.requestFullscreen||el.webkitRequestFullscreen;
  if(r){ try{ const p=r.call(el); if(p&&p.catch) p.catch(()=>{}); }catch(e){} }
}
document.addEventListener('fullscreenchange',()=>{
  if(!fsStage()) document.querySelectorAll('.vstage.playing').forEach(stopVideo);
});
document.querySelectorAll('.vwrap').forEach(w=>{
  const v=w.querySelector('.vplayer'), stage=w.querySelector('.vstage'),
        hint=w.querySelector('.vhint');
  v.addEventListener('error',()=>{
    stage.classList.add('noclip');
    hint.textContent = FILE
      || !w.dataset.vid ? 'pulsa v · abre la página de origen'
      : 'pulsa v · se reproduce aquí, pantalla completa';
  },true);
  v.addEventListener('loadedmetadata',()=>{
    stage.classList.remove('noclip'); hint.textContent='pulsa v · vídeo local, pantalla completa';
  });
  v.addEventListener('ended',()=>{ if(fsStage()===stage){ (document.exitFullscreen||document.webkitExitFullscreen).call(document); } else stopVideo(stage); });
});
function playVideo(w){
  const v=w.querySelector('.vplayer'), stage=w.querySelector('.vstage');
  if(stage.classList.contains('playing')){          // already running: toggle pause
    if(v && v.readyState>0 && !stage.querySelector('.ytframe')){ v.paused?v.play():v.pause(); }
    return;
  }
  // 1. local clip in video/  -> plays inside the deck, full screen, offline
  if(!stage.classList.contains('noclip') && v.readyState>0){
    stage.classList.add('playing'); w.querySelector('.play').style.display='none';
    v.controls=true; v.currentTime=0;
    goFull(stage); const p=v.play(); if(p&&p.catch) p.catch(()=>{});
    w.querySelector('.vhint').textContent='espacio pausa · ← → avanzar · esc salir';
    return;
  }
  // 2. no local clip, served over http(s) -> embedded YouTube player, full screen
  const url=w.dataset.link;
  if(!FILE && w.dataset.vid){
    const f=document.createElement('iframe');
    let ok=false;
    f.className='ytframe';f.allow='autoplay; encrypted-media; fullscreen; picture-in-picture';
    f.allowFullscreen=true;f.style.cssText='position:absolute;inset:0;width:100%;height:100%;border:0';
    f.addEventListener('load',()=>{ok=true});
    f.src='https://www.youtube-nocookie.com/embed/'+w.dataset.vid+'?autoplay=1&rel=0&modestbranding=1&playsinline=1'
      +(w.dataset.start?'&start='+w.dataset.start:'')+(w.dataset.end?'&end='+w.dataset.end:'');
    stage.classList.remove('noclip'); stage.classList.add('playing'); stage.appendChild(f);
    w.querySelector('.play').style.display='none';
    w.querySelector('.vhint').textContent='reproductor de youtube · esc salir';
    goFull(stage);
    setTimeout(()=>{ if(!ok){ stopVideo(stage); stage.classList.add('noclip');
      w.querySelector('.vhint').textContent='vídeo bloqueado aquí · abriendo youtube';
      window.open(url,'_blank','noopener'); } },3500);
    return;
  }
  // 3. opened as a file:// with no local clip -> browsers block the embed, open YouTube
  window.open(url,'_blank','noopener');
}
addEventListener('keydown',e=>{
  const ps=slides[i].querySelector('.vstage.playing');
  if(ps){                                            // a video is on: keys drive it
    const v=ps.querySelector('.vplayer'), yt=ps.querySelector('.ytframe');
    if(e.key===' '||e.key==='k'||e.key==='v'){ e.preventDefault(); if(v&&!yt){v.paused?v.play():v.pause();} }
    if(e.key==='ArrowRight'&&v&&!yt){ e.preventDefault(); v.currentTime=Math.min(v.duration||1e9,v.currentTime+10); }
    if(e.key==='ArrowLeft'&&v&&!yt){ e.preventDefault(); v.currentTime=Math.max(0,v.currentTime-10); }
    if(e.key==='Escape'){                            // leaving fullscreen stops it too (fullscreenchange)
      if(fsStage()) (document.exitFullscreen||document.webkitExitFullscreen).call(document);
      else stopVideo(ps); }
    return;
  }
  if(['ArrowRight','PageDown',' ','Enter','n'].includes(e.key)){e.preventDefault();next()}
  if(['ArrowLeft','PageUp','p'].includes(e.key)){e.preventDefault();prev()}
  if(e.key==='Home')show(0); if(e.key==='End')show(slides.length-1);
  if(e.key==='v'){const w=slides[i].querySelector('.vwrap'); if(w){e.preventDefault();playVideo(w)}}
  if(e.key==='f'){document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen()}
});
addEventListener('resize',fit);
document.addEventListener('click',e=>{
  const cp=e.target.closest('.pcopy');
  if(cp){ e.stopPropagation(); const tx=cp.nextElementSibling.textContent;
    (navigator.clipboard?navigator.clipboard.writeText(tx):Promise.reject()).then(
      ()=>{cp.textContent='copiado';setTimeout(()=>cp.textContent='copiar',1500)},
      ()=>{const r=document.createRange();r.selectNodeContents(cp.nextElementSibling);
           const sel=getSelection();sel.removeAllRanges();sel.addRange(r);document.execCommand('copy');
           cp.textContent='copiado';setTimeout(()=>cp.textContent='copiar',1500)}); return; }
  if(e.target.closest('.pbox'))return;
  const go=e.target.closest('[data-go]');
  if(go){ e.stopPropagation(); show(parseInt(go.dataset.go)); return; }
  const st=e.target.closest('.vstage');
  if(st){ if(!st.classList.contains('playing')) playVideo(st.closest('.vwrap')); return; }
  if(e.target.closest('a'))return;
  (e.clientX < innerWidth*0.28 ? prev : next)();
});
fit();
show(location.hash?parseInt(location.hash.slice(2))-1||0:0);
setTimeout(prefetchAll,1500);
"""

CSS = CSS.replace('LOGOCDP', LOGO_CDP).replace('LOGOHSD', LOGO_HSD).replace('LOGOHS', LOGO_HS)

doc = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(TITLE)} — {html.escape(AUTHOR)}</title>
<style>{CSS}</style>
</head>
<body>
<div id="stage">
{sections}
</div>
<div id="bar"></div>
<div id="help">← → avanzar · f pantalla completa</div>
<script>{JS}</script>
</body>
</html>
"""
OUTFILE = PROJECT / OUTNAME
OUTFILE.write_text(doc, encoding='utf-8')
# index.html so the GitHub Pages URL works without the file name; keeps the #sN hash.
(PROJECT / 'index.html').write_text(
    '<!doctype html><meta charset="utf-8"><title>' + html.escape(TITLE) + '</title>\n'
    '<meta http-equiv="refresh" content="0; url=' + OUTNAME + '">\n'
    '<script>location.replace("' + OUTNAME + '"+location.hash)</script>\n'
    '<a href="' + OUTNAME + '">' + html.escape(TITLE) + '</a>\n', encoding='utf-8')
print(f'wrote {OUTFILE}  {len(doc)/1024:.0f} KB  {TOTAL} slides')
