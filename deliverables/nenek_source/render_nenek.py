"""'Kiriman untuk Nenek' final cut: python3 render_nenek.py OUT.mp4 [preview times...]"""
import sys, math, subprocess
from functools import lru_cache
from multiprocessing import Pool
import numpy as np, cv2, imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter
from gfx import (font, text_size, draw_text, paste_layer, pop, check_icon, back_in_out, to_img, rrect)
from common import clamp, lin, ease_io, ease_out, ease_in
from nk_time import *
import label3, interp

W, H = 1080, 1920
GOLD = (255, 198, 96)
RED = (255, 56, 64)


# ------------------------------------------------------------------ footage
@lru_cache(maxsize=8)
def raw(clip, i):
    return np.asarray(Image.open(f"../{clip}/f{i:04d}.png").convert("RGB"))


def src_frame(clip, p):
    i0 = int(math.floor(p))
    s = p - i0
    a = raw(clip, i0)
    if s > 0.02:
        a = interp.between(a, raw(clip, i0 + 1), s)
    if clip == "k1" and 144 <= p <= 215:
        a = label3.apply(a, p)
    return a


# warm golden-hour grade: shots 2, 4, 5 and clip 2 were overcast, so they get the full push;
# the two golden shots only a touch, so the whole film reads as one late afternoon
WARM = [0.3, 1.0, 0.3, 1.0, 1.0, 1.0, 1.0]


def grade(a, s):
    x = (a.astype(np.float32) / 255.0)
    full = x ** 0.95 * np.array([1.10, 1.02, 0.82], np.float32)
    small = cv2.resize(full, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    glow = cv2.resize(cv2.GaussianBlur(small, (0, 0), 8), (W, H), interpolation=cv2.INTER_LINEAR)
    full = full * 0.65 + np.maximum(full, glow) * 0.35
    out = x * (1 - s) + full * s
    # gentle S-curve + vignette for a filmic finish on every shot
    out = np.clip(out, 0, 1)
    out = out + 0.06 * (out - 0.5) * (1 - np.abs(2 * out - 1))
    return out * VIG * 255


yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.28 * np.clip(np.sqrt(((xx - 540) / 620) ** 2 + ((yy - 960) / 1100) ** 2), 0, 1.4) ** 2.2)[..., None]
SCRIM_LOW = np.clip((yy - 1000) / 700, 0, 1)[..., None] ** 1.3
WHITE_BG = (255 - 12 * np.clip(np.sqrt(((xx - 540) / 900.0) ** 2 + ((yy - 900) / 1300.0) ** 2), 0, 1) ** 2)[..., None].repeat(3, 2)


def footage(k):
    clip, p, si = SRC[min(k, len(SRC) - 1)]
    a = cv2.resize(src_frame(clip, p), (W, H), interpolation=cv2.INTER_CUBIC)
    return grade(a, WARM[si])


# ------------------------------------------------------------------ graphics
_cache = {}


