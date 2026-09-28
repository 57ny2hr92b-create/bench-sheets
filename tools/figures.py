"""Figure generators: SVG in the Bench Sheet vocabulary from a few numbers in the recipe YAML.

Vocabulary (design system): solid = edges; dashed 3/2 = fold or cut; arrow = movement; ticked line =
dimension, labelled in metric at 12 px; 45° hatch = filling; sparse stipple = crumb. 1 px black strokes,
no fills but black, IBM Plex Sans. Imprecision only on edges that are imprecise in life (a spread
frosting), never on anything measured against.

A figure item with `gen:` is rendered here at build time; `svg:` items are files in recipes/figures/.

  {gen: tray,    pan: half, cols: 4, rows: 3, piece: 45, spread: 90}          # portions on a sheet, mm
  {gen: tray,    pan: half, cols: 3, rows: 4, piece: [100, 25], gap: 30}        # oblong pieces (fingers, éclairs): [length, width] mm; gap packs them at piece + gap, centred
  {gen: cut,     pan: 9x13, cols: 6, rows: 4, sling: long}                      # cut map; first two cuts numbered; optional parchment sling
  {gen: section, layers: [[sponge, 25], [filling, 8], [sponge, 25]], frosting: 4, width: 120}
  {gen: dimensions, width: 300, height: 200, thickness: 5}                     # rolled sheet, top + edge
  {gen: fold, kind: letter}                                                      # letter | book | single
  {gen: gauge, diameters: [30, 40, 50]}                                         # actual size, with 5 cm bar
  {gen: gauge, oblongs: [[100, 25]]}                                            # actual-size piping guide for oblong pieces, [length, width] mm

All lengths in mm. `scale` (px per mm) defaults per type; the same scale as the hand-drawn figures.
"""
import math, random

PANS = {  # interior, mm (w, h)
    'half': (430, 300), 'quarter': (300, 215), '9x13': (330, 230), '8x8': (203, 203), '9x9': (229, 229),
    '9x5': (229, 127),
}
PAN_NAMES = {'half': 'Half sheet', 'quarter': 'Quarter sheet', '9x13': '9 × 13 in', '8x8': '8 × 8 in', '9x9': '9 × 9 in', '9x5': '9 × 5 in'}
KINDS = {'sponge': 'stipple', 'cake': 'stipple', 'savoiardi': 'stipple', 'crust': 'dense', 'filling': 'hatch', 'cream': 'hatch',
         'curd': 'hatch', 'jam': 'hatch', 'glaze': 'solid', 'ganache': 'solid', 'plain': 'none'}
FONT = 'font-family="IBM Plex Sans, sans-serif" font-size="12" fill="#000000" stroke="none"'
GREY = '#5C5C5C'
RULE = '#BDBDBD'
DASH = 'stroke-dasharray="3 2"'


class FigureError(ValueError):
    pass


def _svg(w, h, body, label):
    return (f'<svg aria-label="{label}" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" fill="none" '
            f'stroke="#000000" stroke-width="1">\n{body}\n</svg>')


def _dim_h(x1, x2, y, text, above=True):
    ty = y - 4 if above else y + 14
    return (f'<line x1="{x1:.1f}" x2="{x2:.1f}" y1="{y:.1f}" y2="{y:.1f}"/>'
            f'<line x1="{x1:.1f}" x2="{x1:.1f}" y1="{y-3:.1f}" y2="{y+3:.1f}"/><line x1="{x2:.1f}" x2="{x2:.1f}" y1="{y-3:.1f}" y2="{y+3:.1f}"/>'
            f'<text {FONT} text-anchor="middle" x="{(x1+x2)/2:.1f}" y="{ty:.1f}">{text}</text>')


def _dim_v(x, y1, y2, text, left=False):
    t = (f'<text {FONT} text-anchor="end" x="{x-6:.1f}" y="{(y1+y2)/2+4:.1f}">{text}</text>' if left
         else f'<text {FONT} x="{x+6:.1f}" y="{(y1+y2)/2+4:.1f}">{text}</text>')
    return (f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y1:.1f}" y2="{y2:.1f}"/>'
            f'<line x1="{x-3:.1f}" x2="{x+3:.1f}" y1="{y1:.1f}" y2="{y1:.1f}"/><line x1="{x-3:.1f}" x2="{x+3:.1f}" y1="{y2:.1f}" y2="{y2:.1f}"/>' + t)


