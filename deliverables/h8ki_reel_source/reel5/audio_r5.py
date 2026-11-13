"""Sound for Reel #5: one continuous take of the Pixabay piano (already in Hoki's library), placed so its swell
(track 50.74 s) lands on the map; the real sound of the three clips underneath; unpitched stamps, ticks, whooshes
and sparkles on the graphics (they cannot clash with the piano's key).
MUSIC=0 writes the version without the piano (for a trending sound added in the Instagram app)."""
import os, wave
import numpy as np
import render_r5 as V

MUSIC = os.environ.get("MUSIC", "1") == "1"
SR, DUR = 48000, V.DUR
N = int(SR * DUR)
rng = np.random.default_rng(7)
mix = np.zeros((N, 2))


def T(d):
    return np.arange(int(d * SR)) / SR


def put(sig, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N:
        return
    if sig.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l, sig * r], 1) * 1.414
    sig = sig[:N - i]
    mix[i:i + len(sig)] += sig * g


def lp(x, fc):
    X = np.fft.rfft(x, axis=0); f = np.fft.rfftfreq(len(x), 1 / SR)
    m = 1 / np.sqrt(1 + (f / fc) ** 4)
    return np.fft.irfft(X * (m[:, None] if x.ndim == 2 else m), len(x), axis=0)


def hp(x, fc):
    X = np.fft.rfft(x, axis=0); f = np.fft.rfftfreq(len(x), 1 / SR)
    m = 1 / np.sqrt(1 + (fc / np.maximum(f, 1)) ** 4)
    return np.fft.irfft(X * (m[:, None] if x.ndim == 2 else m), len(x), axis=0)


def noise(d):
    return rng.standard_normal(int(d * SR))


def wavread(p):
    w = wave.open(p)
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float64) / 32768


# ---------------- music
if MUSIC:
    trk = wavread("../music/piano.wav")
    i0 = int(V.OFF * SR)
    seg = trk[i0:i0 + N].copy()
    tt = np.arange(len(seg)) / SR
    g = np.interp(tt, [0, 0.06, 7.9, 8.4, 12.9, 13.4, DUR - 1.8, DUR],
                  [0, 0.72, 0.72, 1.0, 1.0, 0.82, 0.82, 0.0])
    put(seg * g[:, None], 0.0, 1.0)

# ---------------- the real place underneath (each piece levelled, short crossfades)
CLIP = {c: wavread(f"../aud/{c}.wav") for c in "ABC"}


def amb(c, s0, t0, t1, g):
    x = CLIP[c][int(s0 * SR):int(s0 * SR) + int((t1 - t0) * SR)].copy()
    x = hp(x, 90)
    rms = np.sqrt((x ** 2).mean()) + 1e-9
    x *= 0.03 / rms
    n = len(x); f = int(0.04 * SR)
    env = np.ones(n); env[:f] = np.linspace(0, 1, f); env[-f:] = np.linspace(1, 0, f)
    put(x * env[:, None], t0, g)


AG = 0.55 if MUSIC else 1.0
amb("C", 5.0, 0.0, 2.32, AG)
amb("A", 3.0, 2.26, 5.04, AG)
amb("B", 0.0, 4.96, 6.40, AG)
amb("B", 2.2, 6.32, 8.45, AG)
amb("C", 6.3, 13.12, DUR, AG * 0.9)
air = lp(hp(noise(4.9), 150), 900)                    # the map: a soft room of air
fa = np.minimum(1, T(4.9) / 0.3) * np.minimum(1, (4.9 - T(4.9)) / 0.3)
put(air / np.abs(air).max() * fa, V.T_MAP, 0.03)


# ---------------- graphics
def thump(f0=55, d=0.35, dec=9):
    tt = T(d)
    return lp(np.sin(2 * np.pi * f0 * tt * (1 + 0.6 * np.exp(-tt * 30))) * np.exp(-tt * dec), 260)


