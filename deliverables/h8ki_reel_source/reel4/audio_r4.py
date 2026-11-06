"""Original soundtrack for Reel #4, synthesized from scratch (no samples): the hook (phone buzz + GPS error), a light
marimba groove while he finds the way (Am - F - G, C when Nenek takes the parcel), soft piano and a warm pad for the
photo, kampung ambience and foley throughout, a two-note logo chime. Beat = 0.6 s, the same grid as the cuts.
MUSIC=0 writes the sound-effects-only version (for a trending sound added in the Instagram app)."""
import os, wave
import numpy as np
MUSIC = os.environ.get("MUSIC", "1") == "1"   # MUSIC=0: sound effects only, for a trending sound added in the app

SR, DUR = 48000, 15.7
N = int(SR * DUR)
BEAT = 0.6
rng = np.random.default_rng(3)
mix = np.zeros((N, 2))


def T(d):
    return np.arange(int(d * SR)) / SR


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def put(sig, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N:
        return
    sig = sig[:N - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    mix[i:i + len(sig), 0] += sig * g * l * 1.414
    mix[i:i + len(sig), 1] += sig * g * r * 1.414


def lp(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (f / fc) ** 4), len(x))


def hp(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (fc / np.maximum(f, 1)) ** 4), len(x))


def marimba(m, d=0.9):
    t = T(d); f = hz(m)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 7) + 0.35 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 28)
    s[:120] *= np.linspace(0, 1, 120)
    return s


def bell(m, d=1.6):
    t = T(d); f = hz(m)
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 2.6) + 0.4 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 4.5)
         + 0.15 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t * 8))
    s[:150] *= np.linspace(0, 1, 150)
    return s


def bass(m, d=0.55):
    t = T(d); f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.2 * np.sin(2 * np.pi * 2 * f * t)
    e = np.minimum(1, t / 0.01) * np.exp(-t * 3.5)
    return s * e


def pad(ms, d):
    t = T(d); s = np.zeros_like(t)
    for m in ms:
        for det in (-0.08, 0.08):
            s += np.sin(2 * np.pi * hz(m + det) * t + rng.uniform(0, 6))
    e = np.minimum(1, t / 0.6) * np.minimum(1, (d - t) / 0.8)
    return lp(s * e / len(ms), 1800)



def piano(m, d=2.4, vel=1.0):
    t = T(d); f = hz(m)
    s = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (1.6 + 1.4 * k)) for k, a in ((1, 1.0), (2, 0.45), (3, 0.2), (4, 0.08)))
    s[:200] *= np.linspace(0, 1, 200)
    return lp(s * vel, 3500)


# ---------------- 0 - 1.3 s: the hook. phone buzz, the GPS error two-tone, a whoosh as the app slides in
for t0 in (0.0, 0.3):
    tt = T(0.2)
    bz = (np.sign(np.sin(2 * np.pi * 150 * tt)) * 0.6 + np.sin(2 * np.pi * 300 * tt) * 0.4) * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * tt))
    put(lp(bz * np.minimum(1, tt / 0.01) * np.clip((0.2 - tt) / 0.03, 0, 1), 1200), t0, 0.12)
for k, m in enumerate([76, 72]):
    tt = T(0.22)
    s = np.sin(2 * np.pi * hz(m) * tt) + 0.25 * np.sign(np.sin(2 * np.pi * hz(m) * tt))
    put(lp(s * np.exp(-tt / 0.07), 4000), 0.08 + k * 0.14, 0.09)
tt = T(0.5)
put(hp(lp(rng.standard_normal(len(tt)), 3500), 400) * np.sin(np.pi * tt / 0.5) ** 2, 1.35, 0.06, -0.2)

