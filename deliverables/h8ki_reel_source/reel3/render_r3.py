"""Reel #3 "Di aplikasi vs Kenyataannya": the courier-tracking dot that sits still for 10 minutes (top), and what
the courier is really doing at that moment (bottom). Reply-with-reel to @heyyyy_dump's comment on Reel #1:
"Ga relate, saya mah tim nonton tracking kurir aja".
Every cut sits on the 100 bpm grid of the score (beat = 0.6 s).
  python3 render_r3.py OUT.mp4 [preview t ...]"""
import sys, math, subprocess
from functools import lru_cache
from multiprocessing import Pool
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
from gfx import font, text_layer, paste_layer, draw_text, check_icon, pop, back_in_out
from common import clamp, lin, ease_io, ease_out
import interp

W, H, FPS = 1080, 1920, 24
DUR = 15.6
PANEL = 900                                  # top: the app; bottom: the reality
INK, GREY, LINE = (24, 28, 40), (104, 112, 124), (226, 229, 235)
RED, GREEN, BLUE, BG = (227, 24, 30), (4, 152, 68), (24, 119, 242), (244, 245, 248)
END_T = 13.2

# (t0, t1, clip, first src frame, last src frame, crop centre x, crop centre y, crop width)
SHOTS = [
    (0.0, 2.4, "d2", 106, 121, 560, 830, 720),    # dead end: face fully visible, looks around, worried (slow motion)
    (2.4, 4.8, "a2", 236, 290, 540, 860, 1080),   # an ibu peeks out and points the way
    (4.8, 5.8, "a2", 290, 313, 560, 820, 900),    # he walks on, smiling
    (5.8, 7.2, "a2", 80, 110, 590, 820, 780),     # under the trees, almost there
    (7.2, 9.6, "b2", 64, 120, 540, 860, 1080),    # the gate opens, warm light
    (9.6, END_T, "h", 41, 121, 540, 900, 1080),   # handover, both smiling
]
PH = [0.0, 2.4, 4.8, 7.2, 9.6]                # status phases follow the cuts


@lru_cache(maxsize=6)
def raw(clip, i):
    return np.asarray(Image.open(f"../fr/{clip}/f{i:04d}.png").convert("RGB"))


def src(clip, p):
    i0 = int(math.floor(p)); s = p - i0
    a = raw(clip, i0)
    return interp.between(a, raw(clip, i0 + 1), s) if s > 0.04 else a


