"""Reel #4 "MISI KURIR #1": a different format from Reel #3. Full-screen cinematic footage (no split screen) with a
game-style mission HUD: the address as the mission, four objectives that tick off with XP, "MISI SELESAI", then the
game layer falls away for the real reward: the family photo Nenek has waited for.
Kling footage of "Kiriman untuk Nenek" as filmed, with its warm grade. Sound cues are placed on measured frames
(footfalls 160/172/183/194, knocks 238/247/251, latch 275, cardboard 48-70) via src_time().
  python3 render_misi.py OUT.mp4 [preview t ...]"""
import sys, math, subprocess
from multiprocessing import Pool
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
from gfx import font, paste_layer, draw_text, check_icon, pop, back_in_out
from common import clamp, lin, ease_io, ease_out
import render_r4 as R

W, H, FPS = 1080, 1920, 24
INK, RED, GREEN, GOLD = (24, 28, 40), (227, 24, 30), (4, 152, 68), (255, 196, 64)
END_T, TRANS = 14.4, 0.35
CARD_T = END_T + 0.3
DUR = 15.7

# (t0, t1, clip, first src, last src, warm grade)
SHOTS = [
    (0.0, 3.0, "k1", 73, 143, 1.0),     # asks the way; the old man smiles and points (src 133)
    (3.0, 5.0, "k1", 152, 200, 0.3),    # walks towards the minaret
    (5.0, 7.0, "k1", 226, 262, 1.0),    # knocks on the blue door (0.75x)
    (7.0, 9.6, "k1", 274, 346, 1.0),    # the door opens, Nenek takes the parcel
    (9.6, 11.2, "k2", 20, 62, 1.0),     # he bows and leaves, she opens the box
    (11.2, END_T, "k2", 62, 121, 1.0),  # the family photo comes out
]


def src_time(clip, s):
    """Timeline time of source frame s (for placing sounds on the picture)."""
    for t0, t1, c, fa, fb, _ in SHOTS:
        if c == clip and fa <= s <= fb:
            return t0 + (s - fa) / (fb - fa) * (t1 - t0)
    raise ValueError((clip, s))


T_ASK = src_time("k1", 133)            # he points the way
T_MOSQUE = 4.0                         # the minaret is in frame
T_DOOR = src_time("k1", 238)           # first knock
T_GIVE = src_time("k1", 320)           # parcel in her hands
T_DONE = T_GIVE + 0.05
OBJ = [("Tanya warga", T_ASK), ("Cari masjid", T_MOSQUE), ("Temukan pintu biru", T_DOOR), ("Paket diterima", T_GIVE)]
HUD_IN, HUD_OUT = 1.45, (9.7, 10.15)


def footage(t):
    for t0, t1, c, fa, fb, warm in SHOTS:
        if t0 <= t < t1:
            break
    u = clamp((t - t0) / (t1 - t0))
    a = R.src(c, fa + u * (fb - fa))
    sh, sw = a.shape[:2]
    z = 1 + 0.04 * u                                    # slow push-in
    w = sw / z; h = w * H / W
    x0 = (sw - w) / 2; y0 = clamp((sh - h) / 2, 0, sh - h)
    M = np.float32([[W / w, 0, -x0 * W / w], [0, H / h, -y0 * H / h]])
    f = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    f = R.grade(f, warm).astype(np.float32)
    return np.clip(f * VIG, 0, 255).astype(np.uint8)


yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.24 * np.clip(np.sqrt(((xx - 540) / 640) ** 2 + ((yy - 960) / 1150) ** 2), 0, 1.4) ** 2.2)[..., None]
SCRIM_TOP = np.clip((420 - yy) / 420, 0, 1)[..., None] ** 1.5           # for text at the top
SCRIM_LOW = np.clip((yy - 1050) / 500, 0, 1)[..., None] ** 1.3          # for the HUD at the bottom


def star(d, cx, cy, r, col):
    pts = [(cx + (r if k % 2 == 0 else r * 0.42) * math.cos(-math.pi / 2 + k * math.pi / 5),
            cy + (r if k % 2 == 0 else r * 0.42) * math.sin(-math.pi / 2 + k * math.pi / 5)) for k in range(10)]
    d.polygon(pts, fill=col)


