"""Original soundtrack for Reel #3, synthesized from scratch (no samples): a ticking clock while the dot is stuck,
then a light 100 bpm marimba groove (Am - F - G - C, resolving on "Paket diterima"), UI pings on every status
change and a two-note logo chime. Beat = 0.6 s, the same grid as the cuts."""
import os, wave
import numpy as np
MUSIC = os.environ.get("MUSIC", "1") == "1"   # MUSIC=0: sound effects only, for a trending sound added in the app

SR, DUR = 48000, 14.6
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


# ---------------- 0 - 2.4 s: stuck. tick-tock and a low drone
for k in range(8):
    tt = T(0.04)
    click = hp(rng.standard_normal(len(tt)), 2500) * np.exp(-tt * 160)
    tone = np.sin(2 * np.pi * (2400 if k % 2 == 0 else 1900) * tt) * np.exp(-tt * 120)
    put(click * 0.6 + tone * 0.5, 0.02 + k * 0.3, 0.16, 0.25 if k % 2 else -0.25)
dr = T(2.6)
drone = (np.sin(2 * np.pi * hz(45) * dr) + 0.5 * np.sin(2 * np.pi * hz(52) * dr)) * (0.8 + 0.2 * np.sin(2 * np.pi * 2.5 * dr))
drone *= np.minimum(1, dr / 0.3) * np.clip((2.6 - dr) / 0.3, 0, 1)
if MUSIC:
    put(drone, 0.0, 0.08)
# hook: phone vibration (two buzzes) and a notification ding on frame 1
for t0 in (0.0, 0.3):
    tt = T(0.2)
    bz = (np.sign(np.sin(2 * np.pi * 150 * tt)) * 0.6 + np.sin(2 * np.pi * 300 * tt) * 0.4) * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * tt))
    bz = lp(bz * np.minimum(1, tt / 0.01) * np.clip((0.2 - tt) / 0.03, 0, 1), 1200)
    put(bz, t0, 0.12)
for k, m in enumerate([88, 93]):
    tt = T(0.5)
    put(np.sin(2 * np.pi * hz(m) * tt) * np.exp(-tt * 9), 0.02 + k * 0.09, 0.08)

if MUSIC:
    # ---------------- 2.4 - 13.2 s: the groove (Am - F - G, C on "Paket diterima", F - G, C on the logo)
    CH = [(2.4, [57, 60, 64], 45), (4.8, [53, 57, 60], 41), (7.2, [55, 59, 62], 43), (8.4, [60, 64, 67], 48),
          (10.8, [53, 57, 60], 41), (12.0, [55, 59, 62], 43)]
    ARP = [0, 1, 2, 1, 2, 3, 2, 1]                     # eighth notes over the triad (+octave)
    for ci, (t0, tri, root) in enumerate(CH):
        t_end = CH[ci + 1][0] if ci + 1 < len(CH) else 13.2
        notes = tri + [tri[0] + 12]
        k = 0
        while t0 + k * BEAT / 2 < t_end - 1e-6:
            put(marimba(notes[ARP[k % 8]] + 12), t0 + k * BEAT / 2, 0.22 if k % 2 == 0 else 0.15, -0.3 + 0.6 * (k % 2))
            k += 1
        for bb in (0, 2):
            if t0 + bb * BEAT < t_end - 1e-6:
                put(bass(root), t0 + bb * BEAT, 0.32)
    t = 2.4 + BEAT / 2                                 # shaker on the off-beats
    while t < 13.2:
        tt = T(0.06)
        put(hp(rng.standard_normal(len(tt)), 6000) * np.exp(-tt * 70), t, 0.05, 0.4)
        t += BEAT
    t = 4.8 + BEAT                                     # claps on 2 and 4 once he is moving
    while t < 13.2:
        tt = T(0.12)
        put(lp(hp(rng.standard_normal(len(tt)), 900), 5000) * np.exp(-tt * 35), t, 0.09, -0.1)
        t += 2 * BEAT
    put(pad([60, 64, 67, 72], 3.6), 8.4, 0.10)        # warmth on the delivery

# ---------------- ambience: an evening kampung after rain (both versions, so it is never silent)
amb_end = 13.6
na = int(amb_end * SR)
ta = np.arange(na) / SR
fade = np.minimum(1, ta / 0.4) * np.clip((amb_end - ta) / 0.5, 0, 1)
rain = hp(lp(rng.standard_normal(na), 6500), 1500)
rain = rain / np.abs(rain).max()
put(rain * fade * (0.9 + 0.1 * np.sin(2 * np.pi * 0.3 * ta)), 0.0, 0.045, -0.2)
put(np.roll(rain, 9000) * fade, 0.0, 0.045, 0.2)
cr = np.zeros(na)                                    # crickets: short 4.6 kHz chirps in little bursts
t = 0.15
while t < amb_end - 0.3:
    for j in range(3):
        i0 = int((t + j * 0.045) * SR); L = int(0.03 * SR)
        if i0 + L < na:
            u = np.arange(L) / SR
            cr[i0:i0 + L] += np.sin(2 * np.pi * 4600 * u) * np.sin(np.pi * u / 0.03) ** 2
    t += rng.uniform(0.55, 0.95)
