"""Original soundtrack for Reel #4 "MISI KURIR #1" (synthesized, no samples). Helpers below; cues further down. Was: the hook (phone buzz + GPS error), a light
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


import render_misi as M                              # every cue is placed on a measured source frame
st = M.src_time


def square(m, d, decay=10.0):
    t = T(d); f = hz(m)
    s = np.sign(np.sin(2 * np.pi * f * t)) * 0.5 + np.sin(2 * np.pi * f * t) * 0.5
    s = lp(s * np.exp(-t * decay), 5000)
    s[:100] *= np.linspace(0, 1, 100)
    return s


# ---------------- hook: "quest start" jingle + the GPS error as the red chip lands
for k, m in enumerate([72, 76, 79, 84]):
    put(square(m, 0.35, 9), 0.0 + k * 0.07, 0.07, -0.2 + 0.13 * k)
tt = T(0.25)
put(lp(np.sin(2 * np.pi * 60 * tt) * np.exp(-tt * 12), 300), 0.0, 0.25)          # low "whomp"
for k, m in enumerate([76, 72]):
    tt = T(0.22)
    s = np.sin(2 * np.pi * hz(m) * tt) + 0.25 * np.sign(np.sin(2 * np.pi * hz(m) * tt))
    put(lp(s * np.exp(-tt / 0.07), 4000), 0.45 + k * 0.14, 0.08)
tt = T(0.4)                                          # the card hands over to the HUD
put(hp(lp(rng.standard_normal(len(tt)), 3500), 500) * np.sin(np.pi * tt / 0.4) ** 2, M.HUD_IN - 0.05, 0.05, -0.3)

if MUSIC:
    # ---------------- the quest: bouncy marimba groove (Am - F - G - C), stops when the mission is done
    CH = [(1.2, [57, 60, 64], 45), (3.0, [53, 57, 60], 41), (5.0, [55, 59, 62], 43), (7.0, [55, 59, 62], 43)]
    ARP = [0, 1, 2, 1, 2, 3, 2, 1]
    for ci, (t0, tri, root) in enumerate(CH):
        t_end = CH[ci + 1][0] if ci + 1 < len(CH) else M.T_DONE
        notes = tri + [tri[0] + 12]
        k = 0
        while t0 + k * BEAT / 2 < t_end - 1e-6:
            put(marimba(notes[ARP[k % 8]] + 12), t0 + k * BEAT / 2, 0.2 if k % 2 == 0 else 0.14, -0.3 + 0.6 * (k % 2))
            k += 1
        for bb in (0, 2):
            if t0 + bb * BEAT < t_end - 1e-6:
                put(bass(root), t0 + bb * BEAT, 0.3)
    t = 1.2 + BEAT / 2
    while t < M.T_DONE:
        tt = T(0.06)
        put(hp(rng.standard_normal(len(tt)), 6000) * np.exp(-tt * 70), t, 0.045, 0.4)
        t += BEAT
    # mission complete: a short major fanfare, then a warm C chord rings into the quiet
    for k, m in enumerate([72, 76, 79, 84, 88]):
        put(square(m, 0.6 if k < 4 else 1.4, 4 if k < 4 else 2.2), M.T_DONE + k * 0.09, 0.06)
    put(pad([60, 64, 67, 72], 2.4), M.T_DONE, 0.09)
    # the real reward: soft piano and a pad, no game sounds
    for t0, chord in [(10.2, [57, 60, 64, 69]), (11.6, [53, 57, 60, 65]), (13.0, [48, 55, 60, 64])]:
        for j, m in enumerate(chord):
            put(piano(m, 2.8, 0.9 if j == 0 else 0.6), t0 + j * 0.06, 0.16, -0.3 + 0.2 * j)
    put(pad([57, 64, 69, 72], 4.4), 10.1, 0.10)
else:
    for k, m in enumerate([72, 76, 79, 84, 88]):     # keep the "mission complete" sting in the SFX version too
        put(square(m, 0.6 if k < 4 else 1.2, 4 if k < 4 else 2.4), M.T_DONE + k * 0.09, 0.05)

# ---------------- objectives: a coin-like tick on each check
for _, ti in M.OBJ:
    put(square(83, 0.12, 25), ti + 0.02, 0.06)
    put(square(88, 0.4, 9), ti + 0.09, 0.06)

# ---------------- ambience: kampung at golden hour (both versions)
amb_end = 14.8
na = int(amb_end * SR)
ta = np.arange(na) / SR
fade = np.minimum(1, ta / 0.4) * np.clip((amb_end - ta) / 0.5, 0, 1)
air = lp(hp(rng.standard_normal(na), 200), 1200)
put(air / np.abs(air).max() * fade, 0.0, 0.035, -0.1)
t = 0.4
while t < amb_end - 0.5:
    tt = T(0.09)
    f0 = rng.uniform(3200, 4600)
    chirp = np.sin(2 * np.pi * (f0 + 1600 * tt / 0.09) * tt) * np.sin(np.pi * tt / 0.09) ** 2
    for r in range(int(rng.integers(1, 4))):
        put(chirp, t + r * 0.12, 0.018, float(rng.uniform(-0.8, 0.8)))
    t += rng.uniform(0.7, 1.4)
for t0 in rng.uniform(0.3, 13.5, 12):
    tt = T(0.05)
    put(np.sin(2 * np.pi * rng.uniform(900, 1700) * (1 + 0.6 * tt / 0.05) * tt) * np.exp(-tt * 70), t0, 0.02, float(rng.uniform(-0.9, 0.9)))


# ---------------- foley, on the measured frames
def step():
    tt = T(0.09)
    return lp(rng.standard_normal(len(tt)), 400) * np.exp(-tt * 45) + hp(rng.standard_normal(len(tt)), 2500) * np.exp(-tt * 60) * 0.35


def creak(d, f_lo, f_hi):
    tt = T(d)
    f = f_lo + (f_hi - f_lo) * (0.5 + 0.5 * np.sin(2 * np.pi * 1.1 * tt)) + 30 * np.sin(2 * np.pi * 9 * tt)
    c = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 34 * tt)))
    return lp(hp(c, 250), 2600) * np.sin(np.pi * tt / d) ** 2


for k, sframe in enumerate((160, 172, 183, 194)):    # footfalls (bag bounce)
    put(step(), st("k1", sframe), 0.13, 0.15 if k % 2 else -0.15)
for sframe in (238, 247, 251):                       # knuckles on the wooden door
    tt = T(0.16)
    put((np.sin(2 * np.pi * 180 * tt) * 0.8 + lp(hp(rng.standard_normal(len(tt)), 300), 2500) * 0.5) * np.exp(-tt * 38),
        st("k1", sframe), 0.17, 0.3)
tt = T(0.06)
put(lp(hp(rng.standard_normal(len(tt)), 1500), 8000) * np.exp(-tt * 90), st("k1", 275), 0.06, 0.3)    # latch
put(creak(0.75, 380, 560), st("k1", 276), 0.035, 0.3)                                                  # door swings
t = st("k2", 48)
while t < st("k2", 70):                              # cardboard as she opens the box
    L = rng.uniform(0.06, 0.12); tt = T(L)
    put(lp(hp(rng.standard_normal(len(tt)), 700), 4000) * np.sin(np.pi * tt / L) ** 1.5, t, 0.07, 0.1)
    t += rng.uniform(0.12, 0.2)
for k, m in enumerate([88, 91, 96, 100]):            # the photo comes out
    put(bell(m, 1.8), st("k2", 76) + k * 0.11, 0.045)
for t, m in [(12.9, 84), (13.4, 88)]:                # the asks
    tt = T(0.12)
    put(np.sin(2 * np.pi * hz(m) * (1 + 0.5 * tt / 0.12) * tt) * np.exp(-tt * 30), t, 0.07)
tt = T(0.45)
put(hp(lp(rng.standard_normal(len(tt)), 2500), 300) * np.sin(np.pi * tt / 0.45) ** 2, 14.35, 0.035)

# ---------------- logo
put(bell(79, 1.4), 14.7, 0.10)
put(bell(84, 1.2), 14.92, 0.10)
for m in ((48, 60, 64, 67, 72) if MUSIC else ()):
    put(marimba(m, 1.0) if m > 50 else bass(m, 1.0), 14.7, 0.15)

mix = np.tanh(mix * 1.6) / 1.6
fo = int(0.3 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
mix *= 0.89 / np.abs(mix).max()
out = "audio_misi.wav" if MUSIC else "audio_misi_sfx.wav"
w = wave.open(out, "wb")
w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((mix * 32767).astype(np.int16).tobytes())
w.close()
print(out, DUR)