def footage(t):
    for (t0, t1, c, fa, fb, cx, cy, cw) in SHOTS:
        if t0 <= t < t1:
            u = (t - t0) / (t1 - t0)
            a = src(c, fa + u * (fb - fa))
            z = 1 + 0.045 * u                        # slow push-in on every shot
            w = cw / z; h = w * (H - PANEL) / W
            x0 = clamp(cx - w / 2, 0, a.shape[1] - w); y0 = clamp(cy - h / 2, 0, a.shape[0] - h)
            M = np.float32([[W / w, 0, -x0 * W / w], [0, (H - PANEL) / h, -y0 * (H - PANEL) / h]])
            return cv2.warpAffine(a, M, (W, H - PANEL), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return None


# ------------------------------------------------------------------ the app (top panel)
MX, MY, MW, MH = 30, 335, 1020, 365          # map box on screen
S2 = 2                                        # map supersampling
DEAD, J, TURN, HOUSE = (290, 62), (290, 200), (780, 200), (780, 86)
PATH = [DEAD, J, TURN, HOUSE]


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
    w, h = MW * S2, MH * S2
    m = Image.new("RGB", (w, h), (236, 238, 232))
    d = ImageDraw.Draw(m)
    q = lambda x: x * S2
    rng = np.random.default_rng(7)
    for _ in range(46):                              # house blocks
        x, y = rng.uniform(0, MW), rng.uniform(0, MH)
        bw, bh = rng.uniform(40, 110), rng.uniform(30, 70)
        d.rounded_rectangle((q(x), q(y), q(x + bw), q(y + bh)), q(6), fill=(224, 226, 220))
    d.rounded_rectangle((q(560), q(232), q(720), q(300)), q(18), fill=(205, 232, 200))     # little park
    # alleys: white with a soft edge
    for (a, b, wd) in [((0, 200), (MW, 200), 30), ((290, 200), (290, 50), 24), ((780, 200), (780, 70), 24),
                       ((520, 200), (520, MH), 24), ((120, 200), (120, MH), 24), ((0, 325), (MW, 325), 38)]:
        d.line([(q(a[0]), q(a[1])), (q(b[0]), q(b[1]))], fill=(214, 216, 212), width=q(wd + 6))
    for (a, b, wd) in [((0, 200), (MW, 200), 30), ((290, 200), (290, 50), 24), ((780, 200), (780, 70), 24),
                       ((520, 200), (520, MH), 24), ((120, 200), (120, MH), 24), ((0, 325), (MW, 325), 38)]:
        d.line([(q(a[0]), q(a[1])), (q(b[0]), q(b[1]))], fill=(255, 255, 255), width=q(wd))
    d.line([(q(270), q(48)), (q(310), q(48))], fill=(150, 150, 150), width=q(6))        # dead-end wall
    # landmarks: mosque, mango tree, warung
    mx, my = 520, 120
    d.rectangle((q(mx - 34), q(my), q(mx + 34), q(my + 34)), fill=(196, 214, 204))
    d.ellipse((q(mx - 24), q(my - 26), q(mx + 24), q(my + 18)), fill=(150, 196, 170))
    d.rectangle((q(mx + 40), q(my - 30), q(mx + 48), q(my + 34)), fill=(150, 196, 170))
    d.ellipse((q(640 - 22), q(255 - 22), q(640 + 22), q(255 + 22)), fill=(120, 184, 110))
    d.rounded_rectangle((q(400), q(240), q(450), q(278)), q(6), fill=(252, 196, 120))
    f = font("m", 22 * S2)
    for txt, x, y in [("Masjid", mx, my + 58), ("Warung", 425, 296), ("Jl. Raya", 900, 325)]:
        tw = f.getlength(txt)
        d.text((q(x) - tw / 2, q(y) - 14 * S2), txt, font=f, fill=(128, 134, 140))
    # planned route (dashed): junction -> house
    pts = [J, TURN, HOUSE]
    for (a, b) in zip(pts, pts[1:]):
        L = math.dist(a, b); n = int(L / 22)
        for k in range(n):
            u0, u1 = k / n, (k + 0.55) / n
            d.line([(q(a[0] + (b[0] - a[0]) * u0), q(a[1] + (b[1] - a[1]) * u0)),
                    (q(a[0] + (b[0] - a[0]) * u1), q(a[1] + (b[1] - a[1]) * u1))], fill=(140, 186, 250), width=q(9))
    return m


def path_point(s):
    """Point at arc length fraction s (0..1) of PATH, and the travelled polyline."""
    segs = [math.dist(a, b) for a, b in zip(PATH, PATH[1:])]
    tot = sum(segs); dist = s * tot; trail = [PATH[0]]
    for (a, b), L in zip(zip(PATH, PATH[1:]), segs):
        if dist <= L:
            u = dist / L
            p = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
            return p, trail + [p]
        dist -= L; trail.append(b)
    return PATH[-1], trail


def dot_state(t):
    segs = [math.dist(a, b) for a, b in zip(PATH, PATH[1:])]
    f1 = segs[0] / sum(segs)
    if t < 3.9:
        s = 0.0
    elif t < 4.8:
        s = f1 * ease_io(lin(t, 3.9, 4.8))
    elif t < 7.0:
        s = f1 + (1 - f1) * ease_io(lin(t, 4.8, 7.0))
    else:
        s = 1.0
    return path_point(s)


def draw_map(t):
    m = map_base().copy()
    d = ImageDraw.Draw(m, "RGBA")
    q = lambda x: x * S2
    (px, py), trail = dot_state(t)
    if len(trail) > 1:
        d.line([(q(x), q(y)) for x, y in trail], fill=BLUE + (255,), width=q(9), joint="curve")
    # house pin, bounces on arrival
    b = 0
    if 7.0 <= t < 7.6:
        b = 16 * math.sin(math.pi * (t - 7.0) / 0.6) * math.exp(-(t - 7.0) * 3)
    hx, hy = HOUSE[0], HOUSE[1] - 14 - b
    pin(d, q(hx), q(hy), q(20), RED + (255,))
    d.rectangle((q(hx - 8), q(hy - 30), q(hx + 8), q(hy - 18)), fill=(255, 255, 255, 255))
    d.polygon([(q(hx - 12), q(hy - 29)), (q(hx + 12), q(hy - 29)), (q(hx), q(hy - 40))], fill=(255, 255, 255, 255))
    # the courier dot (with a searching wiggle while stuck)
    if t < 3.9:
        px += 3 * math.sin(t * 7.3); py += 2 * math.sin(t * 5.1 + 1)
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
    w = (255, 255, 255)
    c = S / 2
    if kind == "clock":
        d.ellipse((c - S * 0.27, c - S * 0.27, c + S * 0.27, c + S * 0.27), outline=w, width=int(S * 0.07))
        d.line([(c, c), (c, c - S * 0.17)], fill=w, width=int(S * 0.07))
        d.line([(c, c), (c + S * 0.13, c + 0.04 * S)], fill=w, width=int(S * 0.07))
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
    ("clock", RED, "Kurir berhenti", "Titiknya nggak gerak sama sekali"),
    ("chat", (245, 150, 30), "Kurir bertanya ke warga", "Alamatnya cuma pakai patokan"),
    ("route", BLUE, "Kurir menuju lokasimu", "Ketemu jalannya, gas lagi"),
    ("pin", RED, "Kurir di depan rumahmu", "Siap-siap buka pintu ya"),
    ("check", GREEN, "Paket diterima", "18.52 · H8KI Logistik Lionindo"),
]