def _hatch(x, y, w, h, uid, pitch=6):
    out = [f'<clipPath id="h{uid}"><rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"/></clipPath>', f'<g clip-path="url(#h{uid})">']
    i = -int(h)
    while i < w + h:
        out.append(f'<line x1="{x+i:.1f}" y1="{y+h:.1f}" x2="{x+i+h:.1f}" y2="{y:.1f}"/>')
        i += pitch
    out.append('</g>')
    return ''.join(out)


def _stipple(x, y, w, h, seed, density=0.006):
    rnd = random.Random(seed)
    return ''.join(f'<circle cx="{x+rnd.random()*w:.1f}" cy="{y+rnd.random()*h:.1f}" r="0.6" fill="#000000" stroke="none"/>'
                   for _ in range(int(w * h * density)))


def _wavy_cap(x, y, w, h, r, amp=1.6, seed=7):
    """Frosting outline: rounded top corners, straight sides and floor, a top edge that wobbles ±amp px.
    Seeded, so a rebuild draws the same line."""
    rnd = random.Random(seed)
    segs = max(6, int(w / 28))
    pts = []
    for i in range(segs + 1):
        t = i / segs
        yy = y + amp * (0.6 * math.sin(t * 2 * math.pi * 1.5 + rnd.random() * 0.4) + 0.4 * math.sin(t * 2 * math.pi * 3.2 + 1.3)) + rnd.uniform(-0.3, 0.3)
        pts.append((x + r + (w - 2 * r) * t, yy))
    d = f'M{x:.1f} {y+h:.1f} L{x:.1f} {y+r:.1f} Q{x:.1f} {y:.1f} {x+r:.1f} {pts[0][1]:.1f} '
    for i in range(1, len(pts)):
        (x1, y1), (x2, y2) = pts[i - 1], pts[i]
        d += f'Q{(x1+x2)/2:.1f} {y1:.1f} {x2:.1f} {y2:.1f} '
    d += f'Q{x+w:.1f} {y:.1f} {x+w:.1f} {y+r:.1f} L{x+w:.1f} {y+h:.1f} Z'
    return f'<path d="{d}"/>'


def _pan(spec):
    pan = str(spec.get('pan', ''))
    if pan in PANS: return PANS[pan], PAN_NAMES[pan]
    if 'size' in spec and isinstance(spec['size'], (list, tuple)) and len(spec['size']) == 2:
        return tuple(spec['size']), f'{spec["size"][0]} × {spec["size"][1]} mm'
    raise FigureError(f'pan must be one of {sorted(PANS)} or size: [w, h] in mm')


