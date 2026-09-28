"""Drawing helpers shared by all scenes."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from common import *

FD = "../fonts/"
_fonts = {}


def font(name, size):
    key = (name, size)
    if key not in _fonts:
        path = FD + {"xb": "Poppins-ExtraBold.ttf", "b": "Poppins-Bold.ttf", "sb": "Poppins-SemiBold.ttf",
                     "m": "Poppins-Medium.ttf", "mono": "JetBrainsMono.ttf", "hand": "Caveat.ttf"}[name]
        f = ImageFont.truetype(path, size)
        if name == "mono":
            try:
                f.set_variation_by_axes([600])
            except Exception:
                pass
        if name == "hand":
            try:
                f.set_variation_by_axes([700])
            except Exception:
                pass
        _fonts[key] = f
    return _fonts[key]


def text_size(txt, f):
    b = f.getbbox(txt)
    return b[2] - b[0], b[3] - b[1], b


_tcache = {}


def text_layer(txt, f, fill, shadow=0.75, blur=10, stroke=0, stroke_fill=None, glow=None):
    """RGBA layer of text with a soft drop shadow; cached."""
    key = (txt, id(f), fill, shadow, blur, stroke, stroke_fill, glow)
    if key in _tcache:
        return _tcache[key]
    w, h, b = text_size(txt, f)
    pad = blur * 3 + 10 + stroke
    L = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    if shadow or glow:
        sh = Image.new("L", L.size, 0)
        ImageDraw.Draw(sh).text((pad - b[0], pad - b[1] + blur * 0.35), txt, font=f, fill=255,
                                stroke_width=stroke + 2)
        sh = sh.filter(ImageFilter.GaussianBlur(blur))
        col = glow if glow else (0, 0, 0)
        a = shadow if not glow else 0.9
        base = Image.new("RGBA", L.size, col + (0,))
        base.putalpha(sh.point(lambda v: int(v * a)))
        L = Image.alpha_composite(L, base)
    d = ImageDraw.Draw(L)
    d.text((pad - b[0], pad - b[1]), txt, font=f, fill=fill, stroke_width=stroke,
           stroke_fill=stroke_fill)
    _tcache[key] = (L, pad)
    return L, pad


def paste_layer(img, L, cx, cy, alpha=1.0, scale=1.0, anchor="c"):
    """Composite RGBA layer onto RGB/RGBA image centred at (cx, cy)."""
    if alpha <= 0.003:
        return
    if abs(scale - 1) > 1e-3:
        L = L.resize((max(1, int(L.width * scale)), max(1, int(L.height * scale))), Image.BICUBIC)
    if anchor == "c":
        x, y = int(cx - L.width / 2), int(cy - L.height / 2)
    elif anchor == "l":
        x, y = int(cx), int(cy - L.height / 2)
    else:
        x, y = int(cx - L.width), int(cy - L.height / 2)
    m = L.getchannel("A")
    if alpha < 0.999:
        m = m.point(lambda v: int(v * alpha))
    img.paste(L.convert("RGB") if img.mode == "RGB" else L, (x, y), m)


def draw_text(img, txt, f, cx, cy, fill=(255, 255, 255), alpha=1.0, scale=1.0, shadow=0.75, blur=10,
              anchor="c", glow=None):
    L, pad = text_layer(txt, f, fill, shadow, blur, glow=glow)
    paste_layer(img, L, cx, cy, alpha, scale, anchor)


def glow_add(arr, cx, cy, r, color, inten, squash=1.0):
    """Additive gaussian glow into float32 HxWx3 array."""
    if inten <= 0.002 or r < 1:
        return
    Hh, Ww = arr.shape[:2]
    ry = r * squash
    x0, x1 = int(max(0, cx - r * 2.2)), int(min(Ww, cx + r * 2.2))
    y0, y1 = int(max(0, cy - ry * 2.2)), int(min(Hh, cy + ry * 2.2))
    if x1 <= x0 or y1 <= y0:
        return
    xs = (np.arange(x0, x1) - cx) / r
    ys = (np.arange(y0, y1) - cy) / ry
    g = np.exp(-(ys[:, None] ** 2 + xs[None, :] ** 2) * 1.6)
    arr[y0:y1, x0:x1] += g[..., None] * (np.array(color, np.float32) * inten)


def vignette(Ww, Hh, strength=0.55, power=2.2):
    ys = (np.arange(Hh) - Hh / 2) / (Hh / 2)
    xs = (np.arange(Ww) - Ww / 2) / (Ww / 2)
    d = np.sqrt(xs[None, :] ** 2 * 0.9 + ys[:, None] ** 2 * 0.75)
    return (1 - strength * np.clip(d, 0, 1.5) ** power)[..., None].astype(np.float32)


VIG = vignette(W, H)
VIG_SOFT = vignette(W, H, 0.3)


def grain(arr, amt, seed):
    r = np.random.default_rng(seed)
    n = r.normal(0, amt, (H // 2, W // 2)).astype(np.float32)
    n = np.repeat(np.repeat(n, 2, 0), 2, 1)
    arr += n[..., None]


def to_img(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def to_arr(img):
    return np.asarray(img.convert("RGB"), dtype=np.float32)


def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def check_icon(size, circle=(22, 170, 80), tick=(255, 255, 255)):
    S = size * 4
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, S - 1, S - 1), fill=circle)
    w = int(S * 0.11)
    d.line([(S * 0.27, S * 0.52), (S * 0.44, S * 0.68), (S * 0.74, S * 0.34)], fill=tick, width=w, joint="curve")
    for p in [(S * 0.27, S * 0.52), (S * 0.74, S * 0.34)]:
        d.ellipse((p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2), fill=tick)
    return im.resize((size, size), Image.LANCZOS)


def x_icon(size, col=(235, 50, 60)):
    S = size * 4
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = int(S * 0.16)
    d.line([(S * .15, S * .15), (S * .85, S * .85)], fill=col, width=w)
    d.line([(S * .85, S * .15), (S * .15, S * .85)], fill=col, width=w)
    return im.resize((size, size), Image.LANCZOS)


def back_in_out(x, c1=1.25):
    """Anticipation (dips below 0) then overshoot (~6-7% past 1) and settle."""
    x = clamp(x)
    c2 = c1 * 1.525
    if x < 0.5:
        return ((2 * x) ** 2 * ((c2 + 1) * 2 * x - c2)) / 2
    return ((2 * x - 2) ** 2 * ((c2 + 1) * (x * 2 - 2) + c2) + 2) / 2


def pop(t, t0, dur=0.55, t_out=None, out_dur=0.35, rise=46):
    """Entrance with pull-back + overshoot; eased exit. Returns (alpha, scale, dy)."""
    if t < t0:
        return 0.0, 1.0, 0.0
    v = back_in_out((t - t0) / dur)
    a = ease_out(lin(t, t0 + 0.08, t0 + 0.3))
    s = 0.93 + 0.07 * v
    dy = rise * (1 - v)
    if t_out is not None and t > t_out - out_dur:
        q = ease_in(lin(t, t_out - out_dur, t_out))
        a *= 1 - q
        dy -= 18 * q
        s *= 1 - 0.03 * q
    return a, s, dy


_chips = {}


def chip(txt):
    """Dark pill with a green check: the courier 'finding' a landmark."""
    if txt in _chips:
        return _chips[txt]
    f = font("sb", 30)
    tw, th, b = text_size(txt, f)
    h = 64
    w = tw + 24 + 44 + 26
    S = 2
    im = Image.new("RGBA", ((w + 40) * S, (h + 40) * S), (0, 0, 0, 0))
    sh = Image.new("L", im.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((20 * S, 26 * S, (20 + w) * S, (26 + h) * S), h * S // 2, fill=150)
    sh = sh.filter(ImageFilter.GaussianBlur(10 * S))
    im.putalpha(sh)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20 * S, 20 * S, (20 + w) * S, (20 + h) * S), h * S // 2, fill=(14, 20, 34, 215),
                        outline=(90, 220, 140, 255), width=2 * S)
    im = im.resize((w + 40, h + 40), Image.LANCZOS)
    ic = check_icon(40)
    im.alpha_composite(ic, (20 + 14, 20 + 12))
    d = ImageDraw.Draw(im)
    d.text((20 + 14 + 44 + 10 - b[0], 20 + (h - th) // 2 - b[1]), txt, font=f, fill=(235, 255, 240))
    _chips[txt] = im
    return im


def draw_chip(img, txt, cx, cy, t, t0, dur=1.6, anchor="c"):
    if t < t0 or t > t0 + dur:
        return
    a, s, dy = pop(t, t0, 0.45, t0 + dur, 0.3, rise=22)
    paste_layer(img, chip(txt), cx, cy + dy, a, 0.75 + 0.25 * s if s < 1 else s, anchor)
