# ---------------- Music (REAL cut): felt piano + strings, rubato walk, steady pulse from the light
# Exec'd inside audio.py (shares its helpers and buses).
#
# Walk (clips 1-2): no tempo. The courier's pace changes between clips (0.61 s vs 0.67 s per step), so a
# beat would drift against his feet. The piano places its chords on his real footfalls (rubato),
# sustained, with strings underneath; the foley steps carry the rhythm.
# Light on -> logo: one steady pulse, P = 7/11 s (94.3 bpm) from LIGHT_T - 0.1, so the recap lands on
# beat 11, the badge bar on beat 8 and the final chord on beat 15 with the logo chime.

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
        dec = 0.9 * (220 / f0) ** 0.35 / (1 + 0.35 * (n - 1))        # higher partials die faster
        for det in (-0.6, 0.6):                                        # two strings, gentle beating
            s += amp * np.sin(2 * np.pi * (fn + det * n * 0.15) * tt + rng.random() * 6.28) * (
                0.55 * np.exp(-tt / (dec * 3.2)) + 0.45 * np.exp(-tt / (dec * 0.9)))
    att = np.clip(tt / 0.006, 0, 1)
    rel = np.clip((d - tt) / 0.35, 0, 1)
    hammer = fft_filter(noise(0.03), 800, 4000) * env_exp(0.03, 0.006) * 0.02 * vel
    s = s * att * rel
    s[:len(hammer)] += hammer
    s = fft_filter(s, 40, 2500 + 3500 * vel)                         # felt: soft top end
    cache[key] = s / 6.0
    return s / 6.0


PV = {
    "D": [50, 57, 62, 66], "A/C#": [49, 57, 61, 64], "Bm": [47, 54, 59, 62], "G": [43, 50, 59, 62],
    "Em7": [40, 50, 55, 59], "Asus4": [45, 52, 57, 62], "A": [45, 52, 57, 61], "D/F#": [42, 50, 57, 62],
    "Dfin": [38, 50, 57, 62, 66, 69],
}


def chord(ch, t, d, vel=0.55, roll=0.035, gain=1.0):
    for i, m in enumerate(PV[ch]):
        place(music, piano(m, d, vel), t + i * roll + rng.uniform(0, 0.006), gain * (1.15 if i == 0 else 0.85),
              -0.25 + 0.5 * i / max(1, len(PV[ch]) - 1))


def note(m, t, d=3.0, vel=0.6, gain=1.0):
    place(music, piano(m, d, vel), t, 0.9 * gain, 0.1)


strings = buf()


def pad(ch, t0, t1, gain, att=0.9):
    d = t1 - t0 + 0.8
    tt = T(d)
    s = np.zeros(len(tt))
    for m in PV[ch][1:]:
        f = midi(m + 12 if m < 52 else m)
        for det in (-0.10, -0.04, 0.03, 0.09):
            s += saw(f * 2 ** (det / 12), tt + rng.random())
    s = fft_filter(s, 160, 1300)
    env = np.clip(tt / att, 0, 1) * np.clip((d - tt) / 0.8, 0, 1)
    vib = 1 + 0.05 * np.sin(2 * np.pi * 4.6 * tt)
    place(strings, s * env * vib * 0.0075 * gain, t0)


F = FOOT_TS
# --- walk: rubato chords on every other footfall, melody joins in clip 2
walk = [("D", F[0] - 0.02), ("A/C#", F[2]), ("Bm", F[4]), ("G", F[6]), ("Em7", F[8])]
for i, (ch, t) in enumerate(walk):
    nxt = walk[i + 1][1] if i + 1 < len(walk) else BELL_T
    chord(ch, t, nxt - t + 1.6, vel=0.45 + 0.04 * i, gain=0.75 + 0.06 * i)
    pad(ch, t, nxt, 0.35 + 0.18 * i)
note(69, F[1], 2.0, 0.4, 0.5)                                     # soft upper voice in clip 1
note(66, F[3], 2.0, 0.4, 0.5)
for m, t in [(78, F[5]), (76, F[6]), (74, F[7]), (76, F[8]), (79, F[9])]:   # melody, clip 2
    note(m, t, 2.6, 0.55, 0.85)
