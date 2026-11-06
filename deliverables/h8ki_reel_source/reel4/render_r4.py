"""Reel #4 "Di aplikasi vs Kenyataannya #2": the address is only "pintu biru dekat masjid".
Opens full screen on two faces (the courier asking a smiling old man) with the hook, then the tracking app slides
in on top (the format of Reel #3). Story: asks the way -> walks past the mosque -> knocks on the blue door ->
Nenek takes the parcel -> the family photo comes out of the box. Kling footage of "Kiriman untuk Nenek", as filmed
(no logo patch), with the film's warm grade. Every cut sits on the 100 bpm grid (beat = 0.6 s).
  python3 render_r4.py OUT.mp4 [preview t ...]"""
import sys, math, subprocess
from functools import lru_cache
from multiprocessing import Pool
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
from gfx import font, paste_layer, draw_text, check_icon, pop, back_in_out
from common import clamp, lin, ease_io, ease_out
import interp

W, H, FPS = 1080, 1920, 24
PANEL = 900
INK, GREY = (24, 28, 40), (104, 112, 124)
RED, GREEN, BLUE, BG, GOLD = (227, 24, 30), (4, 152, 68), (24, 119, 242), (244, 245, 248), (214, 140, 20)
FULL_END, SPLIT_T = 1.4, 1.8                  # full-screen hook (long enough to read), then the app slides in
END_T = 14.4
TRANS = 0.35
CARD_T = END_T + 0.3
DUR = 15.7

# (t0, t1, clip, first src, last src, crop cx, crop cy, crop w, warm grade)
SHOTS = [
    (0.0, 3.0, "k1", 73, 143, 540, 760, 1080, 1.0),     # he asks a smiling old man, who points the way
    (3.0, 5.4, "k1", 150, 210, 540, 900, 1080, 0.3),    # walks towards the minaret (bag as filmed)
    (5.4, 7.2, "k1", 226, 262, 540, 800, 1080, 1.0),    # knocks on the blue door
    (7.2, 9.6, "k1", 286, 350, 540, 880, 1080, 1.0),    # Nenek opens, takes the parcel with both hands
    (9.6, 11.4, "k2", 20, 64, 540, 880, 1080, 1.0),     # he bows and leaves, she opens the box
    (11.4, END_T, "k2", 64, 121, 540, 840, 1080, 1.0),  # the family photo comes out; she holds it close
]
PH = [0.0, 2.2, 3.0, 5.4, 7.2]


@lru_cache(maxsize=6)
def raw(clip, i):
    return np.asarray(Image.open(f"../fr/{clip}/f{i:04d}.png").convert("RGB"))


def src(clip, p):
    i0 = int(math.floor(p)); s = p - i0
    a = raw(clip, i0)
    return interp.between(a, raw(clip, i0 + 1), s) if s > 0.04 else a