def status_card(img, t):
    k = max(i for i, p in enumerate(PH) if t >= p)
    kind, col, title, sub = PHASES[k]
    a = ease_out(lin(t, PH[k], PH[k] + 0.25)) if k else 1.0
    dy = 26 * (1 - a)
    card = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    sh = Image.new("L", card.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((34, 26, W - 34, 186), 30, fill=90)
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    card.paste((0, 0, 0, 255), (0, 0), sh)
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((30, 16, W - 30, 176), 30, fill=(255, 255, 255, 255))
    ic = check_icon(96) if kind == "check" else icon(kind, 96, col)
    card.alpha_composite(ic, (58, 48))
    d.text((180, 46), title, font=font("b", 44), fill=INK)
    d.text((180, 108), sub, font=font("m", 30), fill=GREY)
    if k == 0:                                         # the stuck timer, ticking up to 10:00
        secs = 597 + min(3, int(t / 0.6))
        tm = f"{secs // 60:02d}:{secs % 60:02d}"
        tw = font("b", 46).getlength(tm)
        d.text((W - 70 - tw, 62), tm, font=font("b", 46), fill=RED)
    paste_layer(img, card, W / 2, 700 + 100 + dy, a)


def header(img, t):
    d = ImageDraw.Draw(img)
    if t < 2.4:                                        # the hook, readable from frame 1
        a = 1 - ease_out(lin(t, 2.15, 2.4))
        s = 0.96 + 0.04 * ease_out(lin(t, 0, 0.25))
        draw_text(img, "Titik kurir diem", font("xb", 80), W / 2, 188, INK, a, s, shadow=0)
        draw_text(img, "10 menit?", font("xb", 92), W / 2, 280, RED, a, s, shadow=0)
    elif t < 9.6:
        a = ease_out(lin(t, 2.4, 2.65))
        draw_text(img, "Lacak Paketmu", font("b", 50), 40, 200, INK, a, 1.0, shadow=0, anchor="l")
        draw_text(img, "Diantar hari ini · Resi H8KI", font("m", 30), 40, 262, GREY, a, 1.0, shadow=0, anchor="l")
        paste_layer(img, LOGO_S, W - 40, 228, a, 1.0, anchor="r")
    else:                                              # the punchline
        a1, s1, dy1 = pop(t, 9.75, 0.5)
        a2, s2, dy2 = pop(t, 10.35, 0.5)
        draw_text(img, "Titiknya diem.", font("xb", 72), W / 2, 188 + dy1, INK, a1, s1, shadow=0)
        draw_text(img, "Kurirnya nggak nyerah.", font("xb", 72), W / 2, 280 + dy2, RED, a2, s2, shadow=0)


def label(img, txt, x, y, fg, bgc):
    f = font("b", 30)
    tw = f.getlength(txt)
    L = Image.new("RGBA", (int(tw) + 44, 54), (0, 0, 0, 0))
    ImageDraw.Draw(L).rounded_rectangle((0, 0, L.width - 1, 53), 27, fill=bgc)
    ImageDraw.Draw(L).text((22, 8), txt, font=f, fill=fg)
    img.alpha_composite(L, (x, y))


LOGO_S = logo(170)
LOGO_L = logo(600)
LOGO_M = logo(520)


def heart(size, col=RED):
    S = size * 4
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ts = np.linspace(0, 2 * np.pi, 200)
    x = 16 * np.sin(ts) ** 3
    y = -(13 * np.cos(ts) - 5 * np.cos(2 * ts) - 2 * np.cos(3 * ts) - np.cos(4 * ts))
    k = S * 0.92 / 34
    pts = [(S / 2 + xi * k, S * 0.47 + yi * k) for xi, yi in zip(x, y)]
    ImageDraw.Draw(im).polygon(pts, fill=col)
    return im.resize((size, size), Image.LANCZOS)


def end_card(t):
    img = Image.new("RGB", (W, H), (255, 255, 255))
    p = ease_out(lin(t, END_T + 0.05, END_T + 0.45))
    paste_layer(img, LOGO_M, W / 2, 610, p, 0.92 + 0.08 * back_in_out(p, 1.2))
    a, s, dy = pop(t, END_T + 0.3, 0.5)
    draw_text(img, "Kurir yang", font("xb", 88), W / 2, 930 + dy, INK, a, s, shadow=0.1, blur=10)
    a, s, dy = pop(t, END_T + 0.5, 0.5)
    draw_text(img, "nggak nyerah.", font("xb", 100), W / 2, 1040 + dy, RED, a, s, shadow=0.12, blur=10)
    a, s, dy = pop(t, END_T + 0.8, 0.5)                 # ask for the like
    if a > 0:
        f = font("b", 42); txt = "Tim nonton tracking? Tap"
        tw = f.getlength(txt)
        L = Image.new("RGBA", (int(tw) + 80, 80), (0, 0, 0, 0))
        ImageDraw.Draw(L).text((0, 10), txt, font=f, fill=INK)
        beat = 1 + 0.12 * max(0.0, math.sin(max(0, t - END_T - 1.1) * 7)) ** 8
        hz_ = heart(int(62 * beat))
        L.alpha_composite(hz_, (int(tw) + 14 + (62 - hz_.width) // 2, 8 + (62 - hz_.height) // 2))
        paste_layer(img, L, W / 2, 1215 + dy, a, s)
    a, s, dy = pop(t, END_T + 1.1, 0.5)                 # and the follow
    if a > 0:
        f = font("b", 40); txt = "Follow buat cerita kurir berikutnya"
        tw = f.getlength(txt)
        L = Image.new("RGBA", (int(tw) + 90, 96), (0, 0, 0, 0))
        ImageDraw.Draw(L).rounded_rectangle((0, 0, L.width - 1, 95), 48, fill=GREEN + (255,))
        ImageDraw.Draw(L).text((45, 20), txt, font=f, fill=(255, 255, 255))
        breathe = 1 + 0.02 * math.sin(max(0, t - END_T - 1.5) * 4.2)
        paste_layer(img, L, W / 2, 1370 + dy, a, s * breathe)
    return img


def frame(k):
    t = k / FPS
    if t >= END_T + 0.25:
        return np.asarray(end_card(t))
    img = Image.new("RGBA", (W, H), BG + (255,))
    header(img, t)
    m, mask = draw_map(t)
    img.paste(m, (MX, MY), mask)
    label(img, "DI APLIKASI", MX + 18, MY + 18, (255, 255, 255), INK + (230,))
    status_card(img, t)
    fo = footage(min(t, END_T - 1e-3))
    img.paste(Image.fromarray(fo), (0, PANEL))
    sh = np.linspace(0.35, 0, 26)[:, None] * 255                       # soft shadow under the app panel
    img.alpha_composite(Image.fromarray(np.dstack([np.zeros((26, W, 3)), np.repeat(sh, W, 1)]).astype(np.uint8), "RGBA"),
                        (0, PANEL))
    label(img, "KENYATAANNYA", 30, PANEL + 26, INK, (255, 255, 255, 235))
    out = img.convert("RGB")
    if t >= END_T:                                     # quick white wipe into the end card
        p = ease_io(lin(t, END_T, END_T + 0.25))
        out = Image.blend(out, end_card(t), p)
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
           "-i", "-", "-i", "audio_r3.wav", "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-tune", "film",
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