# ---------------------------------------------------------------- tray
def tray(spec):
    (pw, ph), pname = _pan(spec)
    cols, rows = int(spec['cols']), int(spec['rows'])
    oblong = isinstance(spec['piece'], (list, tuple))
    if oblong:
        if len(spec['piece']) != 2: raise FigureError('an oblong piece is [length, width] mm')
        plen, pwid = (float(v) for v in spec['piece'])
        if plen <= 0 or pwid <= 0 or pwid > plen: raise FigureError('oblong piece needs length ≥ width > 0')
        piece = spread = plen
    else:
        piece, spread = float(spec['piece']), float(spec.get('spread', spec['piece']))
    if cols < 1 or rows < 1: raise FigureError('cols and rows must be ≥ 1')
    if spread < piece: raise FigureError('spread must be ≥ piece')
    s = float(spec.get('scale', 0.5))
    W, H = pw * s, ph * s
    x0, y0 = 20.5, 24.5
    body = [f'<rect x="{x0}" y="{y0}" width="{W:.1f}" height="{H:.1f}"/>']
    gap = spec.get('gap')
    if gap is not None:  # pack at piece + gap and centre the block, instead of spreading over the pan
        gap = float(gap)
        if gap < 0: raise FigureError('gap must be ≥ 0 mm')
        pc, pr = ((plen if oblong else piece) + gap) * s, ((pwid if oblong else piece) + gap) * s
        bx, by = (x0 + (W - pc * cols + gap * s) / 2 - pc / 2, y0 + (H - pr * rows + gap * s) / 2 - pr / 2)
        if pc * cols - gap * s > W + 0.5 or pr * rows - gap * s > H + 0.5: raise FigureError(f'{cols} × {rows} pieces with a {gap:g} mm gap do not fit the {pname}')
    else:
        pc, pr = W / cols, H / rows
        bx, by = x0, y0
    if oblong and (plen * s > pc or pwid * s > pr): raise FigureError(f'{cols} × {rows} pieces of {plen:g} × {pwid:g} mm do not fit the {pname}')
    for r in range(rows):
        for c in range(cols):
            cx, cy = bx + pc * (c + 0.5), by + pr * (r + 0.5)
            if oblong:
                w, h = plen * s, pwid * s
                body.append(f'<rect x="{cx-w/2:.1f}" y="{cy-h/2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h/2:.1f}" fill="#000000"/>')
                continue
            body.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{piece*s/2:.1f}" fill="#000000"/>')
            if spread > piece:
                body.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{spread*s/2:.1f}" {DASH}/>')
    if oblong:
        # gap between pieces, not centre pitch: that is what the hand measures at the tray
        if cols > 1: body.append(_dim_h(bx + pc * 0.5 + plen * s / 2, bx + pc * 1.5 - plen * s / 2, y0 - 8, f'{(pc/s - plen)/10:g} cm'))
        if rows > 1: body.append(_dim_v(x0 + W + 10, by + pr * 0.5 + pwid * s / 2, by + pr * 1.5 - pwid * s / 2, f'{(pr/s - pwid)/10:g} cm'))
        label = (f'{pname} to scale, {pw/10:.0f} by {ph/10:.0f} centimetres, with {cols*rows} pieces of {plen/10:g} by {pwid/10:g} centimetres '
                 f'in {rows} rows of {cols}, gaps labelled')
        return _svg(x0 + W + 64, y0 + H + 12, '\n'.join(body), label)
    if cols > 1: body.append(_dim_h(bx + pc * 0.5, bx + pc * 1.5, y0 - 8, f'{pc/s/10:g} cm'))
    if rows > 1: body.append(_dim_v(x0 + W + 10, by + pr * 0.5, by + pr * 1.5, f'{pr/s/10:g} cm'))
    label = (f'{pname} to scale, {pw/10:.0f} by {ph/10:.0f} centimetres, with {cols*rows} portions of {piece/10:g} centimetres '
             f'in {rows} rows of {cols}' + (f'; dashed circles show the {spread/10:g} centimetre baked size' if spread > piece else ''))
    return _svg(x0 + W + 64, y0 + H + 12, '\n'.join(body), label)