def grade(a, s):
    """The warm late-afternoon grade of 'Kiriman untuk Nenek'."""
    x = a.astype(np.float32) / 255.0
    full = x ** 0.95 * np.array([1.10, 1.02, 0.82], np.float32)
    h, w = a.shape[:2]
    small = cv2.resize(full, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
    glow = cv2.resize(cv2.GaussianBlur(small, (0, 0), 8), (w, h), interpolation=cv2.INTER_LINEAR)
    full = full * 0.65 + np.maximum(full, glow) * 0.35
    out = np.clip(x * (1 - s) + full * s, 0, 1)
    out = out + 0.06 * (out - 0.5) * (1 - np.abs(2 * out - 1))
    return np.clip(out * 255, 0, 255).astype(np.uint8)


def shot_at(t):
    for sh in SHOTS:
        if sh[0] <= t < sh[1]:
            return sh
    return SHOTS[-1]


def footage(t, out_h, full=0.0):
    """Footage for time t, out_h tall. full=1: whole frame (the opening), full=0: the panel crop."""
    t0, t1, c, fa, fb, cx, cy, cw, warm = shot_at(t)
    u = clamp((t - t0) / (t1 - t0))
    a = src(c, fa + u * (fb - fa))
    sh, sw = a.shape[:2]
    z = 1 + 0.045 * u
    w = cw / z
    h = w * out_h / W
    ccy = cy * (1 - full) + (sh / 2) * full
    x0 = clamp(cx - w / 2, 0, sw - w); y0 = clamp(ccy - h / 2, 0, sh - h)
    M = np.float32([[W / w, 0, -x0 * W / w], [0, out_h / h, -y0 * out_h / h]])
    f = cv2.warpAffine(a, M, (W, out_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    f = grade(f, warm).astype(np.float32)
    yy, xx = np.mgrid[0:out_h, 0:W].astype(np.float32)
    vig = 1 - 0.22 * np.clip(np.sqrt(((xx - 540) / 640) ** 2 + ((yy - out_h / 2) / (out_h * 0.6)) ** 2), 0, 1.4) ** 2.2
    return np.clip(f * vig[..., None], 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ the app (top panel)
MX, MY, MW, MH = 30, 375, 1020, 325
S2 = 2
START, C1, C2, HOUSE = (150, 285), (150, 90), (860, 90), (860, 190)
PATH = [START, C1, C2, HOUSE]


def logo(width):
    im = np.asarray(Image.open("logo.jpg").convert("RGB"), np.float32)
    dist = np.max(np.abs(im - 247.0), axis=2)
    a = np.clip((dist - 6) / 40, 0, 1)
    col = np.clip((im - 247 * (1 - a[..., None])) / np.maximum(a[..., None], 1e-3), 0, 255)
    lg = Image.fromarray(np.dstack([col, a * 255]).astype(np.uint8), "RGBA")
    lg = lg.crop(lg.getbbox())
    return lg.resize((width, int(lg.height * width / lg.width)), Image.LANCZOS)


def pin(d, x, y, s, col):
    d.ellipse((x - s, y - 2.3 * s, x + s, y - 0.3 * s), fill=col)
    d.polygon([(x - 0.86 * s, y - 0.8 * s), (x + 0.86 * s, y - 0.8 * s), (x, y + 0.15 * s)], fill=col)


@lru_cache(maxsize=1)
def map_base():
    m = Image.new("RGB", (MW * S2, MH * S2), (236, 238, 232))
    d = ImageDraw.Draw(m)
    q = lambda x: x * S2
    rng = np.random.default_rng(11)
    for _ in range(46):
        x, y = rng.uniform(0, MW), rng.uniform(0, MH)
        bw, bh = rng.uniform(40, 110), rng.uniform(30, 70)
        d.rounded_rectangle((q(x), q(y), q(x + bw), q(y + bh)), q(6), fill=(224, 226, 220))
    roads = [((0, 305), (MW, 305), 30), ((150, 305), (150, 90), 24), ((150, 90), (MW, 90), 24),
             ((860, 90), (860, 215), 24), ((520, 90), (520, 305), 24)]
    for (a, b, wd) in roads:
        d.line([(q(a[0]), q(a[1])), (q(b[0]), q(b[1]))], fill=(214, 216, 212), width=q(wd + 6))
    for (a, b, wd) in roads:
        d.line([(q(a[0]), q(a[1])), (q(b[0]), q(b[1]))], fill=(255, 255, 255), width=q(wd))
    mx, my = 400, 30                                   # the mosque with its minaret, above the upper alley
    d.rectangle((q(mx - 34), q(my), q(mx + 34), q(my + 34)), fill=(196, 214, 204))
    d.ellipse((q(mx - 24), q(my - 22), q(mx + 24), q(my + 20)), fill=(150, 196, 170))
    d.rectangle((q(mx + 40), q(my - 26), q(mx + 48), q(my + 34)), fill=(150, 196, 170))
    d.rounded_rectangle((q(640), q(140), q(700), q(172)), q(6), fill=(252, 196, 120))   # warung
    d.rounded_rectangle((q(880), q(150), q(930), q(214)), q(6), fill=(110, 160, 220))   # the blue door
    f = font("m", 22 * S2)
    for txt, x, y in [("Masjid", mx - 2, 88 - 30), ("Warung", 670, 188), ("Pintu biru", 905, 240), ("Jl. Raya", 300, 305)]:
        tw = f.getlength(txt)
        d.text((q(x) - tw / 2, q(y) - 14 * S2), txt, font=f, fill=(128, 134, 140))
    for (a, b) in zip(PATH, PATH[1:]):                 # planned route, dashed
        L = math.dist(a, b); n = int(L / 22)
        for k in range(n):
            u0, u1 = k / n, (k + 0.55) / n
            d.line([(q(a[0] + (b[0] - a[0]) * u0), q(a[1] + (b[1] - a[1]) * u0)),
                    (q(a[0] + (b[0] - a[0]) * u1), q(a[1] + (b[1] - a[1]) * u1))], fill=(140, 186, 250), width=q(9))
    return m


def path_point(s):
    segs = [math.dist(a, b) for a, b in zip(PATH, PATH[1:])]
    dist = s * sum(segs); trail = [PATH[0]]
    for (a, b), L in zip(zip(PATH, PATH[1:]), segs):
        if dist <= L:
            u = dist / L
            p = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
            return p, trail + [p]
        dist -= L; trail.append(b)
    return PATH[-1], trail


def draw_map(t):
    m = map_base().copy()
    d = ImageDraw.Draw(m, "RGBA")
    q = lambda x: x * S2
    s = 0.0 if t < 3.0 else (ease_io(lin(t, 3.0, 5.3)) if t < 5.3 else 1.0)
    (px, py), trail = path_point(s)
    if len(trail) > 1:
        d.line([(q(x), q(y)) for x, y in trail], fill=BLUE + (255,), width=q(9), joint="curve")
    b = 16 * math.sin(math.pi * (t - 5.3) / 0.6) * math.exp(-(t - 5.3) * 3) if 5.3 <= t < 5.9 else 0
    hx, hy = HOUSE[0], HOUSE[1] - 14 - b
    pin(d, q(hx), q(hy), q(20), RED + (255,))
    d.rectangle((q(hx - 8), q(hy - 30), q(hx + 8), q(hy - 18)), fill=(255, 255, 255, 255))
    d.polygon([(q(hx - 12), q(hy - 29)), (q(hx + 12), q(hy - 29)), (q(hx), q(hy - 40))], fill=(255, 255, 255, 255))
    if t < 3.0:                                        # lost: wiggle + a question bubble
        px += 3 * math.sin(t * 7.3); py += 2 * math.sin(t * 5.1 + 1)
        bx, by = px + 34, py - 58
        d.rounded_rectangle((q(bx - 22), q(by - 22), q(bx + 22), q(by + 22)), q(12), fill=(255, 255, 255, 255),
                            outline=(200, 204, 210, 255), width=q(2))
        fq = font("xb", 30 * S2)
        d.text((q(bx) - fq.getlength("?") / 2, q(by) - 19 * S2), "?", font=fq, fill=RED + (255,))
    ph = (t * 1.1) % 1.0
    r = 16 + 40 * ph
    d.ellipse((q(px - r), q(py - r), q(px + r), q(py + r)), fill=BLUE + (int(70 * (1 - ph)),))
    d.ellipse((q(px - 22), q(py - 22), q(px + 22), q(py + 22)), fill=(255, 255, 255, 255))
    d.ellipse((q(px - 15), q(py - 15), q(px + 15), q(py + 15)), fill=BLUE + (255,))
    m = m.resize((MW, MH), Image.LANCZOS)
    mask = Image.new("L", (MW, MH), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, MW - 1, MH - 1), 28, fill=255)
    return m, mask


def icon(kind, s, col):
    S = s * 4
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, S - 1, S - 1), fill=col)
    w = (255, 255, 255); c = S / 2
    if kind == "alert":
        d.rounded_rectangle((c - S * 0.06, c - S * 0.27, c + S * 0.06, c + S * 0.08), int(S * 0.05), fill=w)
        d.ellipse((c - S * 0.07, c + S * 0.14, c + S * 0.07, c + S * 0.28), fill=w)
    elif kind == "chat":
        d.rounded_rectangle((c - S * 0.26, c - S * 0.2, c + S * 0.26, c + S * 0.14), int(S * 0.08), fill=w)
        d.polygon([(c - S * 0.14, c + S * 0.1), (c - S * 0.02, c + S * 0.1), (c - S * 0.18, c + S * 0.27)], fill=w)
        for k in (-1, 0, 1):
            d.ellipse((c + k * S * 0.12 - S * 0.04, c - S * 0.07, c + k * S * 0.12 + S * 0.04, c + S * 0.01), fill=col)
    elif kind == "route":
        d.polygon([(c - S * 0.22, c + S * 0.2), (c, c - S * 0.26), (c + S * 0.22, c + S * 0.2), (c, c + S * 0.08)], fill=w)
    elif kind == "pin":
        pin(d, c, c + S * 0.22, S * 0.16, w)
    return im.resize((s, s), Image.LANCZOS)


PHASES = [
    ("alert", RED, "Alamat tidak ditemukan", "Patokan: pintu biru dekat masjid"),
    ("chat", (245, 150, 30), "Kurir bertanya ke warga", "Warga nunjukin jalannya"),
    ("route", BLUE, "Kurir menuju lokasimu", "Lewat masjid, ketemu arahnya"),
    ("pin", RED, "Kurir di depan rumahmu", "Kiriman dari anaknya di Jakarta"),     # sets up the payoff
    ("check", GREEN, "Paket diterima", "Diterima oleh: Nenek"),
]


def status_card(img, t):
    k = max(i for i, p in enumerate(PH) if t >= p)
    kind, col, title, sub = PHASES[k]
    a = ease_out(lin(t, PH[k], PH[k] + 0.25)) if k else 1.0
    card = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    sh = Image.new("L", card.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((34, 26, W - 34, 186), 30, fill=90)
    card.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((30, 16, W - 30, 176), 30, fill=(255, 255, 255, 255))
    card.alpha_composite(check_icon(96) if kind == "check" else icon(kind, 96, col), (58, 48))
    d.text((180, 46), title, font=font("b", 44), fill=INK)
    d.text((180, 104), sub, font=font("m", 34), fill=GREY)
    paste_layer(img, card, W / 2, 800 + 26 * (1 - a), a)


def label(img, txt, x, y, fg, bgc):
    f = font("b", 30)
    L = Image.new("RGBA", (int(f.getlength(txt)) + 44, 54), (0, 0, 0, 0))
    ImageDraw.Draw(L).rounded_rectangle((0, 0, L.width - 1, 53), 27, fill=bgc)
    ImageDraw.Draw(L).text((22, 8), txt, font=f, fill=fg)
    img.alpha_composite(L, (x, y))


def part_pill(img, cx, cy, alpha=1.0, scale=1.0, size=34):
    f = font("xb", size)
    txt = "PART 2"
    L = Image.new("RGBA", (int(f.getlength(txt)) + 56, int(size * 1.9)), (0, 0, 0, 0))
    ImageDraw.Draw(L).rounded_rectangle((0, 0, L.width - 1, L.height - 1), L.height // 2, fill=RED + (255,))
    ImageDraw.Draw(L).text((28, int(size * 0.32)), txt, font=f, fill=(255, 255, 255))
    paste_layer(img, L, cx, cy, alpha, scale)


LOGO_S, LOGO_M = logo(170), logo(520)


def send_icon(size, col=(255, 255, 255)):
    """Instagram-style paper plane."""
    S = size * 4
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = int(S * 0.08)
    d.line([(S * 0.08, S * 0.12), (S * 0.92, S * 0.12), (S * 0.5, S * 0.9), (S * 0.4, S * 0.48), (S * 0.08, S * 0.12)],
           fill=col, width=w, joint="curve")
    d.line([(S * 0.4, S * 0.48), (S * 0.92, S * 0.12)], fill=col, width=w)
    return im.resize((size, size), Image.LANCZOS)


def heart(size, col=RED):
    S = size * 4
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ts = np.linspace(0, 2 * np.pi, 200)
    x = 16 * np.sin(ts) ** 3
    y = -(13 * np.cos(ts) - 5 * np.cos(2 * ts) - 2 * np.cos(3 * ts) - np.cos(4 * ts))
    k = S * 0.92 / 34
    ImageDraw.Draw(im).polygon([(S / 2 + xi * k, S * 0.47 + yi * k) for xi, yi in zip(x, y)], fill=col)
    return im.resize((size, size), Image.LANCZOS)


def header(img, t):
    if t < 3.0:                                        # the hook (dark version, once the app is in)
        a = 1 - ease_out(lin(t, 2.75, 3.0))
        part_pill(img, W / 2, 175, a)
        draw_text(img, "Alamatnya cuma", font("b", 50), W / 2, 248, INK, a, 1.0, shadow=0)
        draw_text(img, "“pintu biru dekat masjid”", font("xb", 62), W / 2, 318, RED, a, 1.0, shadow=0)
    elif t < 7.2:
        a = ease_out(lin(t, 3.0, 3.25))
        draw_text(img, "Lacak Paketmu", font("b", 50), 40, 225, INK, a, 1.0, shadow=0, anchor="l")
        draw_text(img, "Diantar hari ini · Resi H8KI", font("m", 32), 40, 290, GREY, a, 1.0, shadow=0, anchor="l")
        paste_layer(img, LOGO_S, W - 40, 255, a, 1.0, anchor="r")
    elif t < 11.4:                                     # punchline
        a1, s1, dy1 = pop(t, 7.35, 0.5, 11.4, 0.25)
        a2, s2, dy2 = pop(t, 7.95, 0.5, 11.4, 0.25)
        draw_text(img, "GPS-nya nyerah.", font("xb", 72), W / 2, 215 + dy1, INK, a1, s1, shadow=0)
        draw_text(img, "Kurirnya nggak.", font("xb", 80), W / 2, 307 + dy2, RED, a2, s2, shadow=0)
    else:                                              # the heart of it
        a1, s1, dy1 = pop(t, 11.55, 0.5)
        a2, s2, dy2 = pop(t, 12.1, 0.5)
        draw_text(img, "Isinya foto cucu", font("xb", 70), W / 2, 215 + dy1, INK, a1, s1, shadow=0)
        draw_text(img, "yang belum pernah ia peluk.", font("xb", 62), W / 2, 305 + dy2, GOLD, a2, s2, shadow=0)


def cta(img, t):
    """The asks on the map (its job is done once the parcel is in her hands); the faces below stay clear."""
    if t < 12.45:
        return
    k = ease_out(lin(t, 12.45, 12.75))
    veil = Image.new("RGBA", (MW, MH), (0, 0, 0, 0))
    ImageDraw.Draw(veil).rounded_rectangle((0, 0, MW - 1, MH - 1), 28, fill=BG + (int(205 * k),))
    img.alpha_composite(veil, (MX, MY))
    a, s, dy = pop(t, 12.6, 0.5)
    if a > 0:
        f = font("b", 40); txt = "Kirim ke yang lagi jauh dari keluarga"     # sends: the strongest signal for new reach
        tw = f.getlength(txt)
        L = Image.new("RGBA", (int(tw) + 150, 96), (0, 0, 0, 0))
        ImageDraw.Draw(L).rounded_rectangle((0, 0, L.width - 1, 95), 48, fill=INK + (215,))
        ImageDraw.Draw(L).text((40, 21), txt, font=f, fill=(255, 255, 255))
        nudge = 6 * max(0.0, math.sin(max(0, t - 13.0) * 6)) ** 6
        L.alpha_composite(send_icon(56), (int(tw) + 62 + int(nudge), 20 - int(nudge * 0.6)))
        paste_layer(img, L, W / 2, MY + 105 + dy, a, s)
    a, s, dy = pop(t, 13.15, 0.5)
    if a > 0:
        f = font("b", 40); txt = "Follow buat Part 3"
        tw = f.getlength(txt)
        L = Image.new("RGBA", (int(tw) + 90, 96), (0, 0, 0, 0))
        ImageDraw.Draw(L).rounded_rectangle((0, 0, L.width - 1, 95), 48, fill=GREEN + (255,))
        ImageDraw.Draw(L).text((45, 20), txt, font=f, fill=(255, 255, 255))
        paste_layer(img, L, W / 2, MY + 225 + dy, a, s * (1 + 0.02 * math.sin(max(0, t - 13.5) * 4.2)))


def app_panel(t):
    img = Image.new("RGBA", (W, PANEL), BG + (255,))
    header(img, t)
    m, mask = draw_map(t)
    img.paste(m, (MX, MY), mask)
    label(img, "DI APLIKASI", MX + 18, MY + 18, (255, 255, 255), INK + (230,))
    cta(img, t)
    status_card(img, t)
    return img


def end_card(t):
    img = Image.new("RGB", (W, H), (255, 255, 255))
    p = ease_out(lin(t, CARD_T, CARD_T + 0.3))
    paste_layer(img, LOGO_M, W / 2, 720, p, 0.92 + 0.08 * back_in_out(p, 1.2))
    a, s, dy = pop(t, CARD_T + 0.12, 0.4)
    draw_text(img, "Kurir yang", font("xb", 88), W / 2, 1040 + dy, INK, a, s, shadow=0.1, blur=10)
    a, s, dy = pop(t, CARD_T + 0.28, 0.4)
    draw_text(img, "nggak nyerah.", font("xb", 100), W / 2, 1150 + dy, RED, a, s, shadow=0.12, blur=10)
    return img


def hook_overlay(img, t, alpha):
    """Full-screen hook: big white text over the two faces, readable from frame 1."""
    s = 1.1 - 0.1 * ease_out(lin(t, 0, 0.2))
    part_pill(img, W / 2, 1130, alpha, s, size=40)
    draw_text(img, "Alamatnya cuma", font("b", 64), W / 2, 1232, (255, 255, 255), alpha, s, shadow=0.85, blur=12)
    draw_text(img, "“pintu biru", font("xb", 100), W / 2, 1335, (255, 255, 255), alpha, s, shadow=0.9, blur=14)
    draw_text(img, "dekat masjid”", font("xb", 100), W / 2, 1445, (255, 214, 120), alpha, s, shadow=0.9, blur=14)
    f = font("b", 38); txt = "GPS nyerah. Kurirnya bisa nemu?"
    L = Image.new("RGBA", (int(f.getlength(txt)) + 60, 72), (0, 0, 0, 0))
    ImageDraw.Draw(L).rounded_rectangle((0, 0, L.width - 1, 71), 36, fill=RED + (255,))
    ImageDraw.Draw(L).text((30, 13), txt, font=f, fill=(255, 255, 255))
    paste_layer(img, L, W / 2, 1545, alpha, s)


def frame(k):
    t = k / FPS
    if t >= END_T + TRANS:
        return np.asarray(end_card(t))
    if t < SPLIT_T:                                    # opening: full screen, then the app pushes in from the top
        p = ease_io(lin(t, FULL_END, SPLIT_T))
        top = int(round(PANEL * p))
        img = Image.new("RGBA", (W, H), BG + (255,))
        img.paste(Image.fromarray(footage(t, H - top, full=1 - p)), (0, top))
        if p > 0:
            img.alpha_composite(app_panel(t), (0, top - PANEL))
        else:                                          # a dark top scrim so the clip reads as cinema, not an app
            sc = np.linspace(0.45, 0, 300)[:, None] * 255
            img.alpha_composite(Image.fromarray(np.dstack([np.zeros((300, W, 3)), np.repeat(sc, W, 1)]).astype(np.uint8), "RGBA"), (0, 0))
        hook_overlay(img, t, 1 - ease_out(lin(t, FULL_END - 0.05, FULL_END + 0.2)))
        out = img.convert("RGB")
        if t < 0.6:                                    # the phone-buzz shake with the GPS error sound
            dx = 10 * math.sin(t * 2 * math.pi * 21) * math.exp(-t * 6)
            if abs(dx) > 0.3:
                out = Image.fromarray(cv2.warpAffine(np.asarray(out), np.float32([[1, 0, dx], [0, 1, 0]]), (W, H),
                                                     borderMode=cv2.BORDER_REPLICATE))
        return np.asarray(out)
    img = Image.new("RGBA", (W, H), BG + (255,))
    img.alpha_composite(app_panel(t), (0, 0))
    img.paste(Image.fromarray(footage(min(t, END_T - 1e-3), H - PANEL)), (0, PANEL))
    sh = np.linspace(0.35, 0, 26)[:, None] * 255
    img.alpha_composite(Image.fromarray(np.dstack([np.zeros((26, W, 3)), np.repeat(sh, W, 1)]).astype(np.uint8), "RGBA"), (0, PANEL))
    label(img, "KENYATAANNYA", 30, PANEL + 26, INK, (255, 255, 255, int(235 * ease_out(lin(t, SPLIT_T, SPLIT_T + 0.3)))))
    out = img.convert("RGB")
    if t >= END_T:
        p = ease_io(lin(t, END_T, END_T + TRANS))
        z = 1 + 0.04 * p
        out = out.resize((int(W * z), int(H * z)), Image.BICUBIC).crop(
            (int((W * z - W) / 2), int((H * z - H) / 2), int((W * z - W) / 2) + W, int((H * z - H) / 2) + H))
        if p > 0.01:
            out = out.filter(ImageFilter.GaussianBlur(14 * p))
        out = Image.blend(out, Image.new("RGB", (W, H), (255, 255, 255)), p)
    return np.asarray(out)


def frame_bytes(k):
    return frame(k).tobytes()


if __name__ == "__main__":
    out = sys.argv[1]
    if len(sys.argv) > 2:
        for tt in map(float, sys.argv[2:]):
            Image.fromarray(frame(int(round(tt * FPS)))).save(f"{out}_{tt:05.2f}.jpg", quality=90)
        sys.exit()
    n = int(round(DUR * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", "audio_r4.wav", "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-tune", "film",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", "-shortest", out + ".master.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for b in pool.imap(frame_bytes, range(n), chunksize=4):
            p.stdin.write(b)
    p.stdin.close(); p.wait()
    for ps in (1, 2):
        c = ["ffmpeg", "-v", "error", "-y", "-i", out + ".master.mp4", "-c:v", "libx264", "-preset", "veryslow",
             "-b:v", "8000k", "-maxrate", "10000k", "-bufsize", "16000k", "-pix_fmt", "yuv420p", "-pass", str(ps),
             "-passlogfile", out + ".p2"]
        c += (["-an", "-f", "mp4", "/dev/null"] if ps == 1 else ["-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out])
        subprocess.run(c, check=True)
    print("done", out)
