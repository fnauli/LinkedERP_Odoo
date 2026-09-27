"""Synthesized score + Foley for 'The Human Algorithm'."""
import numpy as np
import wave
from common import *

SR = 44100
N = int(DUR * SR)
rng = np.random.default_rng(7)


def buf():
    return np.zeros((N, 2))


def T(t):
    return np.arange(int(t * SR)) / SR


def place(bus, sig, t, gain=1.0, pan=0.0):
    """Add mono (or stereo) sig into bus at time t with equal-power pan."""
    i = int(t * SR)
    if i >= N:
        return
    if sig.ndim == 1:
        l = np.cos((pan + 1) * np.pi / 4)
        r = np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l, sig * r], 1) * 1.414
    n = min(len(sig), N - i)
    bus[i:i + n] += sig[:n] * gain


def fft_filter(x, lo=None, hi=None, order=2):
    n = len(x)
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(n, 1 / SR)
    m = np.ones_like(f)
    if hi:
        m *= 1 / np.sqrt(1 + (f / hi) ** (2 * order))
    if lo:
        m *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (2 * order))
    if X.ndim == 2:
        m = m[:, None]
    return np.fft.irfft(X * m, n, axis=0)


def noise(d):
    return rng.standard_normal(int(d * SR))


def env_exp(d, tau, attack=0.002):
    t = T(d)
    e = np.exp(-t / tau)
    a = int(attack * SR)
    if a > 0:
        e[:a] *= np.linspace(0, 1, a)
    return e


def reverb(x, secs=2.4, decay=2.8, pre=0.02, lo=200, hi=6000):
    n = int(secs * SR)
    t = np.arange(n) / SR
    irs = []
    for _ in range(2):
        ir = rng.standard_normal(n) * np.exp(-t * decay)
        ir = fft_filter(ir, lo, hi)
        ir[: int(pre * SR)] = 0
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    out = np.zeros_like(x)
    L = len(x) + n
    nfft = 1 << (L - 1).bit_length()
    for c in range(2):
        out[:, c] = np.fft.irfft(np.fft.rfft(x[:, c], nfft) * np.fft.rfft(irs[c], nfft), nfft)[: len(x)]
    return out


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def karplus(freq, d=3.0, bright=0.5, t_half=1.3):
    """Vectorised Karplus-Strong pluck."""
    n = int(d * SR)
    p = int(SR / freq)
    decay = 0.5 ** (1 / (freq * t_half))
    y = np.zeros(n + p + 1)
    exc = rng.uniform(-1, 1, p)
    # soften the excitation for a warmer nylon/steel tone
    for _ in range(int((1 - bright) * 4) + 1):
        exc = 0.5 * (exc + np.roll(exc, 1))
    y[:p] = exc
    i = p
    while i < n + p:
        j = min(i + p, n + p)
        prev = y[i - p:j - p]
        prev2 = y[i - p - 1:j - p - 1] if i - p - 1 >= 0 else np.concatenate([[0], y[i - p:j - p - 1]])
        y[i:j] = decay * 0.5 * (prev + prev2[: len(prev)])
        i = j
    out = y[p:p + n]
    # body resonance: gentle lowpass + tiny low bump
    out = fft_filter(out, 70, 5200)
    fade = np.ones(n)
    fade[-2000:] = np.linspace(1, 0, 2000)
    return out * fade


def square(f, t):
    return np.sign(np.sin(2 * np.pi * f * t))


def saw(f, t):
    return 2 * ((f * t) % 1.0) - 1


# ---------------------------------------------------------------- buses
digital = buf()   # scene 1-2 (gets hard-gated before the silence)
night = buf()     # ambience + foley
music = buf()
fx_bright = buf()  # UI dings, chime (extra reverb)