# ---------------------------------------------------------------- cut
def cut(spec):
    (pw, ph), pname = _pan(spec)
    cols, rows = int(spec['cols']), int(spec['rows'])
    if cols < 1 or rows < 1: raise FigureError('cols and rows must be ≥ 1')
    s = float(spec.get('scale', 0.5))
    W, H = pw * s, ph * s
    sling = spec.get('sling')
    x0 = 36.5 + (14 if sling == 'long' else 0); y0 = 28.5 + (14 if sling == 'short' else 0)
    body = []  # 'long' | 'short': a parchment strip over the pan, hatched where it overhangs
    if sling:
        ov = 14
        # the strip is cut to the pan's width, so inside the pan it has no edges of its own; only the
        # overhanging tabs show, outlined and hatched, the full height (or width) of the pan
        if sling == 'long':
            body += [f'<rect x="{x0-ov:.1f}" y="{y0}" width="{ov}" height="{H:.1f}"/>', _hatch(x0 - ov, y0, ov, H, uid='sl'),
                     f'<rect x="{x0+W:.1f}" y="{y0}" width="{ov}" height="{H:.1f}"/>', _hatch(x0 + W, y0, ov, H, uid='sr')]
        elif sling == 'short':
            body += [f'<rect x="{x0}" y="{y0-ov:.1f}" width="{W:.1f}" height="{ov}"/>', _hatch(x0, y0 - ov, W, ov, uid='st'),
                     f'<rect x="{x0}" y="{y0+H:.1f}" width="{W:.1f}" height="{ov}"/>', _hatch(x0, y0 + H, W, ov, uid='sb')]
        else:
            raise FigureError("sling must be 'long' or 'short'")
    body.append(f'<rect x="{x0}" y="{y0}" width="{W:.1f}" height="{H:.1f}" stroke-width="1.5"/>')
    for c in range(1, cols):
        x = x0 + W * c / cols
        body.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y0}" y2="{y0+H:.1f}" {DASH}/>')
    for r in range(1, rows):
        y = y0 + H * r / rows
        body.append(f'<line x1="{x0}" x2="{x0+W:.1f}" y1="{y:.1f}" y2="{y:.1f}" {DASH}/>')
    if spec.get('first_cuts', True) and cols % 2 == 0 and rows % 2 == 0:
        mx, my = x0 + W / 2, y0 + H / 2
        ty = y0 - (14 if sling == 'short' else 0); lx = x0 - (14 if sling == 'long' else 0)
        body.append(f'<line x1="{mx:.1f}" x2="{mx:.1f}" y1="{ty-14}" y2="{ty-4}"/><path d="M{mx-3:.1f} {ty-8} L{mx:.1f} {ty-4} L{mx+3:.1f} {ty-8}"/>'
                    f'<text {FONT} text-anchor="middle" x="{mx:.1f}" y="{ty-18}">1</text>')
        body.append(f'<line x1="{lx-14}" x2="{lx-4}" y1="{my:.1f}" y2="{my:.1f}"/><path d="M{lx-8} {my-3:.1f} L{lx-4} {my:.1f} L{lx-8} {my+3:.1f}"/>'
                    f'<text {FONT} text-anchor="end" x="{lx-18}" y="{my+4:.1f}">2</text>')
    body.append(_dim_h(x0, x0 + W / cols, y0 + H + 10 + (14 if sling == 'short' else 0), f'{pw/cols:.0f} mm', above=False))
    body.append(_dim_v(x0 + W + 10 + (14 if sling == 'long' else 0), y0 + H - H / rows, y0 + H, f'{ph/rows:.0f} mm'))
    label = (f'{pname}, {pw/10:.0f} by {ph/10:.0f} centimetres, ' + (f'parchment sling over the {sling} sides, ' if sling else '')
             + f'cut {cols} by {rows} into {cols*rows} pieces of {pw/cols:.0f} by {ph/rows:.0f} millimetres')
    return _svg(x0 + W + 70 + (14 if sling == 'long' else 0), y0 + H + 30 + (14 if sling == 'short' else 0), '\n'.join(body), label)


# ---------------------------------------------------------------- section
def section(spec):
    layers = spec['layers']
    if not layers or not all(isinstance(l, (list, tuple)) and len(l) == 2 for l in layers):
        raise FigureError('layers must be a list of [kind, height_mm], bottom to top')
    for k, h in layers:
        if k not in KINDS: raise FigureError(f'layer kind {k!r} not in {sorted(KINDS)}')
        if not isinstance(h, (int, float)) or h <= 0: raise FigureError(f'layer {k}: height must be a positive number of mm')
    frosting = float(spec.get('frosting', 0) or 0)
    width = float(spec.get('width', 120))
    s = float(spec.get('scale', 1.6))
    W, total = width * s, sum(h for _, h in layers)
    H = total * s; f = frosting * s
    x0, y_top = 70.5, 20.5 + f
    body = []
    y = y_top + H
    labels = []
    for i, (kind, h) in enumerate(layers):
        hp = h * s; y -= hp
        body.append(f'<rect x="{x0}" y="{y:.1f}" width="{W:.1f}" height="{hp:.1f}"/>')
        style = KINDS[kind]
        if style == 'stipple': body.append(_stipple(x0, y, W, hp, seed=i))
        elif style == 'dense': body.append(_stipple(x0, y, W, hp, seed=i, density=0.02))
        elif style == 'hatch': body.append(_hatch(x0, y, W, hp, uid=i))
        elif style == 'solid': body.append(f'<rect x="{x0}" y="{y:.1f}" width="{W:.1f}" height="{hp:.1f}" fill="#000000"/>')
        labels.append((y, hp, f'{kind} · {h:g} mm'))
    if frosting:
        body.append(_wavy_cap(x0 - f, y_top - f, W + 2 * f, H + f, f))
    xd = x0 + W + f + 14
    seen = set()
    for yy, hp, text in labels:
        if text in seen: continue
        seen.add(text)
        body.append(_dim_v(xd, yy, yy + hp, text))
    if frosting: body.append(f'<text {FONT} x="{xd+6:.1f}" y="{y_top-f+4:.1f}">frosting · {frosting:g} mm</text>')
    body.append(_dim_v(x0 - f - 12, y_top, y_top + H, f'{total:g} mm', left=True))
    body.append(_dim_h(x0, x0 + W, y_top + H + f + 12, f'{width:g} mm', above=False))
    label = 'Cross-section, bottom to top: ' + ', '.join(f'{k} {h:g} millimetres' for k, h in layers) + (f', {frosting:g} millimetres of frosting over' if frosting else '')
    return _svg(xd + 120, y_top + H + f + 34, '\n'.join(body), label)