if MUSIC:
    # ---------------- 1.2 - 11.4 s: light marimba groove (Am - F - G, C when she takes the parcel, F)
    CH = [(1.2, [57, 60, 64], 45), (3.0, [53, 57, 60], 41), (5.4, [55, 59, 62], 43), (7.2, [60, 64, 67], 48),
          (9.6, [53, 57, 60], 41)]
    ARP = [0, 1, 2, 1, 2, 3, 2, 1]
    for ci, (t0, tri, root) in enumerate(CH):
        t_end = CH[ci + 1][0] if ci + 1 < len(CH) else 11.4
        notes = tri + [tri[0] + 12]
        k = 0
        while t0 + k * BEAT / 2 < t_end - 1e-6:
            put(marimba(notes[ARP[k % 8]] + 12), t0 + k * BEAT / 2, 0.2 if k % 2 == 0 else 0.14, -0.3 + 0.6 * (k % 2))
            k += 1
        for bb in (0, 2):
            if t0 + bb * BEAT < t_end - 1e-6:
                put(bass(root), t0 + bb * BEAT, 0.3)
    t = 1.2 + BEAT / 2
    while t < 11.4:
        tt = T(0.06)
        put(hp(rng.standard_normal(len(tt)), 6000) * np.exp(-tt * 70), t, 0.045, 0.4)
        t += BEAT
    t = 3.0 + BEAT
    while t < 9.6:
        tt = T(0.12)
        put(lp(hp(rng.standard_normal(len(tt)), 900), 5000) * np.exp(-tt * 35), t, 0.08, -0.1)
        t += 2 * BEAT
    put(pad([60, 64, 67, 72], 3.0), 7.2, 0.08)
    # ---------------- 11.4 - 14.4 s: the photo. the groove stops, soft piano and a warm pad carry it
    for t0, chord in [(11.4, [57, 60, 64, 69]), (12.6, [53, 57, 60, 65]), (13.8, [55, 59, 62, 67])]:
        for j, m in enumerate(chord):
            put(piano(m, 2.6, 0.9 if j == 0 else 0.6), t0 + j * 0.06, 0.16, -0.3 + 0.2 * j)
    put(pad([57, 64, 69, 72], 3.4), 11.3, 0.10)

# ---------------- ambience: a kampung at golden hour after rain (both versions)
amb_end = 14.8
na = int(amb_end * SR)
ta = np.arange(na) / SR
fade = np.minimum(1, ta / 0.4) * np.clip((amb_end - ta) / 0.5, 0, 1)
air = lp(hp(rng.standard_normal(na), 200), 1200)
air = air / np.abs(air).max()
put(air * fade * (0.8 + 0.2 * np.sin(2 * np.pi * 0.2 * ta)), 0.0, 0.035, -0.1)
t = 0.4
while t < amb_end - 0.5:                             # sparse birds
    tt = T(0.09)
    f0 = rng.uniform(3200, 4600)
    chirp = np.sin(2 * np.pi * (f0 + 1600 * tt / 0.09) * tt) * np.sin(np.pi * tt / 0.09) ** 2
    for r in range(int(rng.integers(1, 4))):
        put(chirp, t + r * 0.12, 0.018, float(rng.uniform(-0.8, 0.8)))
    t += rng.uniform(0.7, 1.4)
for t0 in rng.uniform(0.3, 13.5, 12):                # last drips from the roofs
    tt = T(0.05)
    put(np.sin(2 * np.pi * rng.uniform(900, 1700) * (1 + 0.6 * tt / 0.05) * tt) * np.exp(-tt * 70), t0, 0.02, float(rng.uniform(-0.9, 0.9)))
tt = T(2.4)                                          # a motorbike a street away
f0 = 85 + 25 * tt / 2.4
eng = np.sign(np.sin(2 * np.pi * np.cumsum(f0) / SR)) * 0.5 + lp(rng.standard_normal(len(tt)), 600) * 0.5
eng = lp(eng, 900) * np.sin(np.pi * tt / 2.4) ** 2
put(eng / np.abs(eng).max(), 3.4, 0.025, -0.6)


