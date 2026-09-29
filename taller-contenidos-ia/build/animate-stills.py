#!/usr/bin/env python3
"""
Hand-directed loops for the still illustrations: each piece gets its own small motions
(a robot's eyes look around and blink, a gauge needle trembles, a tag swings on its string,
a point of light glints on chrome), never a generic effect over the whole image.

    python3 animate-stills.py originals originals-anim [name ...]
    python3 prepare-media.py originals-anim && python3 build.py

Coordinates in RECIPES are in the 900 x 900 working space (the original, resized).
Every motion is periodic in the 4-second loop, so the loops are seamless.
"""
import sys, math, pathlib
import numpy as np
from PIL import Image, ImageFilter

PAPER = np.array((247, 244, 238), np.float32)
SIZE, N, MS = 900, 48, 84          # 48 frames x 84 ms = 4 s
TAU = 2 * math.pi
YY, XX = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)

# ---------------------------------------------------------------- helpers
_MEMO = {}
def memo(fn):
    def w(*a, **k):
        key = (fn.__name__,) + tuple(id(x) if isinstance(x, np.ndarray) else repr(x) for x in a) \
              + tuple(sorted((kk, repr(v)) for kk, v in k.items()))
        if key not in _MEMO:
            _MEMO[key] = (fn(*a, **k), a)
        return _MEMO[key][0]
    return w
def to_paper(a):
    lo = a.min(2); ch = a.max(2) - lo
    w = np.clip((lo - 222) / 14, 0, 1) * np.clip((22 - ch) / 10, 0, 1)
    return a * (1 - w[..., None]) + PAPER * w[..., None]

@memo
def box_mask(shape, boxes):
    m = np.zeros(shape[:2], np.float32)
    for x0, y0, x1, y1 in boxes:
        m[int(y0):int(y1), int(x0):int(x1)] = 1
    return m

@memo
def border_median(a, box):
    x0, y0, x1, y1 = map(int, box)
    b = np.concatenate([a[y0, x0:x1], a[y1 - 1, x0:x1], a[y0:y1, x0], a[y0:y1, x1 - 1]])
    return np.median(b, 0)

@memo
def ink(a, boxes, bg=None, lo=22, soft=26):
    """Soft mask of what differs from the background inside the boxes."""
    bg = PAPER if bg is None else bg
    d = np.sqrt(((a - bg) ** 2).sum(2))
    return np.clip((d - lo) / soft, 0, 1) * box_mask(a.shape, boxes)

@memo
def grow(m, px):
    im = Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8))
    im = im.filter(ImageFilter.MaxFilter(2 * px + 1)).filter(ImageFilter.GaussianBlur(1))
    return np.asarray(im, np.float32) / 255

@memo
def line_mask(shape, p, q, w):
    yy, xx = YY, XX
    px, py = p; qx, qy = q
    vx, vy = qx - px, qy - py; L2 = vx * vx + vy * vy
    t = np.clip(((xx - px) * vx + (yy - py) * vy) / L2, 0, 1)
    d = np.hypot(xx - (px + t * vx), yy - (py + t * vy))
    return np.clip((w - d) / 2 + 0.5, 0, 1)

def paste(frame, src, alpha, angle=0.0, pivot=(0, 0), dx=0.0, dy=0.0, bg=None):
    """Erase alpha-region to bg, then draw src*alpha rotated about pivot and shifted."""
    bg = PAPER if bg is None else bg
    er = grow(alpha, 2)
    frame = frame * (1 - er[..., None]) + bg * er[..., None]
    rgba = np.dstack([np.clip(src, 0, 255), alpha * 255]).astype(np.uint8)
    im = Image.fromarray(rgba, 'RGBA')
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    px, py = pivot
    # inverse map: output (x, y) -> input
    a_ = c; b_ = s; c_ = px - c * (px + dx) - s * (py + dy)
    d_ = -s; e_ = c; f_ = py + s * (px + dx) - c * (py + dy)
    im = im.transform(im.size, Image.AFFINE, (a_, b_, c_, d_, e_, f_), Image.BICUBIC)
    o = np.asarray(im, np.float32)
    al = o[..., 3:4] / 255
    return frame * (1 - al) + o[..., :3] * al

def wave(t, cycles=1, phase=0.0):
    return math.sin(TAU * (cycles * t + phase))

def bump(t, t0, dur):
    """0..1..0 bump centred on t0 (wraps around the loop)."""
    d = ((t - t0 + 0.5) % 1) - 0.5
    return math.exp(-(d / dur) ** 2)

