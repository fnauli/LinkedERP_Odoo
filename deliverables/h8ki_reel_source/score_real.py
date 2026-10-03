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
    s = fft_filter(s, 60, 2500 + 3500 * vel) / 6.0
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
# (start beat, chord, length in beats)
PROG = [(0, "D", 2), (2, "A/C#", 2), (4, "Bm", 2), (6, "Gadd9", 2), (8, "Em7", 2), (10, "Asus4", 2), (12, "A", 1),
        (13, "G", 3), (16, "A", 2), (18, "Bsus4", 1), (19, "B", 1), (20, "E", 2), (22, "C#m", 2), (24, "A", 2),
        (26, "B", 2)]
FINAL = 28
BREATHS = [(19.5, 20.0), (27.5, 28.0)]                            # half-beat pull-backs before the landings


def energy(k):
    """0 = the quiet walk, 1 = the handover; every layer follows the same curve."""
    return float(np.interp(k, [0, 10, 13, 19, 20, 24, 28], [0.12, 0.22, 0.42, 0.7, 1.0, 0.82, 1.0]))


def in_breath(k):
    return any(a <= k < b for a, b in BREATHS)


strings = buf()


def pad(notes, k0, k1, gain, att=0.9, lo=160, hi=1300):
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
    pad(upper, k, k + ln, 0.2 + 1.5 * e, att=1.3 if k < 13 else 0.5)
    if ch in BASS:                                                 # warm low strings carry the bass
        pad([BASS[ch], BASS[ch] + 12], k, k + ln, 0.9 + 1.2 * e, att=0.35, lo=60, hi=700)
    pat = [0, 1, 2, 3, 2, 1, 2, 3]
    for j in range(int(ln * 2)):                                   # steady 8ths (quarters land on his steps)
        kk = k + j * 0.5
        if kk < 1 or in_breath(kk):
            continue
        m = ARP[ch][pat[j % 8]]
        g = (0.16 + 0.24 * e) * (1.0 if j % 2 == 0 else 0.6)
        place(music, piano(m, 1.4, 0.4 + 0.3 * e), bt(kk) + rng.uniform(0, 0.004), g, -0.3 + 0.6 * (pat[j % 8] / 3))

# melody: the rising motif three times, each higher and fuller (midi, beat, length)
MEL = [(74, 4, 0.5), (76, 4.5, 0.5), (78, 5, 1), (81, 6, 2), (78, 8, 1), (76, 9, 1), (74, 10, 2), (73, 12, 1),
       (74, 13, 0.5), (76, 13.5, 0.5), (78, 14, 1), (83, 15, 1), (81, 16, 2), (78, 18, 1), (75, 19, 0.5),
       (76, 20, 0.5), (78, 20.5, 0.5), (80, 21, 1), (83, 22, 1.5), (80, 23.5, 0.5),
       (81, 24, 1), (80, 25, 1), (78, 26, 1), (75, 27, 0.5)]
for m, k, ln in MEL:
    e = energy(k)
    place(music, piano(m, ln * BEAT + 1.6, 0.55 + 0.25 * e), bt(k), 0.8 + 0.45 * e, 0.1)
    if k >= 20:                                                    # strings double the tune at the peak
        pad([m, m - 12], k, k + ln, 0.9 if k < 24 else 0.7, att=0.12, lo=200, hi=2600)

# sparkle on the two turning points (light, badge)
for k, notes in [(13, [86, 91]), (20, [88, 95])]:
    for i, m in enumerate(notes):
        place(music, glock(m) * 0.06, bt(k) + i * BEAT / 2, pan=0.35 - 0.7 * i)

# heartbeat kick from the light (half-time), every beat in the recap; soft shaker 8ths from the badge
for k in range(14, FINAL):
    if (k < 24 and k % 2) or in_breath(k):
        continue
    tt = T(0.4)
    kick = np.sin(2 * np.pi * (52 + 60 * np.exp(-tt * 30)) * tt) * env_exp(0.4, 0.11)
    place(music, kick * (0.11 + 0.1 * energy(k)), bt(k))
for j in range(40, 2 * FINAL):
    if in_breath(j * 0.5):
        continue
    d = 0.06
    sh = fft_filter(noise(d), 5000, 12000) * np.sin(np.pi * T(d) / d)
    place(music, sh * (0.028 if j % 2 else 0.016), bt(j * 0.5), pan=0.3)
# risers into the landings (kept out of the breath dip), soft cymbal bloom on them
rise = buf()
for k_to, g in [(20, 0.06), (FINAL, 0.065)]:
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
music *= 0.2                                                     # same loudness as the previous score
