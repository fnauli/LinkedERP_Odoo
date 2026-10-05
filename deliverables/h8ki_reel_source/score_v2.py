# V2 cut of the score (see score_real.py for the design notes)
# ---------------- Music (REAL cut): felt piano + strings on ONE steady grid (96 bpm)
# Exec'd inside audio.py (shares its helpers and buses). Beat k is at GRID_A + k * BEAT (common.py).
# Footfalls fall on the beats (0-11), the house light on beat 13, the handover + badge on beat 20,
# the recap on 24, KETEMU on 26 and the logo chime on 28.
#
# One 4-note rising motif (1-2-3-5: "it can be found") carries the story:
#   walk      beats 0-12   D major, soft piano 8ths in the middle register, motif stated quietly
#   light     beats 13-19  lift: G-A-B climbing bass in warm strings, motif higher, heartbeat enters
#   breath    beat 19.5    everything pulls back for half a beat
#   handover  beat 20      KEY LIFT to E major on the badge: motif in full, strings double it
#   recap     beats 24-27  driving pulse; the recap ticks play the motif
#   breath    beat 27.5    half-beat pause after KETEMU
#   logo      beat 28      final E chord with the chime (B -> E), rings out
# No piano note below G2 (98 Hz): low piano octaves sounded ominous.

cache = {}


def pluck(m, d=3.2, bright=0.45):                                  # recap ticks and chime use this
    key = (m, d, bright)
    if key not in cache:
        cache[key] = karplus(midi(m), d, bright)
    return cache[key]


def piano(m, d=4.0, vel=0.8):
    key = ("pno", m, round(d, 2), round(vel, 2))
    if key in cache:
        return cache[key]
    tt = T(d)
    f0 = midi(m)
    B = 0.00035
    s = np.zeros(len(tt))
    for n in range(1, 13):
        fn = f0 * n * np.sqrt(1 + B * n * n)
        if fn > 9000:
            break
        amp = (1.0 / n ** 1.25) * (0.55 + 0.45 * vel) ** (n * 0.35)
        dec = 0.9 * (220 / f0) ** 0.35 / (1 + 0.35 * (n - 1))
        for det in (-0.6, 0.6):
            s += amp * np.sin(2 * np.pi * (fn + det * n * 0.15) * tt + rng.random() * 6.28) * (
                0.55 * np.exp(-tt / (dec * 3.2)) + 0.45 * np.exp(-tt / (dec * 0.9)))
    att = np.clip(tt / 0.006, 0, 1)
    rel = np.clip((d - tt) / 0.35, 0, 1)
    hammer = fft_filter(noise(0.03), 800, 4000) * env_exp(0.03, 0.006) * 0.02 * vel
    s = s * att * rel
    s[:len(hammer)] += hammer
    s = fft_filter(s, 60, 3800 + 5200 * vel) / 6.0
    cache[key] = s
    return s


def glock(m, d=2.5):
    key = ("glk", m)
    if key not in cache:
        tt = T(d)
        f = midi(m)
        s = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2.76 * f * tt) * np.exp(-tt * 8)
             + 0.12 * np.sin(2 * np.pi * 5.4 * f * tt) * np.exp(-tt * 14)) * env_exp(d, 0.7, 0.002)
        cache[key] = s
    return cache[key]


def bt(k):
    return GRID_A + k * BEAT


# piano chord voicings (lowest note G2 = 43) and right-hand broken-chord tones
PV = {"D": [50, 57, 62, 66], "A/C#": [49, 57, 61, 64], "Bm": [47, 54, 59, 62], "Gadd9": [43, 50, 57, 59, 62],
      "Em7": [52, 55, 59, 62], "Asus4": [45, 52, 57, 62], "A": [45, 52, 57, 61], "G": [43, 55, 59, 62],
      "Bsus4": [47, 54, 59, 64], "B": [47, 54, 59, 63], "E": [52, 59, 64, 68], "C#m": [49, 56, 61, 64],
      "Efin": [52, 59, 64, 68, 71, 76]}
