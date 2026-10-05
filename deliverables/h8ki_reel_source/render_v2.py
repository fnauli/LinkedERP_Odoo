"""V2 final cut: GPS act (graphics) + Kling v2 story (Clip A, dead-end insert, Clip B, handover fix) + text, recap, end card."""
import os
os.environ["REAL"] = "1"
os.environ["V2"] = "1"
import sys, subprocess
import numpy as np, cv2
from multiprocessing import Pool
from PIL import Image
import imageio_ffmpeg
from common import *
from gfx import to_img, to_arr, draw_text, draw_chip, font, pop, paste_layer
from interp import between
import scene_digital as SD
import scene_house as SH

CLIP_FPS = 24


def zoom(img, z, fy=0.5):
    if z <= 1.001:
        return img
    cw, ch = W / z, H / z
    x0, y0 = (W - cw) / 2, (H - ch) * fy
    return img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BICUBIC)


def load(folder, idx):
    n = len(os.listdir(folder))
    idx = max(1, min(n, idx))
    im = cv2.cvtColor(cv2.imread(f"{folder}/{idx:03d}.jpg"), cv2.COLOR_BGR2RGB)
    return cv2.resize(im, (W, H), interpolation=cv2.INTER_CUBIC)


# --- the mosque shot was locked-off and far darker than the rest (mean 13 vs 35-64): lift it to the same
# blue dusk, give it a slow push-in, drifting mist over the mosque and fine rain, so it lives like the others
def lift_night(a):
    x = (a.astype(np.float32) / 255.0) ** 0.62
    x = x * np.array([0.96, 1.0, 1.06], np.float32)
    return np.clip(x * 255.0, 0, 255).astype(np.uint8)


