"""Final cut: GPS act (graphics) + four Kling live-action clips + composited branding, text, recap, end card."""
import os
os.environ["REAL"] = "1"
import sys, math, subprocess
import numpy as np, cv2
from multiprocessing import Pool
from PIL import Image
import imageio_ffmpeg
from common import *
from gfx import to_img, to_arr, draw_text, draw_chip, font, pop, glow_add
import scene_digital as SD
import scene_house as SH
from label_logo import apply as logo_on_label

CLIP_FPS = 24
NFR = 121


def zoom(img, z, fy=0.5):
    if z <= 1.001:
        return img
    cw, ch = W / z, H / z
    x0, y0 = (W - cw) / 2, (H - ch) * fy
    return img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BICUBIC)


def grade(a):
    """Gentle unifying grade: navy-lifted blacks, a touch more saturation, soft S-curve."""
    a = a.astype(np.float32)
    g = a.mean(2, keepdims=True)
    a = g + (a - g) * 1.06
    x = np.clip(a / 255.0, 0, 1)
    x = 0.5 + (x - 0.5) * 1.04
    a = x * 255.0 * 0.985 + np.array([1.5, 2.5, 6.0], np.float32)
    return np.clip(a, 0, 255)


def clip_frame(n, src_t):
    idx = int(round(src_t * CLIP_FPS))
    idx = max(0, min(NFR - 1, idx))
    im = cv2.cvtColor(cv2.imread(f"../real/c{n}/{idx + 1:03d}.jpg"), cv2.COLOR_BGR2RGB)
    im = logo_on_label(im, n, idx)
    im = cv2.resize(im, (W, H), interpolation=cv2.INTER_CUBIC)
    return grade(im)


# top scrim for caption legibility over live action
_ys = np.arange(H, dtype=np.float32)
SCRIM = (np.clip(1 - np.abs(_ys - 450) / 380, 0, 1) ** 1.5)[:, None, None]


def scrim(arr, k, depth=0.5):
    if k <= 0:
        return arr
    return arr * (1 - depth * k * SCRIM)


def text_strength(t):
    for a, b in (T1, T2, T3, (LINE1_T - 0.1, S4_END)):
        if a - 0.2 <= t <= b + 0.2:
            return min(1.0, (t - a + 0.2) / 0.4, (b + 0.2 - t) / 0.4)
    return 0.0


def overlays(img, t):
    # location payoffs: what the GPS could not find, the courier does
    draw_chip(img, "Dekat masjid", 540, 690, t, 12.3, 1.7)
    draw_chip(img, "Depan pohon mangga", 60, 640, t, 15.0, 1.6, anchor="l")
    draw_chip(img, "Masuk gang, mentok, belok kiri", 540, 780, t, 16.1, 1.4)
    draw_chip(img, "Rumah cat hijau", 60, 560, t, 17.75, 1.6, anchor="l")
    draw_chip(img, "Pagar hitam", 60, 860, t, 18.15, 1.6, anchor="l")
    draw_chip(img, "Warung Bu Ani", 1040, 900, t, 18.55, 1.6, anchor="r")
    # story lines (white + brand red, anticipation + overshoot)
    a, s, dy = pop(t, T1[0], 0.6, T1[1])
    draw_text(img, "Kurir kami tidak.", font("xb", 88), 540, 420 + dy, (255, 255, 255), a, s, blur=16)
    a, s, dy = pop(t, T2[0], 0.55, T2[1])
    draw_text(img, "Buat yang kirim, ini order", font("sb", 54), 540, 390 + dy, (255, 255, 255), a, s, blur=14)
    a, s, dy = pop(t, T2[0] + 0.45, 0.55, T2[1])
    draw_text(img, "yang sudah lama ditunggu.", font("xb", 58), 540, 466 + dy, (255, 56, 64), a, s, blur=16)
    for k, (txt, y, dt) in enumerate([("Satu paket,", 390, 0.05), ("satu penghasilan.", 480, 1.0)]):
        a, s, dy = pop(t, T3[0] + dt, 0.5, T3[1])
        draw_text(img, txt, font("xb", 80), 540, y + dy, (255, 255, 255) if k == 0 else (255, 56, 64), a, s, blur=18)
    # delivery confirmed
    if t >= BADGE_T:
        a, s, dy = pop(t, BADGE_T, 0.5, rise=30)
        from gfx import paste_layer
        paste_layer(img, SH.badge(), 540, 250 + dy, a, 0.6 + 0.4 * s if s < 1 else s)
    a, s, dy = pop(t, LINE1_T, 0.5)
    draw_text(img, "Alamatnya ketemu.", font("xb", 70), 540, 440 + dy, (255, 255, 255), a, s, blur=16)
    a, s, dy = pop(t, LINE2_T, 0.5)
    draw_text(img, "Sejauh apa pun alamatnya.", font("xb", 52), 540, 522 + dy, (255, 56, 64), a, s, blur=16)