ARP = {"D": [62, 66, 69, 74], "A/C#": [61, 64, 69, 73], "Bm": [59, 62, 66, 71], "Gadd9": [59, 62, 67, 69],
       "Em7": [59, 62, 64, 67], "Asus4": [57, 62, 64, 69], "A": [57, 61, 64, 69], "G": [67, 71, 74, 79],
       "Bsus4": [66, 71, 76, 78], "B": [66, 71, 75, 78], "E": [68, 71, 76, 80], "C#m": [68, 73, 76, 80]}
BASS = {"G": 43, "A": 45, "Bsus4": 47, "B": 47, "E": 52, "C#m": 49}   # warm strings, from the light on
# V2 cut (beats from GRID_A): walk 0-8, dead end 8-13, the ibu points 13-17, bell 17-20, gate 20-23.4,
# handover 23.4-31 (she takes it on beat 28), family 31-35, recap 35-39, logo 39.
PROG = [(0, "D", 2), (2, "A/C#", 2), (4, "Bm", 2), (6, "Gadd9", 2), (8, "Em7", 2), (10, "Asus4", 2), (12, "A", 1),
        (13, "G", 3), (16, "Em7", 2), (18, "A", 2), (20, "Bm", 2), (22, "G", 2), (24, "A", 1), (25, "B", 1),
        (26, "E", 2), (28, "C#m", 2), (30, "A", 1), (31, "B", 1), (32, "A", 2), (34, "B", 2)]
FINAL = 36
BREATHS = [(25.5, 26.0), (35.5, 36.0)]                            # half-beat pull-backs before the landings


def energy(k):
    """0 = the quiet walk, 1 = the handover; every layer follows the same curve."""
    return float(np.interp(k, [0, 8, 12.5, 17, 25, 26, 32, 36], [0.14, 0.2, 0.05, 0.42, 0.72, 1.0, 0.82, 1.0]))


def in_breath(k):
    return any(a <= k < b for a, b in BREATHS)


strings = buf()


def ens(notes, k0, k1, gain, att=0.9, lo=90, hi=4200):
    """Warm string ensemble: 4 detuned voices per note, each with its own slow vibrato, soft harmonics."""
    t0 = bt(k0)
    d = (k1 - k0) * BEAT + 1.0
    tt = T(d)
    s = np.zeros(len(tt))
    for m in notes:
        f = midi(m)
        for v in range(4):
            det = 1 + rng.uniform(-0.0035, 0.0035)
            vib = 1 + 0.0028 * np.sin(2 * np.pi * rng.uniform(4.6, 5.6) * tt + rng.uniform(0, 6.3))
            ph = 2 * np.pi * np.cumsum(f * det * vib) / SR
            for n in range(1, 7):
                if f * n > 7000:
                    break
                s += np.sin(n * ph + rng.uniform(0, 6.3)) * n ** -1.7
    s = fft_filter(s, lo, hi)
    env = (1 - np.exp(-tt / (att / 3 + 1e-3))) * np.clip((d - tt) / 1.0, 0, 1)
    swell = 1 + 0.12 * np.sin(np.pi * np.clip(tt / max(d - 1.0, 0.3), 0, 1))
    place(strings, s * env * swell * 0.0055 * gain, t0, pan=rng.uniform(-0.3, 0.3))


def choir(notes, k0, k1, gain):
    """Soft 'aah' choir: harmonics shaped by the formants of the vowel 'a', three singers per note."""
    t0 = bt(k0)
    d = (k1 - k0) * BEAT + 1.4
    tt = T(d)
    s = np.zeros(len(tt))
    forms = [(800, 90, 1.0), (1150, 110, 0.55), (2900, 180, 0.25), (3300, 220, 0.12)]
    for m in notes:
        f = midi(m)
        for v in range(3):
            vib = 1 + 0.004 * np.sin(2 * np.pi * rng.uniform(5.0, 5.8) * tt + rng.uniform(0, 6.3))
            ph = 2 * np.pi * np.cumsum(f * (1 + rng.uniform(-0.004, 0.004)) * vib) / SR
            for n in range(1, int(4200 / f)):
                fn = f * n
                a = sum(A * np.exp(-0.5 * ((fn - F) / B) ** 2) for F, B, A in forms) + 0.02 / n
                s += a * np.sin(n * ph + rng.uniform(0, 6.3))
    breath = fft_filter(noise(d), 700, 3500) * 0.04
    env = (1 - np.exp(-tt / 0.35)) * np.clip((d - tt) / 1.3, 0, 1)
    place(strings, (s + breath) * env * 0.004 * gain, t0)