# ---------------------------------------------------------------- effects
def fx_sway(f, base, t, boxes, pivot, amp, cycles=1, phase=0.0, bg=None, line=None, lo=22):
    bgc = bg if bg is not None else PAPER
    m = ink(base, boxes, bgc, lo)
    if line: m = m * line_mask(base.shape, *line)
    return paste(f, base, m, amp * wave(t, cycles, phase), pivot, bg=bgc)

def fx_needle(f, base, t, pivot, tip, amp, width=5, cycles=2, phase=0.0, step=None):
    x0, x1 = sorted((pivot[0], tip[0])); y0, y1 = sorted((pivot[1], tip[1]))
    pad = width + 8; box = (x0 - pad, y0 - pad, x1 + pad, y1 + pad)
    bg = border_median(base, box)
    m = ink(base, [box], bg, 30) * line_mask(base.shape, pivot, tip, width)
    if step:                                         # ticking hand: jumps of `step` degrees
        n = round(360 / step); ang = step * math.floor(t * n)
    else:                                            # trembling needle
        ang = amp * (0.7 * wave(t, cycles, phase) + 0.3 * wave(t, cycles * 3 + 1, phase * 2))
    return paste(f, base, m, ang, pivot, bg=bg)

def fx_bob(f, base, t, boxes, dy=4, dx=0, rot=0, pivot=None, cycles=1, phase=0.0, press=False):
    m = ink(base, boxes)
    if press:                                        # quick press down, slow return
        k = bump(t, 0.35, 0.07)
        return paste(f, base, m, 0, (0, 0), 0, dy * k)
    s = wave(t, cycles, phase); c = wave(t, cycles, phase + 0.25)
    pv = pivot or ((boxes[0][0] + boxes[0][2]) / 2, (boxes[0][1] + boxes[0][3]) / 2)
    return paste(f, base, m, rot * c, pv, dx * c, dy * s)