put(cr * fade, 0.0, 0.025, 0.5)
mb_d = 2.6                                           # a motorbike passing a street away
tt = T(mb_d)
f0 = 85 + 25 * tt / mb_d
eng = np.sign(np.sin(2 * np.pi * np.cumsum(f0) / SR)) * 0.5 + lp(rng.standard_normal(len(tt)), 600) * 0.5
eng = lp(eng, 900) * np.sin(np.pi * tt / mb_d) ** 2
put(eng / np.abs(eng).max(), 5.2, 0.03, -0.6)

# ---------------- foley: the world of the bottom half
def step():
    tt = T(0.09)
    thud = lp(rng.standard_normal(len(tt)), 400) * np.exp(-tt * 45)
    splash = hp(rng.standard_normal(len(tt)), 2500) * np.exp(-tt * 60) * 0.35
    return thud + splash

def creak(d, f_lo, f_hi):
    tt = T(d)
    f = f_lo + (f_hi - f_lo) * (0.5 + 0.5 * np.sin(2 * np.pi * 1.1 * tt)) + 30 * np.sin(2 * np.pi * 9 * tt)
    c = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 34 * tt)))
    return lp(hp(c, 250), 2600) * np.sin(np.pi * tt / d) ** 2

put(creak(0.45, 380, 520), 2.45, 0.035, -0.5)       # her door creaks open
for k in range(6):                                   # his footsteps on wet stone
    put(step(), 4.85 + k * 0.4, 0.12, 0.15 if k % 2 else -0.15)
tt = T(0.05)                                         # gate latch, then the iron gate swings
put(hp(rng.standard_normal(len(tt)), 1800) * np.exp(-tt * 110), 7.3, 0.12, 0.3)
put(np.sin(2 * np.pi * 1450 * tt) * np.exp(-tt * 80), 7.31, 0.05, 0.3)
put(creak(0.8, 520, 760), 7.4, 0.04, 0.3)
for k in range(5):                                   # the plastic bag changing hands
    L = rng.uniform(0.05, 0.1); tt = T(L)
    put(hp(rng.standard_normal(len(tt)), 3000) * np.sin(np.pi * tt / L) ** 1.5, 8.5 + k * 0.13 + rng.uniform(0, 0.05), 0.05, -0.1)

# ---------------- UI: status pings, U-turn whoosh, the delivered chime, punchline and ask pops
for t, m in [(2.4, 76), (4.8, 79), (7.2, 81)]:
    tt = T(0.25)
    put(np.sin(2 * np.pi * hz(m) * tt) * np.exp(-tt * 18) + 0.3 * np.sin(2 * np.pi * hz(m + 12) * tt) * np.exp(-tt * 30), t, 0.14)
tt = T(0.6)
put(hp(lp(rng.standard_normal(len(tt)), 3000), 400) * np.sin(np.pi * tt / 0.6) ** 2, 3.75, 0.05, 0.3)
for k, m in enumerate([84, 88, 91, 96]):
    put(bell(m, 1.4), 8.4 + k * 0.075, 0.07)
for t in (8.55, 9.15):
    tt = T(0.08)
    put(np.sin(2 * np.pi * 180 * tt) * np.exp(-tt * 50), t, 0.12)
for t, m in [(10.9, 84), (11.5, 88)]:                 # little pops as the like and follow asks appear
    tt = T(0.12)
    put(np.sin(2 * np.pi * hz(m) * (1 + 0.5 * tt / 0.12) * tt) * np.exp(-tt * 30), t, 0.07)
tt = T(0.45)                                         # soft air under the dissolve to the logo
put(hp(lp(rng.standard_normal(len(tt)), 2500), 300) * np.sin(np.pi * tt / 0.45) ** 2, 13.15, 0.035)

# ---------------- logo: two-note chime and a ringing C chord
put(bell(79, 1.4), 13.5, 0.10)
put(bell(84, 1.2), 13.72, 0.10)
for m in ((48, 60, 64, 67, 72) if MUSIC else ()):
    put(marimba(m, 1.2) if m > 50 else bass(m, 1.1), 13.5, 0.16)

# ---------------- master: gentle saturation, fade, normalise
mix = np.tanh(mix * 1.6) / 1.6
fo = int(0.35 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
mix *= 0.89 / np.abs(mix).max()
w = wave.open("audio_r3.wav" if MUSIC else "audio_r3_sfx.wav", "wb")
w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((mix * 32767).astype(np.int16).tobytes())
w.close()
print("audio_r3.wav" if MUSIC else "audio_r3_sfx.wav", DUR)