def pad(notes, k0, k1, gain, att=0.9, lo=160, hi=1300):
    ens(notes, k0, k1, gain * 0.9, att=att, lo=max(lo, 80), hi=max(hi, 3000))
    return


def _old_pad(notes, k0, k1, gain, att=0.9, lo=160, hi=1300):
    t0 = bt(k0)
    d = (k1 - k0) * BEAT + 0.9
    tt = T(d)
    s = np.zeros(len(tt))
    for m in notes:
        f = midi(m)
        for det in (-0.10, -0.04, 0.03, 0.09):
            s += saw(f * 2 ** (det / 12), tt + rng.random())
    s = fft_filter(s, lo, hi)
    env = np.clip(tt / att, 0, 1) * np.clip((d - tt) / 0.9, 0, 1)
    vib = 1 + 0.05 * np.sin(2 * np.pi * 4.6 * tt)
    place(strings, s * env * vib * 0.0075 * gain, t0)


for k, ch, ln in PROG:
    e = energy(k)
    for i, m in enumerate(PV[ch]):                                 # chord, gently rolled, legato
        place(music, piano(m, ln * BEAT + 1.4, 0.42 + 0.3 * e), bt(k) + i * 0.02,
              (0.85 if i == 0 else 0.7) * (0.7 + 0.45 * e), -0.25 + 0.5 * i / (len(PV[ch]) - 1))
    upper = [m + 12 for m in PV[ch][1:]]
    pad(upper, k, k + ln, 0.2 + 1.5 * e, att=1.3 if k < 17 else 0.5)
    if ch in BASS:                                                 # warm low strings carry the bass
        pad([BASS[ch], BASS[ch] + 12], k, k + ln, 0.9 + 1.2 * e, att=0.35, lo=60, hi=700)
    pat = [0, 1, 2, 3, 2, 1, 2, 3]
    for j in range(int(ln * 2)):                                   # steady 8ths (quarters land on his steps)
        kk = k + j * 0.5
        if kk < 1 or in_breath(kk) or (8 <= kk < 12.5 and j % 2):
            continue
        m = ARP[ch][pat[j % 8]]
        g = (0.16 + 0.24 * e) * (1.0 if j % 2 == 0 else 0.6)
        place(music, piano(m, 1.4, 0.4 + 0.3 * e), bt(kk) + rng.uniform(0, 0.004), g, -0.3 + 0.6 * (pat[j % 8] / 3))

# melody: the rising motif three times, each higher and fuller (midi, beat, length)
MEL = [(74, 4, 0.5), (76, 4.5, 0.5), (78, 5, 1), (81, 6, 2), (78, 8, 1.5), (76, 10, 1.5), (73, 12, 1),
       (74, 13, 0.5), (76, 13.5, 0.5), (78, 14, 1), (83, 15, 1), (79, 16, 2), (76, 18, 1), (73, 19, 1),
       (78, 20, 2), (74, 22, 2), (76, 24, 1), (75, 25, 0.5),
       (76, 26, 0.5), (78, 26.5, 0.5), (80, 27, 1), (83, 28, 1.5), (80, 29.5, 0.5), (81, 30, 1), (78, 31, 1),
       (76, 32, 1), (81, 33, 1), (78, 34, 1), (75, 35, 0.5)]
for m, k, ln in MEL:
    e = energy(k)
    place(music, piano(m, ln * BEAT + 1.6, 0.55 + 0.25 * e), bt(k), 0.8 + 0.45 * e, 0.1)
    if k >= 26:                                                    # strings sing the tune an octave up at the peak
        ens([m + 12, m], k, k + ln, 1.0 if k < 32 else 0.8, att=0.18, hi=6000)

