"""Scenes 1-2: cold GPS interface breaking down."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *
from gfx import *

MW, MH = 1400, 2300
RED = (236, 38, 52)
BLUE = (70, 140, 255)


def make_map():
    S = 2
    r = np.random.default_rng(3)
    im = Image.new("RGB", (MW * S, MH * S), (9, 13, 21))
    d = ImageDraw.Draw(im)
    # river
    pts = [(x * S, (1450 + 140 * math.sin(x / 210) + x * 0.25) * S) for x in range(-50, MW + 60, 20)]
    d.line(pts, fill=(12, 26, 46), width=70 * S)
    # grid roads
    xs = np.cumsum(r.uniform(150, 260, 12)) - 120
    ys = np.cumsum(r.uniform(140, 240, 16)) - 100
    # buildings inside blocks
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            x0, x1, y0, y1 = xs[i] + 14, xs[i + 1] - 14, ys[j] + 14, ys[j + 1] - 14
            for _ in range(r.integers(3, 8)):
                bw, bh = r.uniform(24, 70), r.uniform(24, 60)
                bx, by = r.uniform(x0, max(x0 + 1, x1 - bw)), r.uniform(y0, max(y0 + 1, y1 - bh))
                c = int(r.uniform(16, 24))
                d.rectangle((bx * S, by * S, (bx + bw) * S, (by + bh) * S), fill=(c, c + 5, c + 14))
    for k, x in enumerate(xs):
        sk = r.uniform(-40, 40)
        major = k % 4 == 1
        d.line([((x) * S, -20 * S), ((x + sk) * S, (MH + 20) * S)], fill=(36, 48, 74) if major else (24, 32, 50),
               width=(22 if major else 10) * S)
    for k, y in enumerate(ys):
        sk = r.uniform(-50, 50)
        major = k % 5 == 2
        d.line([(-20 * S, y * S), ((MW + 20) * S, (y + sk) * S)], fill=(36, 48, 74) if major else (24, 32, 50),
               width=(22 if major else 10) * S)
    # arterials
    d.line([(-50 * S, 300 * S), (MW * S, 1900 * S)], fill=(44, 58, 90), width=30 * S)
    d.line([(-50 * S, 300 * S), (MW * S, 1900 * S)], fill=(70, 86, 120), width=3 * S)
    d.line([(MW * S, 200 * S), (100 * S, MH * S)], fill=(40, 54, 84), width=24 * S)
    # small alleys (gang) that dead-end
    for _ in range(40):
        x, y = r.uniform(0, MW), r.uniform(0, MH)
        L = r.uniform(40, 110)
        if r.random() < 0.5:
            d.line([(x * S, y * S), ((x + L) * S, y * S)], fill=(20, 27, 42), width=5 * S)
        else:
            d.line([(x * S, y * S), (x * S, (y + L) * S)], fill=(20, 27, 42), width=5 * S)
    f = font("m", 40)
    names = ["Jl. Melati", "Gg. Kenanga", "Jl. Mawar Raya", "Gg. Sawo", "Jl. Anggrek", "Gg. Buntu",
             "Jl. Cempaka", "Gg. Mangga", "Jl. Flamboyan"]
    for i, n in enumerate(names):
        d.text((r.uniform(40, MW - 300) * S, r.uniform(80, MH - 80) * S), n, font=f, fill=(58, 72, 100))
    return im.resize((MW, MH), Image.LANCZOS)


MAP = np.asarray(make_map(), dtype=np.float32)

# gradients for UI legibility
_g = np.zeros((H, 1), np.float32)
for y in range(H):
    top = clamp(1 - (y - 120) / 520) * 0.88
    bot = clamp((y - 1180) / 380) * 0.8
    _g[y] = max(top, bot)
UI_SHADE = _g[..., None]

X_SMALL = x_icon(30)


def map_frame(t, warp=0.0, seed=0):
    # slow drift, keeps the map alive
    ox = int(160 + 60 * math.sin(t * 0.35))
    oy = int(150 + 25 * t)
    m = MAP[oy:oy + H, ox:ox + W]
    if warp > 0.01:
        r = np.random.default_rng(seed)
        rows = np.arange(H)
        shift = (warp * 38 * np.sin(rows / 55.0 + t * 30)).astype(int)
        # random slice tears
        for _ in range(int(3 + warp * 10)):
            y0 = r.integers(0, H - 40)
            hgt = r.integers(8, 90)
            shift[y0:y0 + hgt] += int(r.uniform(-120, 120) * warp)
        cols = (np.arange(W)[None, :] + shift[:, None]) % W
        m = m[rows[:, None], cols]
    return m.copy()


def rgb_split(arr, amt):
    if amt < 1:
        return arr
    a = int(amt)
    out = arr.copy()
    out[:, a:, 0] = arr[:, :-a, 0]
    out[:, :-a, 2] = arr[:, a:, 2]
    return out


def ui_state(t):
    """Which query, how much typed, whether in error."""
    cur = None
    for i, q in enumerate(QW):
        if t >= q["start"]:
            cur = i
    return cur


def error_amount(t):
    """Decaying impulse after each error; drives shake/warp/flash."""
    v = 0.0
    for q in QW:
        if t >= q["err"]:
            v = max(v, math.exp(-(t - q["err"]) / 0.18))
    return v


def scene1(t, glitch=0.0, overlay_final=False):
    ei = error_amount(t) if not overlay_final else 0.6
    seed = int(t * FPS)
    arr = map_frame(t, warp=max(ei * 0.8, glitch), seed=seed)
    arr = arr * (1 - UI_SHADE) + UI_SHADE * np.array([6, 8, 14], np.float32)
    img = to_img(arr)
    d = ImageDraw.Draw(img, "RGBA")
    i = ui_state(t)
    q = QW[i] if i is not None else QW[0]
    in_err = i is not None and t >= q["err"]
    found_fail = sum(1 for qq in QW if t >= qq["err"])

    # location dot + radar
    cx, cy = 540, 800
    if i is not None and q["type_end"] <= t < q["err"]:
        p = (t - q["type_end"]) / (q["err"] - q["type_end"])
        for k in range(2):
            pp = (p + k * 0.5) % 1
            rr = 40 + pp * 360
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=BLUE + (int(160 * (1 - pp)),), width=4)
    pulse = 0.5 + 0.5 * math.sin(t * 6)
    d.ellipse((cx - 80, cy - 80, cx + 80, cy + 80), fill=BLUE + (int(30 + 20 * pulse),))
    d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=(255, 255, 255, 255))
    d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=BLUE + (255,))

    # failed pins scattered on the map
    for k, qq in enumerate(QW):
        if t >= qq["err"]:
            px, py = [(300, 640), (760, 700), (380, 960), (820, 1000), (560, 590)][k]
            drop = ease_out((t - qq["err"]) / 0.25)
            py2 = py - 60 * (1 - drop)
            d.ellipse((px - 26, py2 - 70, px + 26, py2 - 18), fill=RED + (230,))
            d.polygon([(px - 18, py2 - 36), (px + 18, py2 - 36), (px, py2)], fill=RED + (230,))
            d.text((px, py2 - 44), "?", font=font("xb", 34), fill=(255, 255, 255), anchor="mm")

    # header
    d.ellipse((62, 162, 118, 218), outline=BLUE, width=5)
    d.ellipse((84, 184, 96, 196), fill=BLUE)
    for a in range(4):
        ang = a * math.pi / 2
        d.line([(90 + 26 * math.cos(ang), 190 + 26 * math.sin(ang)), (90 + 38 * math.cos(ang), 190 + 38 * math.sin(ang))],
               fill=BLUE, width=5)
    d.text((140, 190), "Sistem Pencarian Alamat", font=font("sb", 44), fill=(232, 238, 248), anchor="lm")
    d.text((142, 244), "GPS NAV  •  MODE PRESISI", font=font("mono", 24), fill=(100, 118, 150), anchor="lm")
    # status chip
    chip_col = RED if found_fail else (60, 76, 104)
    txt = f"{found_fail}/5 GAGAL"
    tw = d.textlength(txt, font=font("mono", 26))
    rrect(d, (1020 - tw - 40, 300 - 70 - 24, 1020, 300 - 70 + 24), 24, fill=chip_col + (60,), outline=chip_col + (255,), width=2)
    d.text((1020 - 20, 230), txt, font=font("mono", 26), fill=chip_col if found_fail else (150, 165, 190), anchor="rm")

    # search bar
    bar_col = RED if in_err else (48, 64, 98)
    rrect(d, (54, 300, 1026, 420), 30, fill=(18, 25, 40, 245), outline=bar_col + (255,), width=4 if in_err else 3)
    d.ellipse((90, 338, 124, 372), outline=(140, 160, 195), width=5)
    d.line([(120, 368), (136, 384)], fill=(140, 160, 195), width=6)
    if i is not None:
        n = len(q["text"])
        k = int(n * lin(t, q["start"], q["type_end"]))
        txt = q["text"][:k]
        f = font("mono", 33)
        col = (255, 120, 128) if in_err else (235, 240, 250)
        d.text((158, 360), txt, font=f, fill=col, anchor="lm")
        if not in_err and (int(t * 4) % 2 == 0 or t < q["type_end"]):
            cxx = 158 + d.textlength(txt, font=f) + 4
            d.rectangle((cxx, 338, cxx + 16, 382), fill=(120, 170, 255))
        if q["type_end"] <= t < q["err"]:
            dots = "." * (1 + int(t * 10) % 3)
            d.text((70, 455), "Mencari alamat" + dots, font=font("mono", 26), fill=(120, 170, 255), anchor="lm")
    else:
        d.text((158, 360), "Cari alamat tujuan...", font=font("mono", 33), fill=(90, 105, 135), anchor="lm")

    # log
    d.text((70, 1180), "RIWAYAT PENCARIAN", font=font("mono", 24), fill=(100, 118, 150), anchor="lm")
    d.line([(70, 1208), (1010, 1208)], fill=(40, 52, 78), width=2)
    row = 0
    for qq in QW:
        if t >= qq["err"]:
            y = 1244 + row * 57
            a = lin(t, qq["err"], qq["err"] + 0.12)
            img.paste(X_SMALL.convert("RGB"), (70, y - 15), X_SMALL.getchannel("A").point(lambda v: int(v * a)))
            tx = qq["text"] if len(qq["text"]) <= 30 else qq["text"][:29] + "…"
            d.text((116, y), tx, font=font("mono", 26), fill=(170, 182, 205, int(255 * a)), anchor="lm")
            d.text((1010, y), "GAGAL", font=font("mono", 24), fill=RED + (int(255 * a),), anchor="rm")
            row += 1

    # error banner
    if in_err and not overlay_final:
        p = t - q["err"]
        s = 0.55 + 0.45 * back_out(p / 0.16)
        ban = banner()
        paste_layer(img, ban, 540, 1050, 1.0, s)

    arr = to_arr(img)
    # red flash vignette
    if ei > 0.01:
        red = np.array([200, 10, 25], np.float32)
        m = (1 - VIG_SOFT) * 2.2 * ei * 0.9 + 0.12 * ei
        arr = arr * (1 - m) + red * m
        arr = rgb_split(arr, ei * 14)
    return arr


_ban = None


def banner():
    global _ban
    if _ban is None:
        S = 2
        w, h = 900, 150
        im = Image.new("RGBA", ((w + 80) * S, (h + 80) * S), (0, 0, 0, 0))
        g = Image.new("L", im.size, 0)
        ImageDraw.Draw(g).rounded_rectangle((40 * S, 40 * S, (40 + w) * S, (40 + h) * S), 28 * S, fill=200)
        g = g.filter(ImageFilter.GaussianBlur(22 * S))
        glow = Image.new("RGBA", im.size, (255, 30, 50, 0))
        glow.putalpha(g)
        im = Image.alpha_composite(im, glow)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((40 * S, 40 * S, (40 + w) * S, (40 + h) * S), 28 * S, fill=(228, 28, 44))
        # warning triangle
        tx, ty = (40 + 80) * S, (40 + h / 2) * S
        d.polygon([(tx, ty - 42 * S), (tx + 46 * S, ty + 36 * S), (tx - 46 * S, ty + 36 * S)], fill=(255, 255, 255))
        d.text((tx, ty + 8 * S), "!", font=font("xb", 56 * S), fill=(228, 28, 44), anchor="mm")
        d.text(((40 + 150) * S, (40 + h / 2) * S), "ALAMAT TIDAK DITEMUKAN", font=font("xb", 50 * S),
               fill=(255, 255, 255), anchor="lm")
        _ban = im.resize((w + 80, h + 80), Image.LANCZOS)
    return _ban


def glitch_blocks(arr, amt, seed):
    r = np.random.default_rng(seed)
    for _ in range(int(amt * 26)):
        y0 = r.integers(0, H - 60)
        h = r.integers(6, 120)
        sh = int(r.uniform(-260, 260) * amt)
        arr[y0:y0 + h] = np.roll(arr[y0:y0 + h], sh, axis=1)
        if r.random() < 0.25:
            x0 = r.integers(0, W - 200)
            arr[y0:y0 + h, x0:x0 + r.integers(40, 400)] = np.array(
                [[r.choice([255, 30]), r.choice([40, 255, 20]), r.choice([60, 255])]], np.float32)
    return arr


def scene2(t):
    if t < GLITCH_END:
        p = lin(t, S1_END, GLITCH_END)
        amt = 0.35 + 0.65 * p
        arr = scene1(S1_END - 0.01, glitch=amt * 0.8, overlay_final=True)
        arr *= (1 - 0.55 * ease_io(p * 2))
        arr = glitch_blocks(arr, amt, int(t * 100))
        arr = rgb_split(arr, 6 + 26 * amt * abs(math.sin(t * 43)))
        img = to_img(arr)
        # the verdict stays legible on top of the breakdown
        jit = np.random.default_rng(int(t * 60)).uniform(-1, 1, 2) * 8 * amt
        draw_text(img, "5 dari 5 alamat", font("b", 76), 540 + jit[0], 880 + jit[1], (255, 255, 255), blur=14)
        draw_text(img, "TIDAK DITEMUKAN", font("xb", 104), 540 - jit[1], 1000 + jit[0], (255, 50, 62), blur=18,
                  glow=(255, 0, 30))
        arr = to_arr(img)
        if int(t * 30) % 5 == 0:
            arr = rgb_split(arr, 10)
        return arr
    if t < CRT_END:
        # CRT power-off: squash to a line, then to a dot
        base = to_img(scene2(GLITCH_END - 0.001))
        p = lin(t, GLITCH_END, CRT_END)
        out = np.zeros((H, W, 3), np.float32)
        if p < 0.55:
            q = ease_in(p / 0.55)
            hh = max(4, int(H * (1 - q)))
            im = base.resize((W, hh), Image.BILINEAR)
            a = to_arr(im) * (1 + 2.5 * q) + 120 * q
            y0 = (H - hh) // 2
            out[y0:y0 + hh] = a
        else:
            q = ease_in((p - 0.55) / 0.45)
            ww = max(6, int(W * (1 - q)))
            out[H // 2 - 3:H // 2 + 3, (W - ww) // 2:(W + ww) // 2] = 255
            glow_add(out, W / 2, H / 2, 40 + 200 * (1 - q), (180, 200, 255), 0.6 * (1 - q * 0.7), squash=0.15)
        return out
    arr = np.zeros((H, W, 3), np.float32)
    # "GPS menyerah." types out slowly in the silence
    k = int(max(0, t - TYPE_GPS_START) * TYPE_GPS_CPS)
    txt = GPS_TEXT[:min(k, len(GPS_TEXT))]
    img = to_img(arr)
    f = font("sb", 78)
    full_w = text_size(GPS_TEXT, f)[0]
    x0 = 540 - full_w / 2
    d = ImageDraw.Draw(img)
    d.text((x0, 960), txt, font=f, fill=(245, 245, 245), anchor="lm")
    if (int(t * 2.4) % 2 == 0) or (0 < k < len(GPS_TEXT)):
        cx = x0 + d.textlength(txt, font=f) + 8
        d.rectangle((cx, 918, cx + 10, 1004), fill=(245, 245, 245))
    return to_arr(img)


def hook(t):
    """0.5 s cold open: full-size red error, provocation first."""
    arr = np.zeros((H, W, 3), np.float32) + np.array([222, 24, 40], np.float32)
    glow_add(arr, 540, 880, 700, (60, 10, 10), 0.8)
    arr *= VIG_SOFT
    img = to_img(arr)
    r = np.random.default_rng(int(t * 60) + 5)
    shake = math.exp(-t / 0.12) * 26 + (18 if t > HOOK - 0.12 else 0)
    jx, jy = r.uniform(-1, 1, 2) * shake
    s = 1.0 + 0.10 * math.exp(-t / 0.06)
    d = ImageDraw.Draw(img)
    tx, ty = 540 + jx, 520 + jy
    k = 150 * s
    d.polygon([(tx, ty - k * 0.9), (tx + k, ty + k * 0.8), (tx - k, ty + k * 0.8)], fill=(255, 255, 255))
    d.text((tx, ty + k * 0.22), "!", font=font("xb", int(190 * s)), fill=(222, 24, 40), anchor="mm")
    for txt, y, sz in [("ALAMAT", 900, 190), ("TIDAK", 1090, 190), ("DITEMUKAN", 1270, 150)]:
        draw_text(img, txt, font("xb", sz), 540 + jx, y + jy, (255, 255, 255), 1.0, s, shadow=0.35, blur=18)
    d = ImageDraw.Draw(img)
    rrect(d, (130 + jx, 1380 + jy, 950 + jx, 1466 + jy), 43, fill=(120, 8, 20))
    d.text((540 + jx, 1423 + jy), "Rumah cat hijau, sebelah warung Bu Ani", font=font("mono", 30),
           fill=(255, 205, 205), anchor="mm")
    arr = to_arr(img)
    arr = rgb_split(arr, 4 + 10 * math.exp(-t / 0.05))
    if t > HOOK - 0.12:  # glitch cut into the sequence
        arr = glitch_blocks(arr, 0.9, int(t * 100))
        arr = rgb_split(arr, 24)
    return arr