# ---------------------------------------------------------------- dimensions
def dimensions(spec):
    w, h, t = float(spec['width']), float(spec['height']), float(spec.get('thickness', 0) or 0)
    s = float(spec.get('scale', 0.5))
    W, H, T = w * s, h * s, max(3, t * s)
    x0, y0 = 20.5, 24.5
    body = [f'<rect x="{x0}" y="{y0}" width="{W:.1f}" height="{H:.1f}"/>',
            _dim_h(x0, x0 + W, y0 - 8, f'{w:g} mm'),
            _dim_v(x0 + W + 10, y0, y0 + H, f'{h:g} mm')]
    yb = y0 + H + 16
    if t:
        body.append(f'<rect x="{x0}" y="{yb:.1f}" width="{W:.1f}" height="{T:.1f}"/>')
        body.append(f'<line x1="{x0+W+2:.1f}" x2="{x0+W+16:.1f}" y1="{yb+T/2:.1f}" y2="{yb+T/2:.1f}"/><text {FONT} x="{x0+W+20:.1f}" y="{yb+T/2+4:.1f}">{t:g} mm</text>')
    label = f'Rolled sheet {w:g} by {h:g} millimetres' + (f', {t:g} millimetres thick' if t else '')
    return _svg(x0 + W + 80, (yb + T + 8) if t else (y0 + H + 8), '\n'.join(body), label)


# ---------------------------------------------------------------- fold
def fold(spec):
    kind = spec.get('kind', 'letter')
    plans = {'letter': (3, [(0, 'up'), (2, 'down')], 3), 'book': (4, [(0, 'in'), (3, 'in'), (None, 'close')], 4), 'single': (2, [(0, 'up')], 2)}
    if kind not in plans: raise FigureError(f'fold kind must be one of {sorted(plans)}')
    panels, moves, layers = plans[kind]
    w, h = 60, 120
    frames = []
    x = 20.5
    # frame 1: flat with dashed panel lines and first arrow
    b = [f'<rect x="{x}" y="20.5" width="{w}" height="{h}"/>']
    for i in range(1, panels):
        yy = 20.5 + h * i / panels
        b.append(f'<line x1="{x}" x2="{x+w}" y1="{yy:.1f}" y2="{yy:.1f}" {DASH}/>')
    b.append(f'<path d="M{x+w/2:.1f} {20.5+h-8:.1f} Q{x+w/2+10:.1f} {20.5+h/2+20:.1f} {x+w/2:.1f} {20.5+h*(panels-1)/panels+6:.1f}"/>'
             f'<path d="M{x+w/2-3:.1f} {20.5+h*(panels-1)/panels+11:.1f} L{x+w/2:.1f} {20.5+h*(panels-1)/panels+6:.1f} L{x+w/2+3:.1f} {20.5+h*(panels-1)/panels+11:.1f}"/>')
    frames.append(('\n'.join(b), 1))
    x += w + 40
    # frame 2: partly folded
    hh = h * (panels - 1) / panels if kind != 'book' else h / 2
    b = [f'<rect x="{x}" y="{20.5+h-hh:.1f}" width="{w}" height="{hh:.1f}"/>',
         f'<line x1="{x}" x2="{x+w}" y1="{20.5+h-h/panels:.1f}" y2="{20.5+h-h/panels:.1f}"/>']
    b.append(f'<path d="M{x+w/2:.1f} {20.5+h-hh+8:.1f} Q{x+w/2-10:.1f} {20.5+h-hh/2:.1f} {x+w/2:.1f} {20.5+h-h/panels-6:.1f}"/>'
             f'<path d="M{x+w/2-3:.1f} {20.5+h-h/panels-11:.1f} L{x+w/2:.1f} {20.5+h-h/panels-6:.1f} L{x+w/2+3:.1f} {20.5+h-h/panels-11:.1f}"/>')
    frames.append(('\n'.join(b), 2))
    x += w + 40
    # frame 3: packet + edge section showing layers
    ph = h / panels if kind != 'book' else h / 4
    b = [f'<rect x="{x}" y="{20.5+h-ph:.1f}" width="{w}" height="{ph:.1f}"/>']
    ys = 20.5 + h + 10
    for i in range(layers):
        b.append(f'<rect x="{x}" y="{ys+i*4:.1f}" width="{w}" height="4" rx="2"/>')
    b.append(f'<text {FONT} fill="{GREY}" x="{x+w+8:.1f}" y="{ys+layers*2+4:.1f}">{layers} layers</text>')
    frames.append(('\n'.join(b), 3))
    body = []
    xs = [20.5, 20.5 + w + 40, 20.5 + 2 * (w + 40)]
    for (fb, n), fx in zip(frames, xs):
        body.append(fb)
        body.append(f'<text {FONT} text-anchor="middle" x="{fx+w/2:.1f}" y="{20.5+h+layers*4+30:.1f}">{n}</text>')
    label = f'{kind.capitalize()} fold in three frames: flat with fold lines, first fold made, finished packet with an edge view of {layers} layers'
    return _svg(xs[-1] + w + 80, 20.5 + h + layers * 4 + 40, '\n'.join(body), label)