def live(t):
    for n, (a, b, off) in CLIPS.items():
        if a <= t < b or (n == 4 and t >= a):
            arr = clip_frame(n, off + (t - a))
            if n == 1 and t < a + 0.6:                  # from the black "GPS menyerah." screen
                arr = arr * ease_io(lin(t, a, a + 0.6))
            return arr
    raise ValueError(t)


_RBG = None


def recap_bg():
    a = clip_frame(4, CLIPS[4][2] + (CLIPS[4][1] - CLIPS[4][0]) - 0.04)
    g = a.mean(axis=2, keepdims=True)
    return (a * 0.5 + g * 0.5) * 0.28 + np.array([4, 6, 16], np.float32)


def frame(i):
    hf = int(HOOK * FPS)
    if i < hf:
        th = i / FPS
        return np.asarray(zoom(to_img(SD.hook(th)), 1.06 - 0.06 * ease_out(th / HOOK)), np.uint8).tobytes()
    t = (i - hf) / FPS
    if t < S1_END:
        return np.asarray(zoom(to_img(SD.scene1(t)), 1 + 0.035 * ease_io(t / S1_END)), np.uint8).tobytes()
    if t < NIGHT_START:
        return np.asarray(to_img(SD.scene2(t)), np.uint8).tobytes()
    if t < S4_END:
        arr = live(t)
        if t < NIGHT_START + 0.45:                      # "GPS menyerah." fades as the night appears
            txt = SD.scene2(NIGHT_START - 0.01)
            arr = np.maximum(arr, txt * (1 - lin(t, NIGHT_START, NIGHT_START + 0.45)))
        arr = scrim(arr, text_strength(t), 0.82 if t >= LINE1_T - 0.1 else 0.5)
        img = to_img(arr)
        overlays(img, t)
        return np.asarray(img, np.uint8).tobytes()
    if t < LOGO_T:
        global _RBG
        if _RBG is None:
            _RBG = recap_bg()
            SH._rbg = _RBG
        rec = SH.recap_frame(t)
        p = ease_io(lin(t, RECAP_T, RECAP_T + 0.2))
        if p < 1:
            under = live(t)
            rec = to_img(under * (1 - p) + to_arr(rec) * p)
        return np.asarray(rec, np.uint8).tobytes()
    return np.asarray(SH.scene5(t), np.uint8).tobytes()


if __name__ == "__main__":
    out = sys.argv[1]
    n = int((DUR + HOOK) * FPS)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", "audio_real.wav", "-c:v", "libx264", "-preset", "slow", "-b:v", "8M", "-maxrate", "10M",
           "-bufsize", "16M", "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", "-shortest", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for k, b in enumerate(pool.imap(frame, range(n), chunksize=4)):
            p.stdin.write(b)
            if k % 120 == 0:
                print(f"{k}/{n}", flush=True)
    p.stdin.close()
    p.wait()
    print("done", out)