# ---------------- Scene 1: keyboard, errors, anxious beat
for q in QW:
    n = len(q["text"])
    dur = q["type_end"] - q["start"]
    for k in range(n):
        tt = q["start"] + dur * k / n + rng.uniform(-0.006, 0.006)
        d = 0.03
        c = fft_filter(noise(d), 1800, 7000) * env_exp(d, 0.006)
        thump = np.sin(2 * np.pi * 160 * T(d)) * env_exp(d, 0.008) * 0.6
        place(digital, (c + thump) * rng.uniform(0.35, 0.6), tt, pan=rng.uniform(-0.3, 0.3))
    # searching blips
    for k in range(3):
        tb = q["type_end"] + k * (q["err"] - q["type_end"]) / 3
        s = np.sin(2 * np.pi * 1600 * T(0.04)) * env_exp(0.04, 0.012)
        place(digital, s * 0.12, tb)
    # harsh error buzz
    d = 0.42
    t = T(d)
    bz = square(98, t) + 0.8 * square(104.5, t) + 0.5 * square(196, t) + 0.3 * saw(311, t)
    gate = (np.sin(2 * np.pi * 14 * t) > -0.3).astype(float)
    bz = np.tanh(2.5 * bz) * gate * env_exp(d, 0.22, 0.004)
    bz = fft_filter(bz, 60, 3500)
    place(digital, bz * 0.34, q["err"])
    beep = square(880, T(0.12)) * env_exp(0.12, 0.05)
    place(digital, fft_filter(beep, None, 4000) * 0.08, q["err"])

bpm = 140
s16 = 60 / bpm / 4
t = 0.0
k = 0
while t < S1_END + 1.2:
    prog = t / (S1_END + 1.2)
    d = 0.025
    hh = fft_filter(noise(d), 7000, None) * env_exp(d, 0.006 if k % 4 else 0.012)
    place(digital, hh * (0.05 + 0.07 * prog) * (1.5 if k % 4 == 0 else 1), t, pan=0.25 if k % 2 else -0.25)
    if k % 2 == 0:  # 8th-note bass pulse, filter opening = rising tension
        d = s16 * 1.7
        tt = T(d)
        f0 = 55 * (1.0 if t < 3.6 else 2 ** (1 / 12) if t < 5.6 else 2 ** (3 / 12))
        b = saw(f0, tt) + saw(f0 * 1.005, tt)
        b = fft_filter(b, 40, 250 + 1400 * prog) * env_exp(d, 0.09, 0.003)
        place(digital, b * 0.12, t)
    if k % 4 == 0 and t > 1.6:
        tt = T(0.25)
        kick = np.sin(2 * np.pi * (48 + 90 * np.exp(-tt * 40)) * tt) * env_exp(0.25, 0.08)
        place(digital, kick * 0.25, t)
    t += s16
    k += 1

# riser 4.2 -> 7.35
d = S1_END - 4.2
tt = T(d)
sw = np.sin(2 * np.pi * np.cumsum(220 * 2 ** (tt / d * 2.3)) / SR)
rs = (sw * 0.5 + fft_filter(noise(d), 1500, 9000) * 0.5) * (tt / d) ** 2.2
place(digital, rs * 0.10, 4.2)

# ---------------- Scene 2: glitch stutter + power down
seg_src = digital[int((S1_END - 0.8) * SR):int((S1_END - 0.7) * SR)].copy()
t = S1_END
while t < GLITCH_END - 0.05:
    L = int(rng.uniform(0.03, 0.09) * SR)
    piece = digital[int((S1_END - 0.9) * SR):int((S1_END - 0.9) * SR) + L].copy()
    piece = np.round(piece * 6) / 6            # bit crush
    reps = rng.integers(1, 4)
    for r in range(reps):
        place(digital, piece * 0.8, t + r * L / SR)
    if rng.random() < 0.6:
        f = rng.uniform(300, 2400)
        ch = square(f, T(0.05)) * env_exp(0.05, 0.02)
        place(digital, ch * 0.08, t, pan=rng.uniform(-0.6, 0.6))
    t += reps * L / SR + rng.uniform(0.0, 0.03)
# final glitch "5 dari 5" hit
tt = T(0.6)
hit = np.tanh(3 * (square(73, tt) + square(77.8, tt))) * env_exp(0.6, 0.25)
place(digital, fft_filter(hit, 40, 2000) * 0.25, S1_END)

