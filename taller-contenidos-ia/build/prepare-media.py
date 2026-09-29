#!/usr/bin/env python3
"""
Re-derive the deck's artwork from the original illustration files.

You only need this when the artwork changes — new pieces, a re-render, or a
different size/quality trade-off. Editing slide text does NOT need it; that is
build.py alone.

    python3 prepare-media.py ~/path/to/originals

For every NN-name.webp in that folder it writes two things:

  ../img/NN-name.webp      the animated loop, resized and recompressed
  poster/NN-name.webp      its first frame, which build.py embeds in the HTML

It also nudges each file's background to the deck's exact paper colour
(#F7F4EE). The originals come back in slightly different off-whites, and
without this you can see the edge of every image as a faint square.

Requires Pillow:  pip3 install Pillow
"""
import sys, os, glob, collections, pathlib
from PIL import Image
import numpy as np

PAPER    = (247, 244, 238)   # must match --paper in build.py's CSS
ANIM_PX  = 672               # 640 for the heaviest pieces, see below
ANIM_Q   = 60
HEAVY_Q  = 46                # pieces that would otherwise run past ~5 MB
POSTER_PX, POSTER_Q = 560, 72
FRAME_MS = 40                # fallback only: 25 fps when a file carries no frame timing

HERE   = pathlib.Path(__file__).resolve().parent
IMGDIR = HERE.parent / 'img'
POSTER = HERE / 'poster'

def frame_durations(path, n):
    """Per-frame durations in ms, read straight from the ANMF chunks.

    Pillow does not reliably expose them for these files, and the timing is not
    uniform: the automaton's chest pulse runs 80-560 ms a frame. Forcing 40 ms
    would play it 2.5x too fast. Falls back to FRAME_MS if the file has no
    animation chunks."""
    data = path.read_bytes(); pos = 12; out = []
    while pos + 8 <= len(data):
        tag = data[pos:pos+4]; size = int.from_bytes(data[pos+4:pos+8], 'little')
        if tag == b'ANMF':
            out.append(int.from_bytes(data[pos+8+12:pos+8+15], 'little') or FRAME_MS)
        pos += 8 + size + (size & 1)
    return out if len(out) == n else [FRAME_MS] * n

def paper_offset(frame0):
    """How far this file's background sits from the deck's paper colour."""
    a = np.array(frame0).astype(np.int16)
    edge = np.concatenate([a[:8].reshape(-1,3), a[-8:].reshape(-1,3),
                           a[:,:8].reshape(-1,3), a[:,-8:].reshape(-1,3)])
    bg = collections.Counter(map(tuple, edge)).most_common(1)[0][0]
    return np.array(PAPER) - np.array(bg)

def main(srcdir):
    IMGDIR.mkdir(exist_ok=True); POSTER.mkdir(exist_ok=True)
    # animated .webp loops, or still .png/.jpg straight from the image model
    files = sorted(f for ext in ('webp', 'png', 'jpg', 'jpeg')
                   for f in glob.glob(os.path.join(srcdir, '*.' + ext)))
    if not files:
        sys.exit(f'no .webp, .png or .jpg files in {srcdir}')
    total = 0
    for src in files:
        name = pathlib.Path(src).stem + '.webp'
        im = Image.open(src)
        n  = getattr(im, 'n_frames', 1)
        im.seek(0)
        off = paper_offset(im.convert('RGB'))
        durs = frame_durations(pathlib.Path(src), n)

        # a first pass at default size tells us whether this one needs squeezing
        steps = ((ANIM_PX, 88),) if n == 1 else ((ANIM_PX, ANIM_Q), (640, HEAVY_Q))   # stills: no size pressure
        for px, q in steps:
            frames, it = [], Image.open(src)
            for i in range(n):
                it.seek(i)
                f = it.convert('RGB')
                if f.width != f.height:            # not square: centre-crop, never stretch
                    m = min(f.size); l, u = (f.width - m) // 2, (f.height - m) // 2
                    f = f.crop((l, u, l + m, u + m))
                f = f.resize((px, px), Image.LANCZOS)
                a = np.clip(np.array(f).astype(np.int16) + off, 0, 255)
                if n == 1:                         # stills: the image model paints an inner frame in a
                    lo = a.min(2); ch = a.max(2) - lo   # second off-white; pull near-neutral whites to paper
                    w = np.clip((lo - 222) / 14, 0, 1) * np.clip((22 - ch) / 10, 0, 1)
                    a = (a * (1 - w[..., None]) + np.array(PAPER) * w[..., None])
                frames.append(Image.fromarray(a.astype(np.uint8)))
            out = IMGDIR / name
            frames[0].save(out, save_all=True, append_images=frames[1:],
                           duration=durs, loop=0, quality=q, method=4)
            mb = out.stat().st_size / 1024 / 1024
            if mb <= 5 or q in (HEAVY_Q, 88):
                break                      # good enough, or already the low setting

        frames[0].resize((POSTER_PX, POSTER_PX), Image.LANCZOS).save(
            POSTER / name, 'WEBP', quality=POSTER_Q, method=6)
        total += mb
        print(f'{name:22s} {n:3d} frames  {sum(durs)/1000:4.1f} s loop -> {mb:5.2f} MB')
    print(f'\ntotal animation {total:.1f} MB in {IMGDIR}')
    print('now run:  python3 build.py')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