_rs = np.random.default_rng(3)
_mist = cv2.GaussianBlur(_rs.random((H // 8, W // 4)).astype(np.float32), (0, 0), 6)
_mist = cv2.resize((_mist - _mist.min()) / (np.ptp(_mist) + 1e-6), (W * 2, H), interpolation=cv2.INTER_CUBIC)
_rain = np.zeros((H * 2, W), np.float32)
for _ in range(900):
    x0, y0 = _rs.integers(0, W), _rs.integers(0, H * 2)
    L = _rs.integers(25, 70)
    cv2.line(_rain, (int(x0), int(y0)), (int(x0 - L * 0.18), int(y0 + L)), float(_rs.uniform(0.35, 1.0)), 1)
_rain = cv2.GaussianBlur(_rain, (0, 0), 0.8)


def atmos(arr, t, a, b):
    """Push-in + drifting mist (strongest around the mosque) + fine rain for the opening shot."""
    p = (t - a) / (b - a)
    z = 1.0 + 0.09 * p
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    arr = np.asarray(zoom(img, z, fy=0.42), np.float32)
    ox = int((t - a) * 38) % W
    m = _mist[:, ox:ox + W]
    wy = np.clip(1.2 - np.arange(H, dtype=np.float32) / (H * 0.5), 0, 1)[:, None]
    k = (0.10 + 0.22 * m) * wy
    arr = arr * (1 - k[..., None]) + np.array([150, 168, 190], np.float32) * k[..., None]
    oy = int((t - a) * 1500) % H
    r = _rain[oy:oy + H]
    return np.clip(arr + r[..., None] * np.array([70, 80, 95], np.float32), 0, 255)


# one look for all shots: bring each shot part-way to the median exposure, then a gentle shared grade
def _lum(a):
    return float(cv2.cvtColor(a, cv2.COLOR_RGB2GRAY).mean())


_means = []
for k, (a, b, folder, f0, sp, dz) in enumerate(SHOTS):
    mid = f0 + int((b - a) * CLIP_FPS * sp / 2)
    _means.append(_lum(lift_night(load(folder, mid)) if k == 0 else load(folder, mid)))
_target = float(np.median(_means))
GAIN = [float(np.clip((_target / m) ** 0.55, 0.85, 1.45)) for m in _means]


def grade(a, gain=1.0):
    a = a.astype(np.float32) * gain
    g = a.mean(2, keepdims=True)
    a = g + (a - g) * 1.04
    x = np.clip(a / 255.0, 0, 1)
    x = 0.5 + (x - 0.5) * 1.05
    a = x * 255.0 * 0.985 + np.array([1.0, 2.0, 5.0], np.float32)   # navy-lifted blacks, ties both clips together
    return np.clip(a, 0, 255)


def shot_frame(k, t):
    a, b, folder, f0, sp, dz = SHOTS[k]
    last = f0 + (b - a) * CLIP_FPS * sp
    pos = min(f0 + (t - a) * CLIP_FPS * sp, last)
    if sp == 1.0:
        frm = load(folder, int(round(pos)))
    else:                                                  # slow motion: motion-compensated in-betweens
        i0 = int(np.floor(pos))
        frm = load(folder, i0) if pos - i0 < 0.02 or i0 + 1 > last + 0.5 else between(load(folder, i0), load(folder, i0 + 1), pos - i0)
    if k == 0:
        frm = lift_night(frm)
    arr = grade(frm, GAIN[k])
    if k == 0:
        arr = atmos(arr, t, a, b)
    return arr


def live(t):
    for k, (a, b, folder, f0, sp, dz) in enumerate(SHOTS):
        if a <= t < b or (k == len(SHOTS) - 1 and t >= a):
            arr = shot_frame(k, t)
            if dz > 0 and t < a + dz and k > 0:            # soft dissolve from the previous shot
                w = ease_io((t - a) / dz)
                arr = arr * w + shot_frame(k - 1, t) * (1 - w)
            if k == 0 and t < a + 0.8:                     # up from the black "GPS menyerah." screen
                arr = arr * ease_io(lin(t, a, a + 0.8))
            return arr
    raise ValueError(t)


_ys = np.arange(H, dtype=np.float32)
SCRIM = (np.clip(1 - np.abs(_ys - 430) / 400, 0, 1) ** 1.5)[:, None, None]


def text_strength(t):
    for a, b in (T1, T2, T3, (BADGE_T - 0.1, S4_END)):
        if a - 0.2 <= t <= b + 0.2:
            return min(1.0, (t - a + 0.2) / 0.4, (b + 0.2 - t) / 0.4)
    return 0.0


def overlays(img, t):
    # the landmarks GPS could not use, shown as he passes them
    draw_chip(img, "Dekat masjid", 540, 760, t, bt(1), 2.0)
    draw_chip(img, "Depan pohon mangga", 60, 640, t, bt(5) + 0.4, 1.8, anchor="l")
    draw_chip(img, "Masuk gang, mentok, belok kiri", 540, 600, t, bt(9) + 0.4, 2.2)
    a, s, dy = pop(t, T1[0], 0.6, T1[1])
    draw_text(img, "Kurir kami tidak.", font("xb", 88), 540, 420 + dy, (255, 255, 255), a, s, blur=16)
    a, s, dy = pop(t, T2[0], 0.55, T2[1])
    draw_text(img, "Buat yang kirim, ini order", font("sb", 54), 540, 390 + dy, (255, 255, 255), a, s, blur=14)
    a, s, dy = pop(t, T2[0] + 0.45, 0.55, T2[1])
    draw_text(img, "yang sudah lama ditunggu.", font("xb", 58), 540, 466 + dy, (255, 56, 64), a, s, blur=16)
    if t >= BADGE_T:
        a, s, dy = pop(t, BADGE_T, 0.5, rise=30)
        paste_layer(img, SH.badge(), 540, 250 + dy, a, 0.6 + 0.4 * s if s < 1 else s)
    for k, (txt, y, dt) in enumerate([("Satu paket,", 430, 0.0), ("satu penghasilan.", 515, 0.45)]):
        a, s, dy = pop(t, T3[0] + dt, 0.5, T3[1])
        draw_text(img, txt, font("xb", 74), 540, y + dy, (255, 255, 255) if k == 0 else (255, 56, 64), a, s, blur=18)


_RBG = None


def recap_bg():
    a, b, folder, f0, sp, dz = SHOTS[-1]
    arr = grade(load(folder, f0 + int((b - a) * CLIP_FPS * sp) - 1), GAIN[-1])
    g = arr.mean(axis=2, keepdims=True)
    return (arr * 0.5 + g * 0.5) * 0.28 + np.array([4, 6, 16], np.float32)


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
        if t < NIGHT_START + 0.45:
            txt = SD.scene2(NIGHT_START - 0.01)
            arr = np.maximum(arr, txt * (1 - lin(t, NIGHT_START, NIGHT_START + 0.45)))
        k = text_strength(t)
        if k > 0:
            arr = arr * (1 - (0.8 if t >= BADGE_T - 0.1 else 0.55) * k * SCRIM)
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
            rec = to_img(live(t - 0.001) * (1 - p) + to_arr(rec) * p)
        return np.asarray(rec, np.uint8).tobytes()
    return np.asarray(SH.scene5(t), np.uint8).tobytes()


if __name__ == "__main__":
    out = sys.argv[1]
    if len(sys.argv) > 2:                                  # preview: write a few frames as JPEGs
        for tt in map(float, sys.argv[2:]):
            Image.frombytes("RGB", (W, H), frame(int((tt + HOOK) * FPS))).save(f"prev_{tt:.2f}.jpg", quality=88)
        sys.exit()
    n = int((DUR + HOOK) * FPS)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", "audio_v2.wav", "-c:v", "libx264", "-preset", "slow", "-b:v", "5.6M", "-maxrate", "7.5M",
           "-bufsize", "14M", "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k",
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