d = POWER_END - (GLITCH_END - 0.05)
tt = T(d)
fsweep = 700 * (25 / 700) ** (tt / d)
ph = 2 * np.pi * np.cumsum(fsweep) / SR
pd = (np.sin(ph) + 0.45 * saw(1, 0) * 0 + 0.4 * np.sign(np.sin(ph * 0.5))) * (1 - tt / d) ** 1.4
pd = fft_filter(pd, 20, 3000)
hum = np.sin(2 * np.pi * 50 * tt) * np.exp(-tt * 3) * 0.5
thunk = np.sin(2 * np.pi * (40 + 60 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)
place(digital, (pd * 0.35 + hum * 0.2 + thunk * 0.4), GLITCH_END - 0.05)

# ---------------- Scene 3: night ambience
# air
d = DUR - NIGHT_START
air = fft_filter(noise(d), 80, 900) * 0.015
air *= np.clip(T(d) / 1.5, 0, 1)
place(night, air, NIGHT_START)


def cricket(f, t0, t1, period, pan, gain):
    t = t0
    while t < t1:
        nchirp = rng.integers(3, 5)
        for c in range(nchirp):
            d = 0.028
            tt = T(d)
            s = np.sin(2 * np.pi * f * tt) * np.sin(np.pi * tt / d) ** 2
            place(night, s * gain * rng.uniform(0.7, 1.0), t + c * 0.042, pan=pan)
        t += period * rng.uniform(0.85, 1.15)


cricket(4650, 10.75, DUR - 3.4, 0.82, -0.55, 0.030)
cricket(5200, 11.2, DUR - 3.4, 1.07, 0.6, 0.022)
cricket(3900, 12.3, DUR - 3.4, 1.33, 0.1, 0.014)


def gravel_step(gain, pan):
    d = 0.16
    tt = T(d)
    grains = (rng.random(len(tt)) < 0.02).astype(float) * rng.uniform(0.3, 1, len(tt))
    grains = np.convolve(grains, np.exp(-np.arange(90) / 12), "same")
    crunch = fft_filter(noise(d), 500, 5000) * grains * env_exp(d, 0.05, 0.004)
    thud = np.sin(2 * np.pi * 75 * tt) * env_exp(d, 0.03)
    return (crunch * 0.9 + thud * 0.5) * gain


for i, ts in enumerate(footsteps_s3()):
    g = 0.22 * lin(ts, WALK_START, TILT_END - 0.6) + 0.06
    place(night, gravel_step(g, 0), ts, pan=0.12 if i % 2 else -0.12)


def concrete_step(gain):
    d = 0.12
    tt = T(d)
    s = fft_filter(noise(d), 300, 3500) * env_exp(d, 0.02) + np.sin(2 * np.pi * 90 * tt) * env_exp(d, 0.025) * 0.6
    return s * gain


for i, ts in enumerate(footsteps_s4()):
    place(night, concrete_step(0.16), ts, pan=-0.3 + 0.1 * i)
place(night, concrete_step(0.10), LIGHT_T + 0.45, pan=0.0)

# whooshes
for tw, g, dd in [(NIGHT_START, 0.06, 1.8), (S4_START - 0.25, 0.07, 0.6), (S4_END - 0.1, 0.09, 1.0)]:
    tt = T(dd)
    ev = np.sin(np.pi * tt / dd) ** 2
    wsh = fft_filter(noise(dd), 300, 2500) * ev
    place(night, wsh * g, tw)

# heartbeats for "Satu paket, satu penghasilan."
for th in [T3[0] + 0.05, T3[0] + 1.25]:
    for off, g in [(0, 1.0), (0.2, 0.7)]:
        tt = T(0.3)
        hb = np.sin(2 * np.pi * (45 + 25 * np.exp(-tt * 25)) * tt) * env_exp(0.3, 0.07)
        place(night, hb * 0.35 * g, th + off)

# package rustle / thud
d = 0.45
tt = T(d)
crin = (rng.random(len(tt)) < 0.01).astype(float)
crin = np.convolve(crin, np.exp(-np.arange(200) / 30), "same")
rus = fft_filter(noise(d), 700, 4500) * (0.3 + crin) * np.sin(np.pi * tt / d)
place(night, rus * 0.10, RUSTLE_T - 0.2)
tt = T(0.2)
place(night, np.sin(2 * np.pi * 110 * tt) * env_exp(0.2, 0.04) * 0.25, RUSTLE_T + 0.18)

# doorbell ting-tong
for i, m in enumerate([76, 72]):
    d = 1.4
    tt = T(d)
    f = midi(m)
    b = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2.76 * f * tt) * np.exp(-tt * 6)) * env_exp(d, 0.5, 0.003)
    place(fx_bright, b * 0.10, BELL_T + i * 0.38, pan=0.25)

