"""Shared timeline for picture and sound, so every SFX lands on its frame."""
import math

W, H, FPS = 1080, 1920, 30
DUR = 31.8
HOOK = 1.0                         # cold open prepended before the timeline

# Scene 1 - digital breakdown
QUERIES = [
    "Rumah cat hijau, sebelah warung Bu Ani",
    "Depan pohon mangga",
    "Masuk gang, mentok, belok kiri",
    "Pagar hitam",
    "Dekat masjid",
]
Q_START = 0.25
Q_DURS = [1.75, 1.55, 1.40, 1.25, 1.15]
TYPE_FRAC, SEARCH_FRAC = 0.55, 0.12


def query_windows():
    out, s = [], Q_START
    for q, d in zip(QUERIES, Q_DURS):
        type_end = s + TYPE_FRAC * d
        err = type_end + SEARCH_FRAC * d
        out.append(dict(text=q, start=s, type_end=type_end, err=err, end=s + d))
        s += d
    return out


QW = query_windows()
S1_END = QW[-1]["end"]            # ~7.35

# Scene 2 - surrender
GLITCH_END = 8.55
CRT_END = 9.05
POWER_END = 9.35
TYPE_GPS_START, TYPE_GPS_CPS = 9.55, 13.0     # chars / second
GPS_TEXT = "GPS menyerah."
S2_END = 11.0

# Scene 3 - human element
NIGHT_START = 10.9
TILT_START, TILT_END = 11.1, 13.5
WALK_START = 11.1
STEP = 0.5                         # seconds per footstep (brisk)
S3_END = 21.5
T1 = (11.9, 14.6)
T2 = (14.8, 18.1)
T3 = (18.3, 21.3)

# Scene 4 - delivery
S4_START = 21.5
WALKIN_END = 23.0
PLACE_START, PLACE_END = 23.0, 23.95
RUSTLE_T = 23.45
BELL_REACH, BELL_T = 24.0, 24.25
LIGHT_T = 24.6
BADGE_T = 25.05
LINE1_T, LINE2_T = 25.75, 26.35
S4_END = 27.6

# Scene 5 - recap (x -> check) then brand promise
RECAP_T = 27.6                     # crisp wipe to white
FLIP_TS = [28.0 + 0.2 * k for k in range(5)]
RECAP_OK = 29.05                   # "TIDAK DITEMUKAN" -> "DITEMUKAN"
LOGO_T = 29.6
CHIME_T = 29.7
TAG_T = 30.15


def footsteps_s3():
    t, out = WALK_START + 0.25, []
    while t < S3_END - 0.05:
        out.append(t)
        t += STEP
    return out


S4_STEP = 0.46


def footsteps_s4():
    t, out = S4_START + 0.12, []
    while t < WALKIN_END:
        out.append(t)
        t += S4_STEP
    return out


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lin(t, a, b):
    return clamp((t - a) / (b - a)) if b != a else float(t >= a)


def ease_io(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def back_out(x, s=1.9):
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1
