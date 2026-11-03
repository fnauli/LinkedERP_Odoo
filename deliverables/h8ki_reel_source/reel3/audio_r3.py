"""Original soundtrack for Reel #3, synthesized from scratch (no samples): a ticking clock while the dot is stuck,
then a light 100 bpm marimba groove (Am - F - G - C, resolving on "Paket diterima"), UI pings on every status
change and a two-note logo chime. Beat = 0.6 s, the same grid as the cuts."""
import wave
import numpy as np

SR, DUR = 48000, 16.0
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
put(drone, 0.0, 0.08)

# ---------------- 2.4 - 13.2 s: the groove, one chord per bar
CH = [(2.4, [57, 60, 64], 45), (4.8, [53, 57, 60], 41), (7.2, [55, 59, 62], 43), (9.6, [60, 64, 67], 48),
      (12.0, [53, 57, 60], 41)]
ARP = [0, 1, 2, 1, 2, 3, 2, 1]                     # eighth notes over the triad (+octave)
for t0, tri, root in CH:
    notes = tri + [tri[0] + 12]
    for k in range(8):
        t = t0 + k * BEAT / 2
        if t >= 13.8:
            break
        put(marimba(notes[ARP[k]] + 12), t, 0.22 if k % 2 == 0 else 0.15, -0.3 + 0.6 * (k % 2))
    for b in (0, 2):
        if t0 + b * BEAT < 13.8:
            put(bass(root), t0 + b * BEAT, 0.32)
# shaker on the off-beats, claps on 2 and 4 once he is moving
t = 2.4 + BEAT / 2
while t < 13.2:
    tt = T(0.06)
    put(hp(rng.standard_normal(len(tt)), 6000) * np.exp(-tt * 70), t, 0.05, 0.4)
    t += BEAT
t = 4.8 + BEAT
while t < 13.2:
    tt = T(0.12)
    clap = lp(hp(rng.standard_normal(len(tt)), 900), 5000) * np.exp(-tt * 35)
    put(clap, t, 0.09, -0.1)
    t += 2 * BEAT
put(pad([60, 64, 67, 72], 3.6), 9.6, 0.10)        # warmth on the delivery

# ---------------- UI: status pings, the U-turn whoosh, the delivered chime, punchline pops
for t, m in [(2.4, 76), (4.8, 79), (7.2, 81)]:
    tt = T(0.25)
    put(np.sin(2 * np.pi * hz(m) * tt) * np.exp(-tt * 18) + 0.3 * np.sin(2 * np.pi * hz(m + 12) * tt) * np.exp(-tt * 30), t, 0.14)
tt = T(0.6)
wh = hp(lp(rng.standard_normal(len(tt)), 3000), 400) * np.sin(np.pi * tt / 0.6) ** 2
put(wh, 3.75, 0.05, 0.3)
for k, m in enumerate([84, 88, 91, 96]):
    put(bell(m, 1.4), 9.6 + k * 0.075, 0.07)
for t in (9.75, 10.35):
    tt = T(0.08)
    put(np.sin(2 * np.pi * 180 * tt) * np.exp(-tt * 50), t, 0.12)

tt = T(0.7)                                          # soft air under the dissolve to the end card
air = hp(lp(rng.standard_normal(len(tt)), 2500), 300) * np.sin(np.pi * tt / 0.7) ** 2
put(air, 13.15, 0.035)

# ---------------- end card: two-note chime and a final ringing chord
put(bell(79, 2.0), 13.8, 0.10)
put(bell(84, 2.4), 14.1, 0.10)
for m in (48, 60, 64, 67, 72):
    put(marimba(m, 2.0) if m > 50 else bass(m, 1.6), 13.8, 0.16)

# ---------------- master: gentle saturation, fade, normalise
mix = np.tanh(mix * 1.6) / 1.6
fo = int(0.5 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
mix *= 0.89 / np.abs(mix).max()
w = wave.open("audio_r3.wav", "wb")
w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((mix * 32767).astype(np.int16).tobytes())
w.close()
print("audio_r3.wav", DUR)