# light switch click
d = 0.02
place(night, fft_filter(noise(d), 1500, 8000) * env_exp(d, 0.003) * 0.35, LIGHT_T - 0.05, pan=0.2)
place(night, fft_filter(noise(d), 1500, 8000) * env_exp(d, 0.003) * 0.2, LIGHT_T - 0.02, pan=0.2)

# check "ding"
d = 1.6
tt = T(d)
ding = (np.sin(2 * np.pi * 1318.5 * tt) + 0.5 * np.sin(2 * np.pi * 2637 * tt) * np.exp(-tt * 5)
        + 0.25 * np.sin(2 * np.pi * 3955 * tt) * np.exp(-tt * 9)) * env_exp(d, 0.45, 0.002)
place(fx_bright, ding * 0.13, BADGE_T)
place(fx_bright, np.sin(2 * np.pi * 1760 * tt) * env_exp(d, 0.35, 0.002) * 0.07, BADGE_T + 0.09)

# ---------------- Music: acoustic guitar + strings
beat = 0.75   # 80 bpm
e8 = beat / 2
CH = {
    "D": [50, 57, 62, 66, 69],
    "A/C#": [49, 57, 64, 69, 73],
    "Bm": [47, 54, 59, 62, 66],
    "G": [43, 50, 55, 59, 62],
    "A": [45, 52, 57, 61, 64],
    "Asus": [45, 52, 57, 62, 64],
    "Em": [40, 47, 52, 55, 59],
}
prog3 = ["D", "A/C#", "Bm", "G", "D", "A/C#", "Asus"]
pattern = [0, 1, 2, 3, 4, 3, 2, 1]
g_start = 10.85
cache = {}


def pluck(m, d=3.2, bright=0.45):
    key = (m, d, bright)
    if key not in cache:
        cache[key] = karplus(midi(m), d, bright)
    return cache[key]


t0 = g_start
for ci, ch in enumerate(prog3):
    notes = CH[ch]
    for k in range(8):
        tt = t0 + ci * 8 * e8 / 2 + k * e8 / 2
        if ci == 0 and k % 2 == 1:
            continue  # sparse entry
        m = notes[pattern[k]]
        g = 0.22 if k == 0 else 0.13
        g *= 0.6 + 0.4 * lin(tt, g_start, 14.0)
        pan = -0.35 + 0.7 * (pattern[k] / 4)
        place(music, pluck(m), tt + rng.uniform(0, 0.008), g, pan)
# each chord = 4 eighth-notes-of-16th feel -> chord length:
chord_len = 8 * e8 / 2          # 1.5 s
s3_music_end = t0 + len(prog3) * chord_len   # 22.85

# melody (enters with the second phrase)
mel = [(14.6, 78, 0.9), (15.35, 76, 0.4), (15.73, 74, 0.8), (16.85, 76, 0.7), (17.6, 78, 0.8),
       (18.35, 81, 1.2), (19.85, 79, 0.4), (20.23, 78, 0.4), (20.6, 76, 1.0), (21.35, 74, 0.6),
       (22.1, 76, 1.2)]
for tm, m, _ in mel:
    place(music, pluck(m, 3.5, 0.7), tm, 0.16, 0.1)

