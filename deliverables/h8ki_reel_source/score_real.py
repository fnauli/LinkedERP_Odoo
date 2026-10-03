# ---------------- Music (REAL cut): felt piano + strings on ONE steady grid (96 bpm, D major)
# Exec'd inside audio.py (shares its helpers and buses). Beat k is at GRID_A + k * BEAT (common.py).
# The footage was placed so his footfalls fall on the beats (bars 0-2), the house light on beat 13,
# the handover + badge on bar 5's downbeat (beat 20), the recap on beat 24 and the logo chime on beat 28.
#
# Arc:  walk (beats 0-11)  gentle 8th-note piano, melody joins       -> quiet, warm
#       arrival (10-12)    suspended chord under the doorbell          -> waiting
#       light (13-19)      lift to G, strings swell, heartbeat enters  -> hope, momentum
#       handover (20-23)   resolve to D on the badge, fullest point    -> the touching peak
#       recap (24-27)      driving pulse under the ticks               -> payoff
#       logo (28-)         final D chord with the chime, rings out     -> closure

cache = {}


def pluck(m, d=3.2, bright=0.45):                                  # used by the recap flips and the chime
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
    s = fft_filter(s, 40, 2500 + 3500 * vel) / 6.0
    cache[key] = s
    return s


def bt(k):
    return GRID_A + k * BEAT


PV = {  # left hand + middle voicing
    "D": [38, 50, 57, 62, 66], "A/C#": [37, 49, 57, 61, 64], "Bm": [35, 47, 54, 59, 62], "G": [31, 43, 50, 59, 62],
    "Em7": [28, 40, 50, 55, 59], "Asus4": [33, 45, 52, 57, 62], "A": [33, 45, 52, 57, 61],
    "Dfin": [26, 38, 50, 57, 62, 66, 69],
}
ARP = {  # right-hand broken-chord tones
    "D": [62, 66, 69, 74], "A/C#": [61, 64, 69, 73], "Bm": [59, 62, 66, 71], "G": [59, 62, 67, 71],
    "Em7": [59, 62, 64, 67], "Asus4": [57, 62, 64, 69], "A": [57, 61, 64, 69],
}
# (start beat, chord, length in beats)
PROG = [(0, "D", 2), (2, "A/C#", 2), (4, "Bm", 2), (6, "G", 2), (8, "Em7", 2), (10, "Asus4", 2), (12, "A", 1),
        (13, "G", 3), (16, "Em7", 2), (18, "A", 2), (20, "D", 2), (22, "Bm", 2), (24, "G", 2), (26, "A", 2)]
FINAL = 28


def energy(k):
    """0 = the quiet walk, 1 = the handover peak; shapes every layer the same way."""
    return float(np.interp(k, [0, 10, 13, 20, 24, 28], [0.0, 0.15, 0.45, 1.0, 0.72, 0.9]))


strings = buf()


def pad(ch, k0, k1, gain, att=0.9):
    t0 = bt(k0)
    d = (k1 - k0) * BEAT + 0.9
    tt = T(d)
    s = np.zeros(len(tt))
    for m in PV[ch][2:]:
        f = midi(m + 12 if m < 55 else m)
        for det in (-0.10, -0.04, 0.03, 0.09):
            s += saw(f * 2 ** (det / 12), tt + rng.random())
    s = fft_filter(s, 160, 1300)
    env = np.clip(tt / att, 0, 1) * np.clip((d - tt) / 0.9, 0, 1)
    vib = 1 + 0.05 * np.sin(2 * np.pi * 4.6 * tt)
    place(strings, s * env * vib * 0.0075 * gain, t0)


for k, ch, ln in PROG:
    e = energy(k)
    # left hand + chord, gently rolled, held across the change (legato)
    for i, m in enumerate(PV[ch]):
        place(music, piano(m, ln * BEAT + 1.4, 0.45 + 0.3 * e), bt(k) + i * 0.018, (1.2 if i < 2 else 0.7) * (0.75 + 0.4 * e),
              -0.25 + 0.5 * i / (len(PV[ch]) - 1))
    # strings: very soft in the walk, swelling from the light
    pad(ch, k, k + ln, 0.25 + 1.6 * e, att=1.2 if k < 13 else 0.5)
    # right hand: steady 8ths on the grid (quarter-note accents fall on his steps)
    pat = [0, 1, 2, 3, 2, 1, 2, 3]
    for j in range(int(ln * 2)):
        kk = k + j * 0.5
        m = ARP[ch][pat[j % 8]] + (12 if kk >= 13 else 0)
        g = (0.20 + 0.25 * e) * (1.0 if j % 2 == 0 else 0.62)
        place(music, piano(m, 1.4, 0.4 + 0.3 * e), bt(kk) + rng.uniform(0, 0.004), g, -0.3 + 0.6 * (pat[j % 8] / 3))

# melody: (midi, beat, length)
MEL = [(78, 4, 2), (76, 6, 1), (74, 7, 1), (76, 8, 2), (74, 10, 1.5), (76, 11.5, 0.5), (73, 12, 1),
       (78, 13, 1.5), (79, 14.5, 0.5), (81, 15, 1), (79, 16, 2), (76, 18, 1), (73, 19, 1),
       (81, 20, 2), (78, 22, 1.5), (76, 23.5, 0.5), (74, 24, 2), (76, 26, 1), (73, 27, 1)]
for m, k, ln in MEL:
    e = energy(k)
    place(music, piano(m, ln * BEAT + 1.6, 0.55 + 0.25 * e), bt(k), 0.75 + 0.45 * e, 0.1)

# heartbeat kick from the light (half-time), every beat in the recap; soft shaker 8ths from the badge
for k in range(14, FINAL):
    if k < 20 and k % 2:
        continue
    if 20 <= k < 26 and k % 2:
        continue
    tt = T(0.4)
    kick = np.sin(2 * np.pi * (48 + 60 * np.exp(-tt * 30)) * tt) * env_exp(0.4, 0.12)
    place(music, kick * (0.12 + 0.1 * energy(k)), bt(k))
for j in range(40, 2 * FINAL):
    d = 0.06
    sh = fft_filter(noise(d), 5000, 12000) * np.sin(np.pi * T(d) / d)
    place(music, sh * (0.03 if j % 2 else 0.018), bt(j * 0.5), pan=0.3)
# swells into the two big moments (badge, logo)
for k_to, g in [(20, 0.035), (FINAL, 0.05)]:
    d = 2 * BEAT
    tt = T(d)
    place(music, fft_filter(noise(d), 3000, 11000) * (tt / d) ** 2.5 * g, bt(k_to - 2))

# final chord with the logo chime, then let it ring
fin = bt(FINAL)
for i, m in enumerate(PV["Dfin"]):
    place(music, piano(m, DUR - fin + 0.5, 0.8), fin + i * 0.012, 1.3 if i < 2 else 0.85, -0.3 + 0.6 * i / 6)
place(music, piano(74, DUR - fin + 0.5, 0.7), fin, 1.0, 0.1)
tt = T(0.5)
place(music, np.sin(2 * np.pi * (45 + 60 * np.exp(-tt * 25)) * tt) * env_exp(0.5, 0.15) * 0.25, fin)
pad("D", FINAL, FINAL + (DUR - fin) / BEAT - 1.2, 2.2, att=0.25)
music += strings
music *= 0.19                                                     # same loudness as the previous score