@memo
def find_blob(a, p, r=34, thr=85):
    """Dark blob nearest to p (a pupil), with holes (highlights) filled row by row."""
    x, y = map(int, p)
    win = a[y - r:y + r, x - r:x + r]
    lum = win.mean(2)
    dark = lum < thr
    ys, xs = np.nonzero(dark)
    if not len(ys): return None
    k = np.argmin((ys - r) ** 2 + (xs - r) ** 2)
    seen = np.zeros_like(dark); stack = [(ys[k], xs[k])]
    while stack:
        i, j = stack.pop()
        if 0 <= i < 2 * r and 0 <= j < 2 * r and dark[i, j] and not seen[i, j]:
            seen[i, j] = True
            stack += [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
    for i in range(2 * r):                           # fill highlight holes
        js = np.nonzero(seen[i])[0]
        if len(js): seen[i, js.min():js.max() + 1] = True
    m = np.zeros(a.shape[:2], np.float32)
    m[y - r:y + r, x - r:x + r] = seen
    return m

def fx_eyes(f, base, t, eyes, look=6, blinks=(0.47,), vertical=False, r=34, thr=85):
    for p in eyes:
        m = find_blob(base, p, r, thr)
        if m is None: continue
        ring = grow(m, 7) - grow(m, 3)
        face = np.median(base[ring > 0.5], 0)
        # look: left, hold, right, hold, back to centre
        g = (0.5 * wave(t, 1, 0.0) + 0.5 * wave(t, 2, 0.1) * 0.35)
        dx, dy = (0, look * g) if vertical else (look * g, 0)
        f = paste(f, base, m, 0, (0, 0), dx, dy, bg=face)
        k = 1.0 if any(abs(((t - b + 0.5) % 1) - 0.5) < 0.021 for b in blinks) else 0.0
        if k:                                 # lid: face colour over the eye, lash line
            ys, xs = np.nonzero(m > 0.5)
            cy = ys.mean(); x0, x1 = xs.min() - 3 + dx, xs.max() + 3 + dx
            lid = grow(m, 3)
            sh = np.roll(lid, int(round(dx)), 1)
            f = f * (1 - sh[..., None] * k) + face * (sh[..., None] * k)
            lm = line_mask(base.shape, (x0, cy + 2), (x1, cy + 2), 2.2) * k
            f = f * (1 - lm[..., None]) + np.array((40, 36, 34), np.float32) * lm[..., None]
    return f

def fx_sparkle(f, base, t, p, t0, size=26, dur=0.05):
    k = bump(t, t0, dur)
    if k < 0.02: return f
    x, y = p; r = int(size * 1.6)
    yy, xx = np.mgrid[-r:r, -r:r].astype(np.float32)
    s = size * (0.55 + 0.45 * k)
    ax, ay = np.abs(xx) / s, np.abs(yy) / s
    star = np.exp(-(ax * 7 + ay * 1.3) ** 1.2) + np.exp(-(ay * 7 + ax * 1.3) ** 1.2)
    dx_, dy_ = (xx + yy) / 1.414, (xx - yy) / 1.414
    star += 0.45 * (np.exp(-(np.abs(dx_) / s * 9 + np.abs(dy_) / s * 2.4)) +
                    np.exp(-(np.abs(dy_) / s * 9 + np.abs(dx_) / s * 2.4)))
    star += 0.9 * np.exp(-(xx ** 2 + yy ** 2) / (0.12 * s) ** 2)
    a = np.clip(star * k, 0, 1)[..., None]
    col = np.array((255, 253, 240), np.float32)
    f[y - r:y + r, x - r:x + r] = f[y - r:y + r, x - r:x + r] * (1 - a) + col * a
    return f

def fx_lamps(f, base, t, centres, r=17, cycles=1):
    yy, xx = YY, XX
    n = len(centres)
    for i, (x, y) in enumerate(centres):
        on = bump(t * cycles % 1, i / n, 0.07)
        d = np.hypot(xx - x, yy - y)
        disc = np.clip(r - d, 0, 1) * on * 0.45
        halo = np.exp(-((d - r) / 9) ** 2) * (d > r) * on * 0.25
        f = f + (255 - f) * disc[..., None]
        f = f + (np.array((255, 236, 170)) - f) * halo[..., None]
    return f

def fx_fade(f, base, t, boxes, lo=0.25, cycles=1, phase=0.0, flicker=False):
    m = ink(base, boxes)
    if flicker:
        v = 0.5 + 0.25 * wave(t, 7, phase) + 0.25 * wave(t, 11, phase * 3)
    else:
        v = 0.5 + 0.5 * wave(t, cycles, phase)
    v = lo + (1 - lo) * v
    return f * (1 - m[..., None]) + (PAPER + (f - PAPER) * v) * m[..., None]

def fx_ripple(f, base, t, boxes, src, wl=90, cycles=2):
    m = ink(base, boxes)
    yy, xx = YY, XX
    d = np.hypot(xx - src[0], yy - src[1])
    ph = (cycles * t - d / wl) % 1
    v = 0.3 + 0.7 * np.exp(-((ph - 0.5) / 0.22) ** 2)
    return f * (1 - m[..., None]) + (PAPER + (f - PAPER) * v[..., None]) * m[..., None]

def fx_flicker(f, base, t, boxes, amp=0.18):
    m = ink(base, boxes)
    v = 1 + amp * (0.6 * wave(t, 9) + 0.4 * wave(t, 14, 0.3))
    return f * (1 - m[..., None]) + np.clip(f * v, 0, 255) * m[..., None]

def fx_radar(f, base, t, c, r, strength=0.55):
    yy, xx = YY, XX
    ang = np.arctan2(yy - c[1], xx - c[0])
    d = (TAU * t - ang) % TAU
    disc = np.clip(r - np.hypot(xx - c[0], yy - c[1]), 0, 1)
    k = (np.exp(-d / 0.9) * disc * strength)[..., None]
    return f + (np.array((190, 255, 120), np.float32) - f) * k

def fx_green(f, base, t, boxes, amp=0.16, cycles=1, phase=0.0):
    r, g, b = base[..., 0], base[..., 1], base[..., 2]
    m = (np.clip((g - r - 12) / 30, 0, 1) * np.clip((g - b - 40) / 40, 0, 1) * box_mask(base.shape, boxes))
    v = 1 + amp * (0.5 + 0.5 * wave(t, cycles, phase))
    return f * (1 - m[..., None]) + np.clip(f * v, 0, 255) * m[..., None]

def fx_gear(f, base, t, c, r, amp=9, cycles=2):
    yy, xx = YY, XX
    disc = np.clip(r - np.hypot(xx - c[0], yy - c[1]), 0, 1)
    R, G, B = base[..., 0], base[..., 1], base[..., 2]
    yel = np.clip((R - 170) / 30, 0, 1) * np.clip((G - 120) / 30, 0, 1) * np.clip((110 - B) / 40, 0, 1)
    m = yel * disc
    bg = np.median(base[(disc > 0.5) & (yel < 0.1)], 0)
    return paste(f, base, m, amp * wave(t, cycles), c, bg=bg)

def fx_buzz(f, base, t, boxes, pivot, amp=1.4, windows=((0.18, 0.08), (0.66, 0.08)), freq=40):
    """Short bursts of vibration, like a power tool switched on."""
    env = max(math.exp(-(((t - c + 0.5) % 1 - 0.5) / w) ** 4) for c, w in windows)
    if env < 0.02: return f
    m = ink(base, boxes)
    ang = amp * env * math.sin(TAU * freq * t)
    return paste(f, base, m, ang, pivot, 0.8 * env * math.sin(TAU * freq * t + 1), 0)

FX = dict(buzz=fx_buzz, sway=fx_sway, needle=fx_needle, bob=fx_bob, eyes=fx_eyes, sparkle=fx_sparkle,
          lamps=fx_lamps, fade=fx_fade, ripple=fx_ripple, flicker=fx_flicker, radar=fx_radar,
          green=fx_green, gear=fx_gear)

# ---------------------------------------------------------------- recipes
S = 'sparkle'
RECIPES = {
 'portada': [
   ('eyes', dict(eyes=[(415, 160), (490, 158)], look=5, blinks=(0.46,))),
   ('sway', dict(boxes=[(703, 200, 760, 258), (699, 255, 832, 412)], pivot=(708, 200), amp=4)),
   ('needle', dict(pivot=(512, 352), tip=(535, 328), amp=9)),
   (S, dict(p=(446, 102), t0=0.15)), (S, dict(p=(338, 792), t0=0.72, size=22)),
 ],
 'tres-modelos': [
   ('eyes', dict(eyes=[(715, 160), (740, 158)], look=3, blinks=(0.3,))),
   ('needle', dict(pivot=(645, 404), tip=(656, 345), amp=6, width=4)),
   ('needle', dict(pivot=(362, 461), tip=(368, 430), amp=6, width=3, phase=0.3)),
   (S, dict(p=(752, 106), t0=0.6)), (S, dict(p=(585, 423), t0=0.1, size=18)),
 ],
 'voz': [
   ('ripple', dict(boxes=[(585, 180, 762, 402)], src=(580, 245))),
   ('ripple', dict(boxes=[(603, 383, 688, 488)], src=(692, 462), wl=60)),
   (S, dict(p=(742, 424), t0=0.35)),
 ],
 'gafas': [
   ('sway', dict(boxes=[(783, 222, 822, 408)], pivot=(792, 410), amp=4, cycles=2)),
   ('sway', dict(boxes=[(690, 310, 784, 418)], pivot=(746, 420), amp=5, phase=0.3)),
   ('green', dict(boxes=[(440, 470, 660, 695)], amp=0.25, cycles=2)),
   (S, dict(p=(135, 492), t0=0.2)), (S, dict(p=(470, 505), t0=0.65, size=20)),
 ],
 'anuncio': [
   ('eyes', dict(eyes=[(175, 165), (245, 160)], look=5, blinks=(0.55,))),
   ('needle', dict(pivot=(245, 322), tip=(256, 300), amp=10, width=3)),
   (S, dict(p=(506, 330), t0=0.25)), (S, dict(p=(781, 262), t0=0.8, size=20)),
 ],
 'pregunta': [
   ('buzz', dict(boxes=[(492, 122, 762, 304)], pivot=(718, 232))),
   ('green', dict(boxes=[(455, 60, 830, 365)], amp=0.2, cycles=1)),
   (S, dict(p=(796, 470), t0=0.4)),
 ],
 'panel': [
   ('needle', dict(pivot=(345, 247), tip=(320, 225), amp=10, width=4)),
   ('needle', dict(pivot=(458, 252), tip=(486, 214), amp=7, width=4, phase=0.4)),
   ('needle', dict(pivot=(575, 258), tip=(555, 234), amp=9, width=4, phase=0.7)),
   ('lamps', dict(centres=[(338, 338), (403, 343), (480, 347), (555, 352)], cycles=2)),
   (S, dict(p=(690, 202), t0=0.5)),
 ],
 'cadena': [
   ('gear', dict(c=(250, 520), r=74, amp=8)),
   ('bob', dict(boxes=[(640, 172, 872, 468)], dy=14, press=True)),
   (S, dict(p=(486, 330), t0=0.75)),
 ],
 'manual': [
   ('eyes', dict(eyes=[(426, 215), (492, 226)], look=4, blinks=(), r=20, thr=60)),
   ('green', dict(boxes=[(420, 250, 720, 500)], amp=0.14, cycles=1)),
   (S, dict(p=(392, 148), t0=0.2)),
 ],
 'whatsapp': [
   ('bob', dict(boxes=[(582, 102, 838, 392), (548, 205, 584, 272)], dy=0, rot=2.4, pivot=(572, 240))),
   ('fade', dict(boxes=[(270, 236, 318, 282)], lo=0.0, cycles=2)),
   (S, dict(p=(632, 170), t0=0.55)),
 ],
 'foto': [
   ('fade', dict(boxes=[(282, 72, 478, 250)], lo=0.35, cycles=2)),
   ('eyes', dict(eyes=[(745, 318), (803, 305)], look=4, blinks=(0.4,), r=52)),
   ('fade', dict(boxes=[(596, 352, 600 + 40, 420), (700, 352, 745, 420)], lo=0.2, cycles=2, phase=0.25)),
   (S, dict(p=(445, 455), t0=0.7)),
 ],
 'ficha': [
   ('sway', dict(boxes=[(335, 655, 675, 752)], pivot=(505, 704), amp=1.2, line=((343, 742), (668, 662), 11))),
   (S, dict(p=(398, 250), t0=0.3, size=30)), (S, dict(p=(820, 722), t0=0.75)),
   (S, dict(p=(228, 64), t0=0.05, size=16)),
 ],
 'taller': [
   ('radar', dict(c=(455, 370), r=84)),
   ('sway', dict(boxes=[(528, 72, 838, 238)], pivot=(566, 212), amp=2.2, cycles=2)),
   (S, dict(p=(548, 440), t0=0.35, size=20)), (S, dict(p=(795, 160), t0=0.8, size=18)),
 ],
 'lupa': [
   ('green', dict(boxes=[(380, 200, 470, 470)], amp=0.35, cycles=1)),
   ('green', dict(boxes=[(720, 210, 805, 510)], amp=0.35, cycles=1, phase=0.5)),
   (S, dict(p=(205, 218), t0=0.25, size=30)), (S, dict(p=(322, 160), t0=0.7, size=18)),
 ],
 'romper': [
   ('sway', dict(boxes=[(598, 104, 792, 300)], pivot=(680, 282), amp=3, cycles=6)),
   ('fade', dict(boxes=[(548, 122, 592, 228)], lo=0.1, cycles=3)),
   ('fade', dict(boxes=[(772, 122, 818, 238)], lo=0.1, cycles=3, phase=0.5)),
   ('fade', dict(boxes=[(492, 52, 578, 108)], lo=0.0, flicker=True)),
   ('eyes', dict(eyes=[(400, 188), (465, 212)], look=4, blinks=(), r=18, thr=60)),
 ],
 'medir': [
   ('needle', dict(pivot=(337, 437), tip=(455, 345), amp=0, width=5, step=45)),
   ('needle', dict(pivot=(630, 318), tip=(645, 188), amp=4, width=5)),
   (S, dict(p=(195, 392), t0=0.3)), (S, dict(p=(622, 150), t0=0.8, size=20)),
 ],
 'piloto': [
   ('flicker', dict(boxes=[(505, 618, 578, 702)], amp=0.22)),
   ('fade', dict(boxes=[(540, 158, 552, 172)], lo=0.4, cycles=2)),
   (S, dict(p=(506, 300), t0=0.2)),
 ],
 'parada': [
   ('bob', dict(boxes=[(238, 28, 868, 308)], dy=6)),
   (S, dict(p=(312, 345), t0=0.3, size=30)), (S, dict(p=(552, 512), t0=0.78, size=20)),
 ],
}

# ---------------------------------------------------------------- run
def animate(src, dst, recipe):
    im = Image.open(src).convert('RGB')
    if im.width != im.height:
        m = min(im.size); l, u = (im.width - m) // 2, (im.height - m) // 2
        im = im.crop((l, u, l + m, u + m))
    base = to_paper(np.asarray(im.resize((SIZE, SIZE), Image.LANCZOS), np.float32))
    frames = []
    for i in range(N):
        t = i / N; f = base.copy()
        for name, kw in recipe:
            f = FX[name](f, base, t, **kw)
        frames.append(Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)))
    frames[0].save(dst, save_all=True, append_images=frames[1:], duration=MS, loop=0,
                   quality=82, method=4)
    print(f'{dst.name:22s} {len(recipe)} motions')

if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    dst.mkdir(exist_ok=True)
    only = set(sys.argv[3:])
    for f in sorted(src.glob('*.webp')):
        key = f.stem.split('-', 1)[1]
        if (only and key not in only) or key not in RECIPES:
            continue
        _MEMO.clear()
        animate(f, dst / f.name, RECIPES[key])