# --- arrival: suspension on the doorbell, resolves just before the light
chord("Asus4", BELL_T - 0.02, 1.9, vel=0.5, gain=0.9)
pad("Asus4", BELL_T, 18.45, 0.9)
chord("A", 18.45, 1.3, vel=0.45, gain=0.7)
pad("A", 18.45, LIGHT_T - 0.1, 0.9)
note(76, 18.45, 1.6, 0.5, 0.7)

# --- steady pulse: light -> logo
P = 7.0 / 11.0
B0 = LIGHT_T - 0.1


def bt(k):
    return B0 + k * P


prog = [("G", 0), ("D/F#", 2), ("Em7", 4), ("Asus4", 6), ("A", 7), ("D", 8), ("Bm", 10), ("G", 12), ("A", 14)]
arp = {"G": [55, 59, 62, 67], "D/F#": [54, 57, 62, 66], "Em7": [52, 55, 59, 62], "Asus4": [57, 62, 64, 69],
       "A": [57, 61, 64, 69], "D": [57, 62, 66, 69], "Bm": [54, 59, 62, 66]}
for i, (ch, k) in enumerate(prog):
    k2 = prog[i + 1][1] if i + 1 < len(prog) else 15
    lift = min(1.0, k / 8)
    chord(ch, bt(k), (k2 - k) * P + 1.2, vel=0.5 + 0.25 * lift, gain=0.8 + 0.35 * lift, roll=0.02)
    pad(ch, bt(k), bt(k2), 1.0 + 0.9 * lift, att=0.6 if k else 1.2)
    e = 0
    while k + e * 0.5 < k2 - 0.01:                                 # 8th-note arpeggio, grows in
        m = arp[ch][[0, 1, 2, 3, 2, 1, 2, 3][e % 8]] + 12
        g = (0.18 + 0.32 * lift) * (1.0 if e % 2 == 0 else 0.7)
        if k + e * 0.5 >= 2:                                       # first bar: chord only, then motion
            place(music, piano(m, 1.6, 0.45 + 0.2 * lift), bt(k + e * 0.5) + rng.uniform(0, 0.005), g,
                  -0.3 + 0.6 * ((e % 4) / 3))
        e += 1
# melody over the pulse (beats, length)
mel = [(78, 0, 2), (81, 2, 2), (83, 4, 1.5), (81, 5.5, 0.5), (76, 6, 2), (78, 8, 2), (74, 10, 1), (76, 11, 1),
       (74, 12, 1.5), (73, 13.5, 1.5)]
for m, k, ln in mel:
    note(m, bt(k), ln * P + 1.5, 0.62 + 0.12 * min(1, k / 8), 1.0)
# heartbeat kick from bar 2, shaker 8ths from the badge bar
for k in range(4, 15):
    if k % 2 == 0 or k >= 8:
        tt = T(0.4)
        kick = np.sin(2 * np.pi * (48 + 60 * np.exp(-tt * 30)) * tt) * env_exp(0.4, 0.12)
        place(music, kick * (0.16 if k < 8 else 0.2) * (1.0 if k % 2 == 0 else 0.6), bt(k))
for e in range(16, 30):
    d = 0.06
    sh = fft_filter(noise(d), 5000, 12000) * np.sin(np.pi * T(d) / d)
    place(music, sh * (0.035 if e % 2 else 0.02), bt(e * 0.5), pan=0.3)
# swell into the final hit, then the resolution with the logo chime
d = 2 * P
tt = T(d)
sw = fft_filter(noise(d), 3000, 11000) * (tt / d) ** 2.5
place(music, sw * 0.05, bt(13))
fin = bt(15)
chord("Dfin", fin, 4.5, vel=0.8, gain=1.25, roll=0.012)
note(74, fin, 4.5, 0.7, 0.9)
pad("D", fin, DUR - 0.2, 2.0, att=0.3)
music += strings
music *= 0.17                                                     # sit at the old score's level
