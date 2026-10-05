"""Soundtrack for 'Kiriman untuk Nenek': the Pixabay piano track (swell on the photo reveal),
light kampung ambience, and Foley/UI accents tuned to the track's G major."""
import wave
import numpy as np
from nk_time import *

SR = 44100
N = int(DUR * SR)
rng = np.random.default_rng(11)


def T(d):
    return np.arange(int(d * SR)) / SR


def fft_filter(x, lo=None, hi=None, order=2):
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if hi:
        m *= 1 / np.sqrt(1 + (f / hi) ** (2 * order))
    if lo:
        m *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (2 * order))
    if X.ndim == 2:
        m = m[:, None]
    return np.fft.irfft(X * m, len(x), axis=0)


def noise(d):
    return rng.standard_normal(int(d * SR))


def env(d, tau, attack=0.002):
    t = T(d)
    e = np.exp(-t / tau)
    a = max(1, int(attack * SR))
    e[:a] *= np.linspace(0, 1, a)
    return e


def place(bus, sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i + len(sig) <= 0:
        return
    if sig.ndim == 1:
        sig = np.stack([sig * np.cos((pan + 1) * np.pi / 4), sig * np.sin((pan + 1) * np.pi / 4)], 1) * 1.414
    if i < 0:
        sig, i = sig[-i:], 0
    n = min(len(sig), N - i)
    bus[i:i + n] += sig[:n] * gain


def reverb(x, secs=2.2, decay=3.0, lo=200, hi=6500):
    n = int(secs * SR)
    t = np.arange(n) / SR
    out = np.zeros_like(x)
    L = len(x) + n
    nfft = 1 << (L - 1).bit_length()
    for c in range(2):
        ir = fft_filter(rng.standard_normal(n) * np.exp(-t * decay), lo, hi)
        ir[:int(0.015 * SR)] = 0
        ir /= np.sqrt(np.sum(ir ** 2))
        out[:, c] = np.fft.irfft(np.fft.rfft(x[:, c], nfft) * np.fft.rfft(ir, nfft), nfft)[:len(x)]
    return out


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def bell(m, d=2.0, bright=1.0):
    t = T(d)
    f = midi(m)
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 2.2) + 0.45 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 4)
         + 0.18 * bright * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t * 7))
    s[:200] *= np.linspace(0, 1, 200)
    return s


amb = np.zeros((N, 2))
fx = np.zeros((N, 2))       # dry Foley
ui = np.zeros((N, 2))       # UI accents (get reverb)

# ---------------- ambience: after-rain kampung (outdoor until the door opens, softer at the doorstep)
bed = fft_filter(noise(DUR), 150, 1800)
bed = bed / np.abs(bed).max()
lvl = np.interp(np.arange(N) / SR, [0, 0.6, 11.4, 12.2, FOOT_END, DUR], [0, 0.020, 0.020, 0.011, 0.009, 0.0])
amb += np.stack([bed * lvl, np.roll(bed, 3000) * lvl], 1)
for t0 in np.arange(0.4, FOOT_END, 0.9):                          # birds, sparse and far
    if rng.random() < 0.55:
        tt = T(0.09)
        f0 = rng.uniform(3200, 4600)
        chirp = np.sin(2 * np.pi * (f0 + 1800 * tt / 0.09) * tt) * np.sin(np.pi * tt / 0.09) ** 2
        for r in range(rng.integers(1, 4)):
            place(amb, chirp, t0 + r * 0.12 + rng.uniform(0, 0.3),
                  0.012 if t0 < 11.4 else 0.006, rng.uniform(-0.8, 0.8))
for t0 in rng.uniform(0.2, 11.0, 14):                              # last drips from the roofs
    tt = T(0.05)
    f0 = rng.uniform(900, 1700)
    drip = np.sin(2 * np.pi * f0 * (1 + 0.6 * tt / 0.05) * tt) * np.exp(-tt * 70)
    place(amb, drip, t0, 0.02, rng.uniform(-0.9, 0.9))
mb = fft_filter(noise(3.2), 60, 500)                               # a motorbike passing a street away
tt = T(3.2)
mb *= np.sin(np.pi * tt / 3.2) ** 2 * (1 + 0.3 * np.sin(2 * np.pi * 22 * tt))
place(amb, mb / np.abs(mb).max(), 3.6, 0.03, -0.4)