# ---------------------------------------------------------------- gauge
def gauge(spec):
    """Actual size at 96 px per inch (3.7795 px/mm), with a 5 cm check bar. Print at 100%."""
    ds = [float(d) for d in spec.get('diameters', [])]
    obs = [(float(a), float(b)) for a, b in spec.get('oblongs', [])]
    if not ds and not obs: raise FigureError('give diameters (round) or oblongs ([length, width]) in mm')
    if any(d <= 0 for d in ds) or any(a <= 0 or b <= 0 or b > a for a, b in obs): raise FigureError('sizes must be positive mm; oblong length ≥ width')
    s = 96 / 25.4
    x, y = 20.5, 20.5
    hmax = max([d for d in ds] + [b for _, b in obs]) * s
    body = []
    for d in ds:
        r = d * s / 2
        body.append(f'<circle cx="{x+r:.1f}" cy="{y+hmax/2:.1f}" r="{r:.1f}"/>'
                    f'<text {FONT} text-anchor="middle" x="{x+r:.1f}" y="{y+hmax+16:.1f}">{d:g} mm</text>')
        x += 2 * r + 20
    for a, b in obs:
        w, h = a * s, b * s
        body.append(f'<rect x="{x:.1f}" y="{y+(hmax-h)/2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h/2:.1f}"/>'
                    f'<text {FONT} text-anchor="middle" x="{x+w/2:.1f}" y="{y+hmax+16:.1f}">{a:g} × {b:g} mm</text>')
        x += w + 20
    yb = y + hmax + 34
    body.append(_dim_h(20.5, 20.5 + 50 * s, yb + 8, 'check 5 cm · print at 100%', above=False))
    what = ', '.join([f'circles of {d:g}' for d in ds] + [f'an oblong of {a:g} by {b:g}' for a, b in obs])
    return _svg(max(x, 20.5 + 50 * s + 20), yb + 30, '\n'.join(body), f'Actual-size gauge: {what} millimetres, with a 5 centimetre check bar')


GENERATORS = dict(tray=tray, cut=cut, section=section, dimensions=dimensions, fold=fold, gauge=gauge)


def render(spec):
    """spec: a figure item with `gen`. Returns SVG text; raises FigureError on a bad spec."""
    g = spec.get('gen')
    if g not in GENERATORS: raise FigureError(f'gen must be one of {sorted(GENERATORS)}')
    try:
        return GENERATORS[g](spec)
    except KeyError as e:
        raise FigureError(f'{g}: missing {e.args[0]}')