# ---------------- foley
def step():
    tt = T(0.09)
    return lp(rng.standard_normal(len(tt)), 400) * np.exp(-tt * 45) + hp(rng.standard_normal(len(tt)), 2500) * np.exp(-tt * 60) * 0.35


def creak(d, f_lo, f_hi):
    tt = T(d)
    f = f_lo + (f_hi - f_lo) * (0.5 + 0.5 * np.sin(2 * np.pi * 1.1 * tt)) + 30 * np.sin(2 * np.pi * 9 * tt)
    c = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 34 * tt)))
    return lp(hp(c, 250), 2600) * np.sin(np.pi * tt / d) ** 2


for k in range(6):                                   # his footsteps on the wet path
    put(step(), 3.05 + k * 0.4, 0.12, 0.15 if k % 2 else -0.15)
for kt in (5.9, 6.15, 6.38):                         # knocks on the wooden door
    tt = T(0.16)
    put((np.sin(2 * np.pi * 180 * tt) * 0.8 + lp(hp(rng.standard_normal(len(tt)), 300), 2500) * 0.5) * np.exp(-tt * 38), kt, 0.16, 0.3)
tt = T(0.06)
put(lp(hp(rng.standard_normal(len(tt)), 1500), 8000) * np.exp(-tt * 90), 7.25, 0.06, 0.3)    # latch
put(creak(0.7, 380, 560), 7.32, 0.035, 0.3)          # the door opens
for k in range(6):                                   # cardboard: she opens the box
    L = rng.uniform(0.06, 0.12); tt = T(L)
    put(lp(hp(rng.standard_normal(len(tt)), 700), 4000) * np.sin(np.pi * tt / L) ** 1.5, 10.4 + k * 0.16 + rng.uniform(0, 0.05), 0.07, 0.1)

# ---------------- UI pings, delivered chime, punchline pops, the photo shimmer, asks
for t, m in [(2.2, 76), (3.0, 79), (5.4, 81)]:
    tt = T(0.25)
    put(np.sin(2 * np.pi * hz(m) * tt) * np.exp(-tt * 18) + 0.3 * np.sin(2 * np.pi * hz(m + 12) * tt) * np.exp(-tt * 30), t, 0.13)
for k, m in enumerate([84, 88, 91, 96]):
    put(bell(m, 1.4), 7.2 + k * 0.075, 0.07)
for t in (7.35, 7.95):
    tt = T(0.08)
    put(np.sin(2 * np.pi * 180 * tt) * np.exp(-tt * 50), t, 0.12)
for k, m in enumerate([88, 91, 96, 100]):            # the photo comes out
    put(bell(m, 1.8), 11.5 + k * 0.11, 0.045)
for t, m in [(12.6, 84), (13.15, 88)]:
    tt = T(0.12)
    put(np.sin(2 * np.pi * hz(m) * (1 + 0.5 * tt / 0.12) * tt) * np.exp(-tt * 30), t, 0.07)
tt = T(0.45)
put(hp(lp(rng.standard_normal(len(tt)), 2500), 300) * np.sin(np.pi * tt / 0.45) ** 2, 14.35, 0.035)

# ---------------- logo: two-note chime and a ringing chord
put(bell(79, 1.4), 14.7, 0.10)
put(bell(84, 1.2), 14.92, 0.10)
for m in ((48, 60, 64, 67, 72) if MUSIC else ()):
    put(marimba(m, 1.0) if m > 50 else bass(m, 1.0), 14.7, 0.15)

# ---------------- master
mix = np.tanh(mix * 1.6) / 1.6
fo = int(0.3 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
mix *= 0.89 / np.abs(mix).max()
out = "audio_r4.wav" if MUSIC else "audio_r4_sfx.wav"
w = wave.open(out, "wb")
w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((mix * 32767).astype(np.int16).tobytes())
w.close()
print(out, DUR)
