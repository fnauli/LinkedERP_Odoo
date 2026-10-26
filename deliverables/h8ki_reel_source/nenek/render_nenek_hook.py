"""'Kiriman untuk Nenek' v3: a 2-second flash-forward opens the film on Nenek's face as she takes the parcel,
with the stake ("ditunggu 3 Lebaran"), then a short rewind whoosh and the v2 film from its first frame.
Followers already saw "GPS menyerah. Kurir kami tidak." on the first Reel, so the film now opens on what is
new: her, and why this parcel matters.
  python3 render_nenek_hook.py OUT.mp4 [preview]"""
import sys, wave, subprocess
from multiprocessing import Pool
import numpy as np, imageio_ffmpeg
from PIL import Image
import render_nenek as R
from gfx import font, draw_text, pop, to_img
from nk_time import FPS, DUR

W, H = 1080, 1920
COLD_SRC = 14.9                     # film time the flash-forward is taken from (clean footage, no badge)
COLD = 2.0                          # seconds
NC = int(round(COLD * FPS))
L1 = ("Kiriman ini ditunggu Nenek", -0.45)
L2 = ("3 Lebaran lamanya.", -0.1)


def cold_frame(j):
    t = j / FPS
    arr = R.footage(int(round(COLD_SRC * FPS)) + j)
    arr = arr * (1 - 0.62 * R.SCRIM_LOW)
    img = to_img(arr)
    a, s, dy = pop(t, L1[1], 0.55)
    draw_text(img, L1[0], font("sb", 58), 540, 1290 + dy, (255, 255, 255), a, s, blur=14)
    a, s, dy = pop(t, L2[1], 0.55)
    draw_text(img, L2[0], font("xb", 92), 540, 1400 + dy, R.GOLD, a, s, blur=18)
    return np.asarray(img, np.uint8)


def frame_bytes(k):
    return (cold_frame(k) if k < NC else R.frame(k - NC)).tobytes()


def audio(path):
    w = wave.open("audio_nenek.wav")
    sr, ch = w.getframerate(), w.getnchannels()
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64).reshape(-1, ch) / 32768
    i0, n = int(COLD_SRC * sr), int(COLD * sr)
    cold = a[i0:i0 + n].copy()
    env = np.ones(n)
    env[:int(0.12 * sr)] = np.linspace(0, 1, int(0.12 * sr))
    env[-int(0.4 * sr):] = np.linspace(1, 0, int(0.4 * sr)) ** 1.5
    cold *= env[:, None]
    # rewind whoosh across the cut: band-passed noise rising in pitch, peaking on the cut
    m = int(0.5 * sr)
    rng = np.random.default_rng(4)
    noise = rng.standard_normal(m)
    X = np.fft.rfft(noise)
    f = np.fft.rfftfreq(m, 1 / sr)
    X *= np.exp(-((np.log(np.maximum(f, 1)) - np.log(2200)) / 0.8) ** 2)
    wh = np.fft.irfft(X, m)
    tt = np.linspace(0, 1, m)
    wh *= np.where(tt < 0.8, (tt / 0.8) ** 2, ((1 - tt) / 0.2))
    wh = wh / np.abs(wh).max() * 0.12
    out = np.concatenate([cold, a])
    j = n - int(0.4 * sr)
    out[j:j + m] += np.stack([wh, np.roll(wh, 40)], 1)
    pk = np.abs(out).max()
    if pk > 0.98:
        out *= 0.98 / pk
    o = wave.open(path, "wb")
    o.setnchannels(ch); o.setsampwidth(2); o.setframerate(sr)
    o.writeframes((out * 32767).astype(np.int16).tobytes())
    o.close()


if __name__ == "__main__":
    out = sys.argv[1]
    if len(sys.argv) > 2:
        for j in (0, 6, 20, 47):
            Image.fromarray(cold_frame(j)).save(f"../nad/hook_{j:02d}.jpg", quality=90)
        sys.exit()
    wav = out + ".wav"
    audio(wav)
    n = NC + int(DUR * FPS)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    master = out + ".master.mp4"
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-tune", "film",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", "-shortest", master]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for k, b in enumerate(pool.imap(frame_bytes, range(n), chunksize=6)):
            p.stdin.write(b)
            if k % 120 == 0:
                print(f"{k}/{n}", flush=True)
    p.stdin.close(); p.wait()
    for ps in (1, 2):
        c = [ff, "-v", "error", "-y", "-i", master, "-c:v", "libx264", "-preset", "veryslow", "-b:v", "7000k",
             "-maxrate", "9000k", "-bufsize", "14000k", "-pix_fmt", "yuv420p", "-pass", str(ps), "-passlogfile", out + ".p2"]
        c += (["-an", "-f", "mp4", "/dev/null"] if ps == 1 else
              ["-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out])
        subprocess.run(c, check=True)
    print("done", out)
