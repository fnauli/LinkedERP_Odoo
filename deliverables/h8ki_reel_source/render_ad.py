"""Ad cut of the v29 Reel: no animated GPS opening. It starts on the courier in the alley (master frame 308,
just after the "GPS menyerah." text has faded), with the parcel's landmark address and the GPS error laid
over the first 4 seconds, kept clear of the bag logo and of the bottom band where Instagram puts the ad button.
  python3 render_ad.py MASTER.mp4 OUT.mp4
"""
import sys, os, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import imageio_ffmpeg
from gfx import font

FF = imageio_ffmpeg.get_ffmpeg_exe()
SRC, OUT = sys.argv[1], sys.argv[2]
W, H, FPS = 1080, 1920, 24
F0 = 308                                   # first master frame used (12.83 s)
S0 = F0 / FPS
RED, WHITE = (227, 24, 30), (255, 255, 255)

HEAD = ("ALAMAT DI PAKET:", 0.0)
LINES = [("Dekat masjid.", -0.22), ("Depan pohon mangga.", 0.45), ("Gang mentok, belok kiri.", 0.9)]
CHIP_T = 1.6                               # "GPS: alamat tidak ditemukan"
OUT_A, OUT_B = 3.7, 4.05                   # whole hook fades out
Y0 = 1150


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def warn_icon(d, cx, cy, s, fg, bg):
    d.polygon([(cx, cy - s * 0.55), (cx + s * 0.6, cy + s * 0.48), (cx - s * 0.6, cy + s * 0.48)], fill=fg)
    d.rounded_rectangle((cx - s * 0.06, cy - s * 0.22, cx + s * 0.06, cy + s * 0.16), s * 0.05, fill=bg)
    d.ellipse((cx - s * 0.07, cy + s * 0.24, cx + s * 0.07, cy + s * 0.38), fill=bg)


def overlay(t):
    """RGBA layer for hook time t, or None once it has gone."""
    if t >= OUT_B:
        return None
    fade = 1 - ease((t - OUT_A) / (OUT_B - OUT_A)) if t > OUT_A else 1.0
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # soft dark band behind the text (from below the bag logo down), so white reads on the wet stones
    g = np.clip((np.arange(H) - (Y0 - 140)) / 220, 0, 1) * 0.62
    band = Image.fromarray(np.repeat((g * 255 * fade).astype(np.uint8)[:, None], W, 1), "L")
    lay.paste((8, 10, 18, 255), (0, 0), band)
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt)
    fh, fl, fc = font("sb", 36), font("xb", 60), font("b", 38)
    y = Y0
    d.text((W / 2, y), HEAD[0], font=fh, fill=(255, 255, 255, 215), anchor="mt")
    y += 62
    for s, t0 in LINES:
        a = ease((t - t0) / 0.22)
        if a > 0:
            d.text((W / 2, y + 18 * (1 - a)), s, font=fl, fill=(255, 255, 255, int(255 * a)), anchor="mt")
        y += 80
    a = ease((t - CHIP_T) / 0.16)
    if a > 0:
        label = "GPS: alamat tidak ditemukan"
        tw = fc.getlength(label) + 64
        bw, bh = tw + 48, 78
        sc = 0.85 + 0.15 * a
        chip = Image.new("RGBA", (int(bw), bh), (0, 0, 0, 0))
        cd = ImageDraw.Draw(chip)
        cd.rounded_rectangle((0, 0, bw - 1, bh - 1), bh // 2, fill=RED + (255,))
        warn_icon(cd, 44, bh / 2, 40, WHITE, RED)
        cd.text((80, bh / 2), label, font=fc, fill=WHITE, anchor="lm")
        chip = chip.resize((int(bw * sc), int(bh * sc)), Image.LANCZOS)
        cx, cy = W // 2, y + 20 + bh // 2
        al = chip.getchannel("A").point(lambda v: int(v * a))
        chip.putalpha(al)
        txt.alpha_composite(chip, (cx - chip.width // 2, cy - chip.height // 2))
    # subtle shadow for legibility
    sh = txt.getchannel("A").filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.6))
    lay.paste((0, 0, 0, 255), (0, 3), sh)
    lay.alpha_composite(txt)
    if fade < 1:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * fade)))
    return lay


def audio(path):
    """Master sound from S0 with a short fade-in, plus a tick per address line and the GPS error blip."""
    SR = 48000
    raw = subprocess.run([FF, "-v", "error", "-ss", f"{S0:.4f}", "-i", SRC, "-vn", "-ac", "2", "-ar", str(SR),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float64).reshape(-1, 2) / 32768
    n = len(a)
    fi = int(0.3 * SR)
    a[:fi] *= np.linspace(0, 1, fi)[:, None] ** 2
    rng = np.random.default_rng(3)

    def put(sig, t, g):
        i = int(t * SR)
        m = min(len(sig), n - i)
        a[i:i + m] += sig[:m, None] * g

    for _, t0 in LINES:
        tt = np.arange(int(0.05 * SR)) / SR
        click = rng.standard_normal(len(tt)) * np.exp(-tt * 140)
        click = np.convolve(click, np.ones(6) / 6, "same")
        put(click, max(t0, 0.0) + 0.02, 0.05)
    for k, f in enumerate([659.3, 523.3]):                       # soft two-tone error, as in the original hook
        tt = np.arange(int(0.22 * SR)) / SR
        s = np.sin(2 * np.pi * f * tt) + 0.25 * np.sign(np.sin(2 * np.pi * f * tt))
        e = np.exp(-tt / 0.07)
        e[:200] *= np.linspace(0, 1, 200)
        put(s * e, CHIP_T + k * 0.13, 0.06)
    pk = np.abs(a).max()
    if pk > 0.98:
        a *= 0.98 / pk
    w = wave.open(path, "wb")
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((a * 32767).astype(np.int16).tobytes())
    w.close()
    return n / SR


if __name__ == "__main__":
    wav = OUT + ".wav"
    dur = audio(wav)
    dec = subprocess.Popen([FF, "-v", "error", "-i", SRC, "-vf", f"select=gte(n\\,{F0})", "-vsync", "0",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    master = OUT + ".master.mp4"
    enc = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "14",
                            "-tune", "film", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", "-shortest",
                            "-movflags", "+faststart", master], stdin=subprocess.PIPE)
    k = 0
    while True:
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        t = k / FPS
        lay = overlay(t)
        if lay is not None:
            im = Image.frombytes("RGB", (W, H), buf).convert("RGBA")
            im.alpha_composite(lay)
            buf = im.convert("RGB").tobytes()
            if k in (0, 12, 30, 48, 80, 95):
                Image.frombytes("RGB", (W, H), buf).save(f"{OUT}.prev_{k:03d}.jpg", quality=90)
        enc.stdin.write(buf)
        k += 1
    enc.stdin.close(); enc.wait(); dec.wait()
    print("frames", k, "video", k / FPS, "audio", dur)
    # upload encode: two-pass, ~7 Mb/s (well under 30 MiB for 26 s)
    for p in (1, 2):
        cmd = [FF, "-v", "error", "-y", "-i", master, "-c:v", "libx264", "-preset", "veryslow", "-b:v", "7000k",
               "-maxrate", "9000k", "-bufsize", "14000k", "-pix_fmt", "yuv420p", "-pass", str(p),
               "-passlogfile", OUT + ".p2"]
        cmd += (["-an", "-f", "mp4", os.devnull] if p == 1 else
                ["-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", OUT])
        subprocess.run(cmd, check=True)
    print("wrote", OUT, os.path.getsize(OUT) / 2 ** 20, "MiB")