# ---------------- hook: soft two-tone error
for k, m in enumerate([76, 72]):
    tt = T(0.22)
    s = np.sin(2 * np.pi * midi(m) * tt) + 0.25 * np.sign(np.sin(2 * np.pi * midi(m) * tt))
    place(ui, s * env(0.22, 0.07, 0.004), NOTIF_T + 0.12 + k * 0.13, 0.05)

# ---------------- note: paper slide-in
sw = fft_filter(noise(0.35), 1500, 7000) * np.sin(np.pi * T(0.35) / 0.35) ** 1.5
place(fx, sw, NOTE_IN, 0.035, -0.5)
place(fx, fft_filter(noise(0.3), 1500, 7000) * np.sin(np.pi * T(0.3) / 0.3) ** 1.5, NOTE_OUT - 0.4, 0.025, -0.5)

# ---------------- clue ticks: pen stroke + a rising G-major bell (B5, D6, G6)
for tk, m in zip(TICKS, [83, 86, 91]):
    pen = fft_filter(noise(0.18), 2500, 9000) * np.interp(T(0.18), [0, 0.03, 0.12, 0.18], [0, 1, 0.6, 0])
    place(fx, pen, tk, 0.03, -0.4)
    place(ui, bell(m, 1.6), tk + 0.06, 0.06)

# ---------------- knocks, latch, door creak
for kt in KNOCKS:
    tt = T(0.16)
    knock = (np.sin(2 * np.pi * 180 * tt) * 0.8 + fft_filter(noise(0.16), 300, 2500) * 0.5) * np.exp(-tt * 38)
    place(fx, knock, kt, 0.16, 0.3)
tt = T(0.06)
place(fx, fft_filter(noise(0.06), 1500, 8000) * np.exp(-tt * 90), LATCH_T, 0.06, 0.3)
tt = T(0.8)
fcr = 420 + 180 * np.sin(2 * np.pi * 1.3 * tt) + 60 * np.sin(2 * np.pi * 7 * tt)
creak = np.sin(2 * np.pi * np.cumsum(fcr) / SR) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 38 * tt))) * 0.5
creak = fft_filter(creak, 250, 2600) * np.sin(np.pi * tt / 0.8) ** 2
place(fx, creak, CREAK_T, 0.03, 0.3)

# ---------------- delivered: bright ding (D6 over G)
place(ui, bell(86, 2.2) + 0.6 * bell(91, 2.2), BADGE_T, 0.07)

# ---------------- his steps leaving + cardboard flaps opening
for k, st in enumerate(np.arange(15.25, 16.7, 0.48)):
    tt = T(0.12)
    step = fft_filter(noise(0.12), 120, 1600) * np.exp(-tt * 40)
    place(fx, step, st, 0.05 * (1 - k * 0.15), -0.6)
for k in range(5):
    d = rng.uniform(0.15, 0.3)
    rs = fft_filter(noise(d), 600, 5000) * np.sin(np.pi * T(d) / d)
    place(fx, rs, RUSTLE_T + k * 0.27 + rng.uniform(0, 0.08), 0.05, 0.1)

# ---------------- a soft rising shimmer into the swell (the photo reveal)
d = 1.3
tt = T(d)
sh = fft_filter(noise(d), 3000, 11000) * (tt / d) ** 3
place(ui, sh, REVEAL_T - d, 0.03)

# ---------------- end: logo ting-tong, doorbell timbre resolving to G
for k, m in enumerate([86, 79]):
    place(ui, bell(m, 2.6), CARD_T + k * 0.31, 0.085)

# ---------------- music
f = wave.open("track_piano.wav")
trk = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32).reshape(-1, f.getnchannels()) / 32768
if trk.shape[1] == 1:
    trk = np.repeat(trk, 2, 1)
j0 = int(OFF * SR)
seg = trk[j0:j0 + N].astype(np.float64)
seg = np.pad(seg, ((0, N - len(seg)), (0, 0)))
tt = np.arange(N) / SR
gain = np.interp(tt, [0, 0.5, DUR - 2.2, DUR], [0, 1, 1, 0])
seg *= gain[:, None]

mix = seg * 0.62 + amb + fx + ui * 0.85 + reverb(ui) * 0.35
peak = np.abs(mix).max()
mix = mix / peak * 0.97
out = (mix * 32767).astype(np.int16)
w = wave.open("audio_nenek.wav", "wb")
w.setnchannels(2)
w.setsampwidth(2)
w.setframerate(SR)
w.writeframes(out.tobytes())
w.close()
print("audio_nenek.wav", DUR, "s  peak", round(float(peak), 3))