def notif_card():
    if "notif" not in _cache:
        w, h, k = 880, 170, 2
        im = Image.new("RGBA", ((w + 80) * k, (h + 80) * k), (0, 0, 0, 0))
        sh = Image.new("L", im.size, 0)
        ImageDraw.Draw(sh).rounded_rectangle((40 * k, 54 * k, (40 + w) * k, (54 + h) * k), 44 * k, fill=170)
        im.putalpha(sh.filter(ImageFilter.GaussianBlur(18 * k)))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((40 * k, 40 * k, (40 + w) * k, (40 + h) * k), 44 * k, fill=(255, 255, 255, 250))
        cx, cy, r = (40 + 88) * k, (40 + h // 2) * k, 52 * k                  # red map pin with "!"
        d.ellipse((cx - r, cy - r - 8 * k, cx + r, cy + r - 8 * k), fill=(232, 40, 52))
        d.polygon([(cx - 30 * k, cy + 26 * k), (cx + 30 * k, cy + 26 * k), (cx, cy + 66 * k)], fill=(232, 40, 52))
        d.ellipse((cx - 30 * k, cy - 38 * k, cx + 30 * k, cy + 22 * k), fill=(255, 255, 255))
        d.text((cx, cy - 9 * k), "!", font=font("xb", 50 * k), fill=(232, 40, 52), anchor="mm")
        im = im.resize((w + 80, h + 80), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        d.text((40 + 168, 40 + 62), "ALAMAT TIDAK DITEMUKAN", font=font("xb", 42), fill=(214, 30, 44), anchor="lm")
        d.text((40 + 170, 40 + 116), "GPS tidak bisa menemukan rumah tujuan", font=font("m", 28), fill=(96, 104, 116), anchor="lm")
        _cache["notif"] = im
    return _cache["notif"]


CLUES = ["tanya warga", "dekat masjid", "pintu biru"]
INK = (28, 44, 104)
TICK = (12, 150, 70)


def note_card(t):
    """Handwritten address note; each clue gets ticked as he finds it."""
    w, h, k = 500, 330, 2
    im = Image.new("RGBA", ((w + 60) * k, (h + 60) * k), (0, 0, 0, 0))
    sh = Image.new("L", im.size, 0)
    ImageDraw.Draw(sh).rectangle((30 * k, 40 * k, (30 + w) * k, (40 + h) * k), fill=150)
    im.putalpha(sh.filter(ImageFilter.GaussianBlur(14 * k)))
    d = ImageDraw.Draw(im)
    d.rectangle((30 * k, 30 * k, (30 + w) * k, (30 + h) * k), fill=(255, 249, 230))
    for j in range(5):                                                 # faint ruled lines
        y = (30 + 118 + j * 62) * k
        d.line([(50 * k, y), ((10 + w) * k, y)], fill=(214, 226, 240), width=2 * k)
    d.rectangle(((30 + w / 2 - 70) * k, 18 * k, (30 + w / 2 + 70) * k, 52 * k), fill=(236, 222, 186, 200))   # tape
    d.text((54 * k, 50 * k), "Alamat:", font=font("m", 22 * k), fill=(120, 120, 130))
    d.text((52 * k, 74 * k), "Rumah Nenek Sumi", font=font("hand", 54 * k), fill=INK)
    for j, txt in enumerate(CLUES):
        y = (30 + 150 + j * 62) * k
        bx = 58 * k
        d.rounded_rectangle((bx, y - 17 * k, bx + 34 * k, y + 17 * k), 5 * k, outline=INK, width=3 * k)
        d.text((bx + 52 * k, y), txt, font=font("hand", 46 * k), fill=INK, anchor="lm")
        p = lin(t, TICKS[j], TICKS[j] + 0.22)
        if p > 0:                                                      # hand-drawn green tick, drawn on
            pts = [(bx + 4 * k, y - 2 * k), (bx + 15 * k, y + 13 * k), (bx + 44 * k, y - 28 * k)]
            seg1 = min(1, p / 0.35)
            seg2 = clamp((p - 0.35) / 0.65)
            mid = (pts[0][0] + (pts[1][0] - pts[0][0]) * seg1, pts[0][1] + (pts[1][1] - pts[0][1]) * seg1)
            d.line([pts[0], mid], fill=TICK, width=7 * k, joint="curve")
            if seg2 > 0:
                end = (pts[1][0] + (pts[2][0] - pts[1][0]) * seg2, pts[1][1] + (pts[2][1] - pts[1][1]) * seg2)
                d.line([pts[1], end], fill=TICK, width=7 * k, joint="curve")
            if p >= 1:                                                 # found: strike-through in green
                tw = font("hand", 46 * k).getlength(txt)
                q = ease_out(lin(t, TICKS[j] + 0.22, TICKS[j] + 0.5))
                if q > 0:
                    d.line([(bx + 50 * k, y + 4 * k), (bx + 50 * k + tw * q, y + 2 * k)], fill=TICK + (150,), width=4 * k)
    im = im.resize((w + 60, h + 60), Image.LANCZOS)
    return im.rotate(2.5, resample=Image.BICUBIC, expand=True)


def badge():
    if "badge" not in _cache:
        w, h, k = 740, 170, 2
        im = Image.new("RGBA", ((w + 80) * k, (h + 80) * k), (0, 0, 0, 0))
        sh = Image.new("L", im.size, 0)
        ImageDraw.Draw(sh).rounded_rectangle((40 * k, 52 * k, (40 + w) * k, (52 + h) * k), 40 * k, fill=170)
        im.putalpha(sh.filter(ImageFilter.GaussianBlur(18 * k)))
        ImageDraw.Draw(im).rounded_rectangle((40 * k, 40 * k, (40 + w) * k, (40 + h) * k), 40 * k, fill=(255, 255, 255))
        im = im.resize((w + 80, h + 80), Image.LANCZOS)
        im.alpha_composite(check_icon(104, (0, 160, 72)), (40 + 30, 40 + 33))
        d = ImageDraw.Draw(im)
        d.text((40 + 158, 40 + 70), "PAKET DITERIMA", font=font("xb", 56), fill=(0, 140, 64), anchor="lm")
        d.text((40 + 160, 40 + 128), "16:47  ·  H8KI Logistik Lionindo", font=font("m", 28), fill=(90, 100, 110), anchor="lm")
        _cache["badge"] = im
    return _cache["badge"]


def make_logo():
    im = np.asarray(Image.open("logo.jpg").convert("RGB"), np.float32)
    dist = np.max(np.abs(im - 247.0), axis=2)
    a = np.clip((dist - 6) / 40, 0, 1)
    col = np.clip((im - 247 * (1 - a[..., None])) / np.maximum(a[..., None], 1e-3), 0, 255)
    lg = Image.fromarray(np.dstack([col, a * 255]).astype(np.uint8), "RGBA")
    lg = lg.crop(lg.getbbox())
    return lg.resize((820, int(lg.height * 820 / lg.width)), Image.LANCZOS)


LOGO = make_logo()


def cta_pill():
    if "cta" not in _cache:
        f = font("sb", 42)
        txt = "Tag orang yang kamu kangenin"
        tw, th, b = text_size(txt, f)
        w, h = tw + 90, 92
        im = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((4, 4, 4 + w, 4 + h), h // 2, fill=(0, 150, 70))
        d.text((4 + w / 2, 4 + h / 2), txt, font=f, fill=(255, 255, 255), anchor="mm")
        _cache["cta"] = im
    return _cache["cta"]


# ------------------------------------------------------------------ compose
_END = None


def end_bg():
    global _END
    if _END is None:
        _END = footage(len(SRC) - 1)
    return _END


def frame(k):
    t = k / FPS
    if t < FOOT_END:
        arr = footage(k)
    else:                                   # hold the last frame, still slowly pushing in
        arr = end_bg()
        z = 1 + 0.035 * ease_io(lin(t, FOOT_END, DUR))
        M = cv2.getRotationMatrix2D((540, 820), 0, z)
        arr = cv2.warpAffine(arr, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    # end: the image softens and dims for the closing line
    if t >= DIM_T:
        p = ease_io(lin(t, DIM_T, DIM_T + 0.8))
        small = cv2.resize(arr, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        bl = cv2.resize(cv2.GaussianBlur(small, (0, 0), 1 + 5 * p), (W, H), interpolation=cv2.INTER_LINEAR)
        arr = (arr * (1 - p) + bl * p) * (1 - 0.5 * p)
    # lower scrim behind the big lines
    sl = max(clamp(min((t - T1A + 0.2) / 0.4, (T1_OUT + 0.2 - t) / 0.4)),
             clamp(min((t - GIFT_A + 0.2) / 0.4, (GIFT_OUT + 0.3 - t) / 0.4)))
    if sl > 0 and t < DIM_T + 0.3:
        arr = arr * (1 - 0.62 * sl * SCRIM_LOW)
    if t >= CARD_T:
        p = ease_io(lin(t, CARD_T, CARD_T + 0.3))
        arr = arr * (1 - p) + WHITE_BG * p
    img = to_img(arr)

    # ---- hook: the GPS gives up (a small error shake right after it lands)
    if t < 1.9:
        a, s, dy = pop(t, NOTIF_T, 0.45, 1.85, 0.3, rise=-40)
        shake = 10 * math.sin((t - 0.45) * 60) * math.exp(-(t - 0.45) * 9) if t > 0.45 else 0
        paste_layer(img, notif_card(), 540 + shake, 470 + dy, a, s)
    a, s, dy = pop(t, T1A, 0.55, T1_OUT)
    draw_text(img, "GPS menyerah.", font("sb", 62), 540, 1290 + dy, (255, 255, 255), a, s, blur=14)
    a, s, dy = pop(t, T1B, 0.55, T1_OUT)
    draw_text(img, "Kurir kami tidak.", font("xb", 98), 540, 1395 + dy, RED, a, s, blur=18)

    # ---- the address note, ticked clue by clue
    if NOTE_IN <= t <= NOTE_OUT:
        p_in = ease_out(lin(t, NOTE_IN, NOTE_IN + 0.5))
        p_out = ease_in(lin(t, NOTE_OUT - 0.4, NOTE_OUT))
        nc = note_card(t)
        bump = 0.0
        for tk in TICKS:
            if tk <= t < tk + 0.35:
                bump = 0.04 * math.sin(math.pi * (t - tk) / 0.35)
        x = 64 + nc.width / 2
        y = 330 - 260 * (1 - p_in) - 200 * p_out
        paste_layer(img, nc, x, y, min(p_in * 1.4, 1) * (1 - p_out), 1 + bump)

    # ---- delivered
    if BADGE_T <= t <= BADGE_OUT:
        a, s, dy = pop(t, BADGE_T, 0.5, BADGE_OUT, 0.4, rise=30)
        paste_layer(img, badge(), 540, 300 + dy, a, 0.6 + 0.4 * s if s < 1 else s)

    # ---- the reveal
    a, s, dy = pop(t, GIFT_A, 0.55, GIFT_OUT)
    draw_text(img, "Kiriman dari anak", font("sb", 64), 540, 1360 + dy, (255, 255, 255), a, s, blur=14)
    a, s, dy = pop(t, GIFT_B, 0.55, GIFT_OUT)
    draw_text(img, "di Jakarta.", font("xb", 90), 540, 1460 + dy, GOLD, a, s, blur=18)

    # ---- closing line over the softened last frame
    if WAIT_A <= t < CARD_T + 0.3:
        a, s, dy = pop(t, WAIT_A, 0.6, CARD_T + 0.05, 0.35)
        draw_text(img, "Ada yang menunggu", font("sb", 66), 540, 880 + dy, (255, 255, 255), a, s, blur=16)
        a, s, dy = pop(t, WAIT_B, 0.6, CARD_T + 0.05, 0.35)
        draw_text(img, "di ujung setiap alamat.", font("xb", 78), 540, 985 + dy, GOLD, a, s, blur=18)

    # ---- logo card
    if t >= CARD_T:
        p = lin(t, CARD_T + 0.05, CARD_T + 0.5)
        lg = LOGO
        sp = lin(t, CARD_T + 0.7, CARD_T + 1.4)
        if 0 < sp < 1:
            lg = LOGO.copy()
            gx = np.arange(lg.width)[None, :] + np.arange(lg.height)[:, None] * 0.4
            c = -200 + sp * (lg.width + 400)
            band = np.exp(-((gx - c) / 60) ** 2) * 0.55
            la = np.asarray(lg, np.float32).copy()
            la[..., :3] = la[..., :3] + (255 - la[..., :3]) * band[..., None]
            lg = Image.fromarray(la.astype(np.uint8), "RGBA")
        drift = 1 + 0.03 * ease_io(lin(t, CARD_T + 0.4, DUR))
        paste_layer(img, lg, 540, 760, ease_out(p), (0.9 + 0.1 * back_in_out(p, 1.2)) * drift)
        a, s, dy = pop(t, TAG_A, 0.5)
        draw_text(img, "Kurir yang", font("xb", 92), 540, 1120 + dy, (30, 36, 48), a, s, shadow=0.12, blur=12)
        a, s, dy = pop(t, TAG_B, 0.5)
        draw_text(img, "nggak nyerah.", font("xb", 104), 540, 1235 + dy, (228, 20, 30), a, s, shadow=0.15, blur=12)
        u = ease_out(lin(t, TAG_B + 0.4, TAG_B + 0.8))
        if u > 0:
            half = 330 * u
            ImageDraw.Draw(img).rounded_rectangle((540 - half, 1318, 540 + half, 1330), 6, fill=(0, 150, 70))
        a, s, dy = pop(t, CTA_T, 0.5)
        if a > 0:
            breathe = 1 + 0.02 * math.sin(max(0, t - CTA_T - 0.6) * 4.2)
            paste_layer(img, cta_pill(), 540, 1470 + dy, a, s * breathe)
    return np.asarray(img, np.uint8)


def frame_bytes(k):
    return frame(k).tobytes()


if __name__ == "__main__":
    out = sys.argv[1]
    if len(sys.argv) > 2:
        for tt in map(float, sys.argv[2:]):
            Image.fromarray(frame(int(round(tt * FPS)))).save(f"prev_{tt:05.2f}.jpg", quality=88)
        sys.exit()
    n = int(DUR * FPS)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", "audio_nenek.wav", "-c:v", "libx264", "-preset", "slow", "-b:v", "7.4M", "-maxrate", "9M",
           "-bufsize", "16M", "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", "-shortest", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for k, b in enumerate(pool.imap(frame_bytes, range(n), chunksize=6)):
            p.stdin.write(b)
            if k % 96 == 0:
                print(f"{k}/{n}", flush=True)
    p.stdin.close()
    p.wait()
    print("done", out)