def click(d=0.03, fc=2200):
    return hp(noise(d), fc) * np.exp(-T(d) * 180)


def whoosh(d, rise=True, lo=500, hi=4500):
    tt = T(d)
    env = (tt / d) ** 2 if rise else np.sin(np.pi * tt / d) ** 2
    return hp(lp(noise(d), hi), lo) * env


def sparkle(d, rate=23):
    tt = T(d)
    return hp(noise(d), 6000) * (0.5 + 0.5 * np.sin(2 * np.pi * rate * tt)) * np.exp(-tt * 5)


def pop_snd():
    return lp(hp(noise(0.05), 800), 3200) * np.exp(-T(0.05) * 90)


# hook stamps
for t0, g in ((0.0, 1.0), (0.42, 0.9), (0.95, 0.8)):
    put(thump(52), t0 + 0.01, 0.42 * g)
    put(click(), t0 + 0.01, 0.12 * g)
    put(hp(lp(noise(0.12), 5000), 900) * np.exp(-T(0.12) * 30), t0, 0.05 * g)
# hook -> montage punch
put(whoosh(0.32), 2.28 - 0.32, 0.09, -0.2)
put(thump(48, 0.45, 7), 2.28, 0.4)
# the clock ticks through the day (half-beats), then the "done" hit
t = 2.28 + 0.34
while t < V.T_C1 - 0.05:
    tt = T(0.025)
    put(hp(noise(0.025), 3000) * np.exp(-tt * 260), t, 0.05, 0.25)
    t += 0.34
put(thump(50, 0.5, 7), V.T_C1, 0.35)
put(sparkle(1.0), V.T_C1 + 0.02, 0.05, 0.2)
# cuts inside the montage
for tc in (5.0, 6.36):
    put(whoosh(0.18, False, 800, 5000), tc - 0.09, 0.05)
# checks
for _, ti in V.CHECKS:
    put(pop_snd(), ti + 0.02, 0.16, -0.3)
    put(sparkle(0.45), ti + 0.04, 0.03, -0.3)
# dive into the cartons -> the map
put(whoosh(0.45, True, 300, 6000), V.T_MAP - 0.45, 0.13)
put(thump(42, 0.9, 4), V.T_MAP, 0.35)
put(sparkle(1.5, 17), V.T_MAP + 0.02, 0.04)
# arcs: a soft launch per island, sparkles where the dots land
for name, lab, ta, dests in V.ISLANDS:
    pan = {"JAWA": 0.3, "SUMATERA": -0.6, "KALIMANTAN": 0.6}[name]
    put(whoosh(0.6, False, 700, 5000), ta, 0.05, pan)
    for j in range(len(dests)):
        tt = T(0.04)
        put(hp(noise(0.04), 4000) * np.exp(-tt * 120), ta + j * 0.09 + V.ARC_DUR, 0.05, pan)
    put(sparkle(0.6), ta + V.ARC_DUR, 0.035, pan)
# pill + stat tiles
put(pop_snd(), 11.27, 0.14)
for j in range(3):
    put(pop_snd(), 11.57 + j * 0.17, 0.13, (j - 1) * 0.4)
# dive back into the yard
put(whoosh(0.4, True, 300, 6000), 13.16 - 0.4, 0.1)
put(thump(46, 0.6, 6), 13.16, 0.28)
# closing
for k, tt0 in enumerate((0.15, 0.45, 0.85, 1.1)):
    put(pop_snd(), V.T_END + tt0 + 0.02, 0.12)
put(sparkle(1.4), V.T_END + 0.47, 0.03)

# ---------------- master
mix = np.tanh(mix * 1.4) / 1.4
mix *= 0.89 / np.abs(mix).max()
out = "audio_r5.wav" if MUSIC else "audio_r5_sfx.wav"
w = wave.open(out, "wb")
w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((mix * 32767).astype(np.int16).tobytes())
w.close()
print(out, DUR)