def mission_card(t):
    """The big mission card of the hook (frame 1): readable in one glance."""
    L = Image.new("RGBA", (960, 440), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    d.rounded_rectangle((0, 0, 959, 439), 40, fill=(16, 18, 28, 215), outline=GOLD + (255,), width=4)
    d.text((44, 30), "MISI KURIR #1", font=font("xb", 40), fill=GOLD)
    d.text((620, 40), "Kesulitan", font=font("m", 26), fill=(220, 220, 228))
    for k in range(5):
        star(d, 760 + k * 38, 54, 16, GOLD)
    d.text((44, 100), "Antar paket ke:", font=font("sb", 42), fill=(255, 255, 255))
    d.text((44, 160), "“pintu biru", font=font("xb", 76), fill=(255, 255, 255))
    d.text((44, 250), "dekat masjid”", font=font("xb", 76), fill=GOLD)
    f = font("b", 34); txt = "GPS: alamat tidak ditemukan"
    d.rounded_rectangle((44, 358, 44 + f.getlength(txt) + 56, 416), 29, fill=RED + (255,))
    d.text((72, 365), txt, font=f, fill=(255, 255, 255))
    return L


def hud(t):
    """Compact mission HUD (bottom left, clear of the faces and of Instagram's buttons)."""
    L = Image.new("RGBA", (660, 360), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    d.rounded_rectangle((0, 0, 659, 359), 30, fill=(16, 18, 28, 200), outline=GOLD + (200,), width=3)
    d.text((28, 20), "MISI KURIR #1", font=font("xb", 28), fill=GOLD)
    for k in range(5):
        star(d, 300 + k * 28, 38, 11, GOLD)
    d.text((28, 62), "“pintu biru dekat masjid”", font=font("b", 32), fill=(255, 255, 255))
    d.text((28, 104), "Pengirim: anaknya di Jakarta", font=font("m", 26), fill=(205, 208, 216))
    done = 0
    for i, (txt, ti) in enumerate(OBJ):
        y = 150 + i * 44
        p = ease_out(lin(t, ti, ti + 0.25))
        if p > 0:
            done += 1
            sc = 1 + 0.35 * math.sin(math.pi * min(1, (t - ti) / 0.35)) if t - ti < 0.35 else 1
            ic = check_icon(int(32 * sc))
            L.alpha_composite(ic, (28 + (32 - ic.width) // 2, y + 4 + (32 - ic.height) // 2))
        else:
            d.rounded_rectangle((30, y + 6, 58, y + 34), 7, outline=(200, 204, 214, 255), width=3)
        d.text((74, y), txt, font=font("sb", 30), fill=(255, 255, 255, 255) if p == 0 else (170, 230, 190, 255))
        if 0 < t - ti < 0.9:                            # floating +100 XP
            q = (t - ti) / 0.9
            fx = font("xb", 28)
            col = GOLD + (int(255 * (1 - q)),)
            d.text((74 + font("sb", 30).getlength(txt) + 20, y - 18 * q), "+100 XP", font=fx, fill=col)
    xp = sum(ease_out(lin(t, ti, ti + 0.4)) for _, ti in OBJ) / len(OBJ)
    d.rounded_rectangle((28, 330 - 6, 632, 340), 8, fill=(60, 64, 80, 255))
    if xp > 0:
        d.rounded_rectangle((28, 330 - 6, 28 + 604 * xp, 340), 8, fill=GOLD + (255,))
    return L


def done_banner(img, t):
    a, s, dy = pop(t, T_DONE, 0.5, 9.75, 0.35)
    if a <= 0:
        return
    L = Image.new("RGBA", (820, 210), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    d.rounded_rectangle((0, 0, 819, 209), 40, fill=(16, 18, 28, 225), outline=GOLD + (255,), width=5)
    L.alpha_composite(check_icon(84), (44, 30))
    d.text((150, 26), "MISI SELESAI", font=font("xb", 72), fill=GOLD)
    d.text((152, 126), "+400 XP  ·  GPS nyerah, kurir nggak", font=font("sb", 32), fill=(255, 255, 255))
    paste_layer(img, L, W / 2, 330 + dy, a, s)


def cta(img, t):
    a, s, dy = pop(t, 12.9, 0.5)
    if a > 0:
        f = font("b", 40); txt = "Kirim ke yang lagi jauh dari keluarga"
        tw = f.getlength(txt)
        L = Image.new("RGBA", (int(tw) + 150, 96), (0, 0, 0, 0))
        ImageDraw.Draw(L).rounded_rectangle((0, 0, L.width - 1, 95), 48, fill=(16, 18, 28, 220))
        ImageDraw.Draw(L).text((40, 21), txt, font=f, fill=(255, 255, 255))
        nudge = 6 * max(0.0, math.sin(max(0, t - 13.3) * 6)) ** 6
        L.alpha_composite(R.send_icon(56), (int(tw) + 62 + int(nudge), 20 - int(nudge * 0.6)))
        paste_layer(img, L, W / 2 - 30, 1425 + dy, a, s)
    a, s, dy = pop(t, 13.4, 0.5)
    if a > 0:
        f = font("b", 40); txt = "Follow buat Misi #2"
        L = Image.new("RGBA", (int(f.getlength(txt)) + 90, 96), (0, 0, 0, 0))
        ImageDraw.Draw(L).rounded_rectangle((0, 0, L.width - 1, 95), 48, fill=GREEN + (255,))
        ImageDraw.Draw(L).text((45, 20), txt, font=f, fill=(255, 255, 255))
        paste_layer(img, L, W / 2 - 30, 1537 + dy, a, s * (1 + 0.02 * math.sin(max(0, t - 13.8) * 4.2)))


LOGO_M = R.logo(520)


def end_card(t):
    img = Image.new("RGB", (W, H), (255, 255, 255))
    p = ease_out(lin(t, CARD_T, CARD_T + 0.3))
    paste_layer(img, LOGO_M, W / 2, 720, p, 0.92 + 0.08 * back_in_out(p, 1.2))
    a, s, dy = pop(t, CARD_T + 0.12, 0.4)
    draw_text(img, "Kurir yang", font("xb", 88), W / 2, 1040 + dy, INK, a, s, shadow=0.1, blur=10)
    a, s, dy = pop(t, CARD_T + 0.28, 0.4)
    draw_text(img, "nggak nyerah.", font("xb", 100), W / 2, 1150 + dy, RED, a, s, shadow=0.12, blur=10)
    return img


def frame(k):
    t = k / FPS
    if t >= END_T + TRANS:
        return np.asarray(end_card(t))
    f = footage(min(t, END_T - 1e-3)).astype(np.float32)
    hud_a = ease_out(lin(t, HUD_IN, HUD_IN + 0.35)) * (1 - ease_io(lin(t, *HUD_OUT)))
    low = max(1.0 if t < HUD_IN + 0.35 else 0.0, hud_a)
    top = max(ease_out(lin(t, T_DONE, T_DONE + 0.3)) * (1 - ease_io(lin(t, 9.6, 10.0))),
              ease_out(lin(t, 11.6, 12.0)))
    f = f * (1 - 0.55 * low * SCRIM_LOW) * (1 - 0.6 * top * SCRIM_TOP)
    img = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).convert("RGBA")
    if t < HUD_IN + 0.35:                              # hook: the big mission card lands like a stamp, then hands over
        a = 1 - ease_out(lin(t, HUD_IN - 0.05, HUD_IN + 0.3))
        s = (1.1 - 0.1 * ease_out(lin(t, 0, 0.2))) * (1 - 0.25 * ease_io(lin(t, HUD_IN - 0.05, HUD_IN + 0.3)))
        paste_layer(img, mission_card(t), W / 2 - 160 * ease_io(lin(t, HUD_IN - 0.05, HUD_IN + 0.3)), 1300, a, s)
    if hud_a > 0:
        paste_layer(img, hud(t), 36 + 330 - 40 * (1 - hud_a), 1360, hud_a)
    done_banner(img, t)
    a1, s1, dy1 = pop(t, 11.95, 0.55)                  # the real reward
    a2, s2, dy2 = pop(t, 12.45, 0.55)
    draw_text(img, "Isinya foto cucu", font("xb", 74), W / 2, 210 + dy1, (255, 255, 255), a1, s1, shadow=0.8, blur=14)
    draw_text(img, "yang belum pernah ia peluk.", font("xb", 66), W / 2, 305 + dy2, GOLD, a2, s2, shadow=0.85, blur=14)
    cta(img, t)
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
           "-i", "-", "-i", "audio_misi.wav", "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-tune", "film",
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
