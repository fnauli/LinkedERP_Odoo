"""Sound for "MISI KURIR #1" v2: ONE continuous piece of music (Pixabay "piano background music", Pixabay Content
License, already in Hoki's library), cut so its swell (track 50.74 s) lands on the photo, under soft unpitched
game sounds (they cannot clash with the piano's key), kampung ambience and foley on the measured frames.
MUSIC=0 writes the version without the piano (for a trending sound added in the Instagram app)."""
import os, wave
import numpy as np
import render_misi2 as V

MUSIC = os.environ.get("MUSIC", "1") == "1"
SR, DUR = 48000, V.DUR
N = int(SR * DUR)
rng = np.random.default_rng(5)
mix = np.zeros((N, 2))
st = V.st


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


# ---------------- music: one take of the piano, swell on the photo
if MUSIC:
    w = wave.open("../music/piano.wav")
    trk = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float64) / 32768
    i0 = int(V.OFF * SR)
    seg = trk[i0:i0 + N].copy()
    tt = np.arange(len(seg)) / SR
    # gentle under the story, full from the box opening (the track itself swells on the photo), long fade at the end
    g = np.interp(tt, [0, 0.25, 5.25, 5.4, 6.4, 6.7, 9.6, 10.6, DUR - 1.6, DUR], [0, 0.62, 0.62, 0.45, 0.45, 0.62, 0.62, 1.0, 1.0, 0.0])   # dip under the knocks
    put(seg * g[:, None], 0.0, 1.0)

# ---------------- hook: the mission card lands (soft whoosh, click, low thump) + a GPS "glitch"
s = hp(lp(noise(0.35), 4000), 600) * np.linspace(0, 1, int(0.35 * SR)) ** 2
put(s, 0.0, 0.05, -0.2)
tt = T(0.3)
put(lp(np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 10), 250), 0.02, 0.22)
tt = T(0.03)
put(hp(noise(0.03), 2000) * np.exp(-tt * 200), 0.02, 0.08)
for k in range(2):                                   # unpitched digital glitch for "alamat tidak ditemukan"
    d = 0.09
    gl = hp(noise(d), 1500) * (np.sign(np.sin(2 * np.pi * 37 * T(d))) * 0.5 + 0.5)
    put(lp(gl, 6000) * np.exp(-T(d) * 18), 0.45 + k * 0.13, 0.05, 0.3)
put(hp(lp(noise(0.4), 3500), 500) * np.sin(np.pi * T(0.4) / 0.4) ** 2, V.HUD_IN - 0.05, 0.035, -0.3)


def sparkle(d, g):
    tt = T(d)
    s = hp(noise(d), 6000) * (0.5 + 0.5 * np.sin(2 * np.pi * 23 * tt)) * np.exp(-tt * 5)
    return s * g


for _, ti in V.M.OBJ:                                # each objective: soft pop + sparkle
    tt = T(0.05)
    put(lp(hp(noise(0.05), 800), 3000) * np.exp(-tt * 90), ti + 0.02, 0.12)
    put(sparkle(0.5, 1.0), ti + 0.04, 0.03, 0.2)
tt = T(0.9)                                          # MISI SELESAI: a rising shimmer and a warm thump
put(hp(noise(0.9), 3000) * (tt / 0.9) ** 2 * np.exp(-np.maximum(0, tt - 0.7) * 20), V.T_GIVE - 0.75, 0.035)
put(lp(np.sin(2 * np.pi * 50 * T(0.5)) * np.exp(-T(0.5) * 7), 200), V.T_GIVE + 0.05, 0.25)
put(sparkle(1.2, 1.0), V.T_GIVE + 0.05, 0.04, -0.2)
put(sparkle(1.6, 1.0), V.T_REVEAL, 0.02, 0.0)        # a breath of air as the photo comes out

# ---------------- ambience: kampung at golden hour (fades as the closing card comes)
amb_end = V.END_T + 0.8
na = int(amb_end * SR)
ta = np.arange(na) / SR
fade = np.minimum(1, ta / 0.4) * np.clip((amb_end - ta) / 1.0, 0, 1)
air = lp(hp(noise(amb_end), 200), 1200)
put(air / np.abs(air).max() * fade, 0.0, 0.03, -0.1)
t = 0.4
while t < amb_end - 0.6:
    tt = T(0.09)
    f0 = rng.uniform(3200, 4600)
    chirp = np.sin(2 * np.pi * (f0 + 1600 * tt / 0.09) * tt) * np.sin(np.pi * tt / 0.09) ** 2
    for r in range(int(rng.integers(1, 3))):
        put(chirp, t + r * 0.12, 0.012, float(rng.uniform(-0.8, 0.8)))
    t += rng.uniform(0.9, 1.6)


# ---------------- foley on the measured frames
def step():
    tt = T(0.09)
    return lp(noise(0.09), 400) * np.exp(-tt * 45) + hp(noise(0.09), 2500) * np.exp(-tt * 60) * 0.35


def creak(d, f_lo, f_hi):
    tt = T(d)
    f = f_lo + (f_hi - f_lo) * (0.5 + 0.5 * np.sin(2 * np.pi * 1.1 * tt)) + 30 * np.sin(2 * np.pi * 9 * tt)
    c = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 34 * tt)))
    return lp(hp(c, 250), 2600) * np.sin(np.pi * tt / d) ** 2


for k, sf in enumerate((160, 172, 183, 194)):
    put(step(), st("k1", sf), 0.13, 0.15 if k % 2 else -0.15)
for sf in (238, 247, 251):
    tt = T(0.16)
    put((np.sin(2 * np.pi * 180 * tt) * 0.8 + lp(hp(noise(0.16), 300), 2500) * 0.5) * np.exp(-tt * 38), st("k1", sf), 0.26, 0.3)
tt = T(0.06)
put(lp(hp(noise(0.06), 1500), 8000) * np.exp(-tt * 90), st("k1", 275), 0.06, 0.3)
put(creak(0.75, 380, 560), st("k1", 276), 0.03, 0.3)
t = st("k2", 48)
while t < st("k2", 70):
    L = rng.uniform(0.06, 0.12); tt = T(L)
    put(lp(hp(noise(L), 700), 4000) * np.sin(np.pi * tt / L) ** 1.5, t, 0.06, 0.1)
    t += rng.uniform(0.12, 0.2)

# ---------------- master
mix = np.tanh(mix * 1.4) / 1.4
mix *= 0.89 / np.abs(mix).max()
out = "audio_misi2.wav" if MUSIC else "audio_misi2_sfx.wav"
w = wave.open(out, "wb")
w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((mix * 32767).astype(np.int16).tobytes())
w.close()
print(out, DUR)