# scene 4: strums + strings swell
prog4 = [("G", 21.35), ("A", 22.85), ("D", LIGHT_T - 0.1), ("Bm", 26.1), ("G", 27.1), ("D", CHIME_T - 0.05)]
for idx, (ch, ts) in enumerate(prog4):
    nxt = prog4[idx + 1][1] if idx + 1 < len(prog4) else DUR
    b = ts
    while b < nxt - 0.05 and b < DUR - 1.5:
        for s, m in enumerate(CH[ch]):
            place(music, pluck(m, 3.0, 0.55), b + s * 0.014, 0.10 if b == ts else 0.065, -0.4 + s * 0.2)
        b += beat if ch != "D" or idx != len(prog4) - 1 else 99

strings = buf()
for idx, (ch, ts) in enumerate(prog4):
    nxt = prog4[idx + 1][1] if idx + 1 < len(prog4) else DUR
    d = nxt - ts + 0.6
    tt = T(d)
    s = np.zeros(len(tt))
    for m in CH[ch][1:]:
        f = midi(m + 12 if m < 52 else m)
        for det in (-0.12, 0.0, 0.11):
            s += saw(f * 2 ** (det / 12), tt + rng.random())
    s = fft_filter(s, 150, 1800)
    att = np.clip(tt / 0.9, 0, 1)
    rel = np.clip((d - tt) / 0.6, 0, 1)
    vib = 1 + 0.08 * np.sin(2 * np.pi * 5 * tt)
    swell = 0.5 + 0.5 * lin(ts, 21.3, LIGHT_T)
    place(strings, s * att * rel * vib * 0.012 * swell, ts, pan=(-0.2 if idx % 2 else 0.2))
music += strings

# subtle uplifting beat after the light turns on
t = LIGHT_T - 0.1
k = 0
while t < CHIME_T - 0.2:
    if k % 2 == 0:
        tt = T(0.35)
        kick = np.sin(2 * np.pi * (50 + 70 * np.exp(-tt * 35)) * tt) * env_exp(0.35, 0.1)
        place(music, kick * 0.22, t)
    d = 0.06
    sh = fft_filter(noise(d), 5000, 12000) * np.sin(np.pi * T(d) / d)
    place(music, sh * 0.04, t + e8 / 2, pan=0.3)
    t += e8
    k += 1

# brand chime: two-note harmonic (A5 -> E6), bell-clean
for i, m in enumerate([81, 88]):
    d = 3.0
    tt = T(d)
    f = midi(m)
    harm = (np.sin(2 * np.pi * f * tt) + 0.18 * np.sin(2 * np.pi * 2 * f * tt)) * env_exp(d, 0.9, 0.004)
    place(fx_bright, harm * 0.13, CHIME_T + i * 0.24, pan=-0.15 + 0.3 * i)
    place(fx_bright, pluck(m, 3.0, 0.8) * 0.25, CHIME_T + i * 0.24)

# ---------------------------------------------------------------- mix
dig = digital + reverb(digital, 1.2, 5, lo=300, hi=5000) * 0.18
gi = int(POWER_END * SR)
fade = int(0.05 * SR)
dig[gi - fade:gi] *= np.linspace(1, 0, fade)[:, None]
dig[gi:] = 0

wet = reverb(music + night * 0.4, 2.8, 2.4) * 0.28 + reverb(fx_bright, 3.2, 2.0, hi=9000) * 0.45
mix = dig * 0.6 + night * 1.1 + music * 1.15 + fx_bright + wet
# enforce the 1s of complete silence
si, se = int(POWER_END * SR), int(10.65 * SR)
mix[si:se] = 0
ramp = int(0.2 * SR)
mix[se:se + ramp] *= np.linspace(0, 1, ramp)[:, None]
# end fade
fo = int(0.8 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5

peak = np.max(np.abs(mix))
mix = mix / peak * 1.25
mix = np.tanh(mix) * 0.89
pcm = (mix * 32767).astype(np.int16)
with wave.open("audio.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("audio ok", peak)