# the choir enters with the key lift, and again under the logo
choir([64, 68, 71, 76], 26, 30, 1.0)
choir([64, 69, 73, 76], 30, 32, 0.8)
choir([64, 68, 71, 76, 80], FINAL, FINAL + (DUR - bt(FINAL)) / BEAT - 1.4, 1.1)
# deep cinematic hit under the key lift: the moment she holds the parcel
tt = T(2.4)
hit = np.sin(2 * np.pi * (38 + 30 * np.exp(-tt * 6)) * tt) * np.exp(-tt / 0.7) + fft_filter(noise(2.4), 60, 400) * np.exp(-tt / 0.25) * 0.25
place(music, hit * 0.5, bt(26))
# sparkle on the two turning points (light, badge)
for k, notes in [(13, [86, 91]), (26, [88, 92, 95]), (36, [88, 95])]:
    for i, m in enumerate(notes):
        place(music, glock(m) * 0.06, bt(k) + i * BEAT / 2, pan=0.35 - 0.7 * i)

# heartbeat kick from the light (half-time), every beat in the recap; soft shaker 8ths from the badge
for k in range(18, FINAL):
    if (k < 32 and k % 2) or in_breath(k):
        continue
    tt = T(0.4)
    kick = np.sin(2 * np.pi * (52 + 60 * np.exp(-tt * 30)) * tt) * env_exp(0.4, 0.11)
    place(music, kick * (0.11 + 0.1 * energy(k)), bt(k))
for j in range(52, 2 * FINAL):
    if in_breath(j * 0.5):
        continue
    d = 0.06
    sh = fft_filter(noise(d), 5000, 12000) * np.sin(np.pi * T(d) / d)
    place(music, sh * (0.028 if j % 2 else 0.016), bt(j * 0.5), pan=0.3)
# risers into the landings (kept out of the breath dip), soft cymbal bloom on them
rise = buf()
for k_to, g in [(26, 0.07), (FINAL, 0.065)]:
    d = 2 * BEAT
    tt = T(d)
    sig = fft_filter(noise(d), 2500, 11000) * (tt / d) ** 3 * g
    l = int(d * SR)
    i0 = int((bt(k_to) - d) * SR)
    rise[i0:i0 + l] += np.stack([sig, sig], 1)
    d = 2.2
    tt = T(d)
    place(music, fft_filter(noise(d), 4000, 14000) * env_exp(d, 0.7, 0.004) * g * 0.6, bt(k_to))

# final chord with the logo chime, then let it ring
fin = bt(FINAL)
ring = DUR - fin + 0.5
for i, m in enumerate(PV["Efin"]):
    place(music, piano(m, ring, 0.8), fin + i * 0.014, 1.15 if i == 0 else 0.95, -0.3 + 0.6 * i / 5)
place(music, piano(76, ring, 0.7), fin, 1.0, 0.1)
pad([64, 68, 71, 76], FINAL, FINAL + (DUR - fin) / BEAT - 1.2, 2.0, att=0.2)
pad([40, 52], FINAL, FINAL + (DUR - fin) / BEAT - 1.2, 1.4, att=0.2, lo=60, hi=600)
music += strings
# the breaths: everything sinks for half a beat, then lands together on the beat
for a, b in BREATHS:
    i0, i1 = int(bt(a) * SR), int(bt(b) * SR)
    x = np.linspace(0, 1, i1 - i0)
    music[i0:i1] *= (1 - 0.7 * np.sin(np.pi / 2 * np.minimum(x * 3, 1)))[:, None]
music += rise
# presence and air: lift everything above ~2.5 kHz so piano, strings and choir shimmer instead of sounding boxy
for ch in range(2):
    music[:, ch] += fft_filter(music[:, ch], 2500, 14000) * 1.6 + fft_filter(music[:, ch], 6000, 16000) * 1.2
# the dead end is the quietest, most intimate moment, so the turn back and the handover feel earned
i0, i1, i2 = int(bt(8) * SR), int(bt(9) * SR), int(bt(12.5) * SR)
duck = np.ones(len(music))
duck[i0:i1] = np.linspace(1, 0.62, i1 - i0)
duck[i1:i2] = 0.62
duck[i2:i2 + int(1.2 * SR)] = np.linspace(0.62, 1, int(1.2 * SR))
music *= duck[:, None]
music *= 0.2                                                     # same loudness as the previous score
