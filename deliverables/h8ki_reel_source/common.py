"""Shared timeline for picture and sound, so every SFX lands on its frame."""
import math

W, H, FPS = 1080, 1920, 30
DUR = 32.3
HOOK = 1.0                         # cold open prepended before the timeline

# Scene 1 - digital breakdown
# ONE parcel whose address is only landmarks: the GPS tries each clue and fails on every one
QUERIES = [
    "Dekat masjid",
    "Depan pohon mangga",
    "Masuk gang, mentok, belok kiri",
    "Rumah cat hijau, pagar hitam",
    "Sebelah warung Bu Ani",
]
Q_START = 0.25
Q_DURS = [1.10, 1.30, 1.70, 1.60, 1.40]
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
# hand-over (same window as before, no added time)
BELL_REACH, BELL_T = 23.15, 23.4   # rings with the parcel still in hand
LIGHT_T = 23.85
DOOR_OPEN_T = 24.25                # recipient opens the door
REC_OUT = (24.75, 25.3)            # recipient steps out to the gate
STEP_FWD = (24.7, 25.15)           # courier steps forward
STEP_FWD_T = 24.95
OFFER = (24.95, 25.45)             # parcel held out at chest height
TAKE = (25.15, 25.45)              # recipient's hands reach the box
GIVE_T = 25.85                     # both hands on the box until here
RUSTLE_T = 25.5
NOD = (25.95, 26.6)                # courier's small nod
BADGE_T = 25.9
LINE1_T, LINE2_T = 26.35, 26.75
S4_END = 27.6

# Scene 5 - recap (x -> check) then brand promise
RECAP_T = 27.6                     # cut to the dark recap
FLIP_TS = [28.0 + 0.2 * k for k in range(5)]
RECAP_OK = 29.05                   # big green "KETEMU."
LOGO_T = 30.1
CHIME_T = 30.2
TAG_T = 30.65


# ---------------------------------------------------------------- REAL (Kling live-action) cut
import os
REAL = os.environ.get("REAL") == "1"
if REAL:
    FPS = 24                     # native frame rate of the Kling footage: no 24->30 judder
    # four Kling clips replace the drawn night + delivery scenes: (film start, film end, source offset)
    # One musical grid for the whole night: 96 bpm, beat k at GRID_A + k * BEAT, bars of 4 from GRID_A.
    # Source offsets were chosen so his footfalls, the house light and the handover land on beats;
    # the graphics (badge, recap, flips, logo) are placed on the same grid.
    BEAT, GRID_A = 0.625, 11.19
    CLIPS = {1: (10.9, 14.4, 0.82), 2: (14.4, 17.6, 0.625), 3: (17.6, 22.1, 0.185), 4: (22.1, 26.19, 0.51)}   # clip 4 = take 2 (fixed face): release at src 2.1 s -> beat 20
    NIGHT_START, WALK_START, S3_END = 10.9, 10.9, 17.6
    T1, T2, T3 = (11.5, 14.3), (14.94, 17.5), (19.94, 22.0)
    S4_START = WALKIN_END = 17.6
    BELL_REACH, BELL_T = 17.665, 17.815              # clip-3 events follow its footage (offset -0.115)
    STEP_FWD_T, REC_OUT = 18.915, (19.015, 19.115)
    LIGHT_T, DOOR_OPEN_T = 19.315, 19.815            # light = beat 13
    GIVE_T, RUSTLE_T, BADGE_T = 23.69, 23.39, 23.69  # handover + badge = bar 5 downbeat (beat 20)
    LINE1_T, LINE2_T = 24.315, 24.94                 # beats 21, 22
    S4_END = RECAP_T = 26.19                         # bar 6 downbeat (beat 24)
    FLIP_TS = [26.19 + 0.3125 + 0.15625 * k for k in range(5)]   # 16ths from the off-beat
    RECAP_OK = 27.44                                 # beat 26
    LOGO_T, CHIME_T, TAG_T = 28.59, 28.69, 29.315    # chime = bar 7 downbeat (beat 28), tag = beat 29
    DUR = 30.94


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


if REAL:
    # heel strikes measured from the Kling footage (clips 1-2): the backpack's walking bob, checked frame by
    # frame against the feet. Clip 3 has no steps (he stands at the gate), only a small weight shift.
    # Each sound is moved at most one frame (42 ms) towards the beat, so the steps and the music agree.
    FOOT_TS = [11.19, 11.815, 12.44, 13.065, 13.69, 14.315, 14.924, 15.565, 16.19, 16.829]
    SHIFT_T = 18.455

    def footsteps_s3():
        return list(FOOT_TS)

    def footsteps_s4():
        return []


V2 = os.environ.get("V2") == "1"
if V2:
    # Kling v2 cut: one 96 bpm grid (beat k = GRID_A + k * BEAT); every shot boundary sits on a beat.
    BEAT, GRID_A = 0.625, 11.15

    def bt(k):
        return GRID_A + k * BEAT

    # (timeline start, timeline end, frame folder, first source frame, speed, dissolve-in seconds)
    H_START = bt(28) - (53 - 41) / 0.75 / 24          # handover: she holds it fully (src 53) exactly on beat 28
    SHOTS = [
        (10.9, bt(5), "../new/a2", 1, 0.885, 0.0),        # mosque, rebuilt: dusk exposure, push-in, mist, rain
        (bt(5), bt(9), "../new/a2", 92, 1.0, 0.35),       # under the trees, the landmark
        (bt(9), bt(15), "../new/d", 46, 0.833, 0.35),    # dead end, gentle slow motion: stops, wipes sweat, turns
        (bt(15), bt(19), "../new/a2", 240, 1.0, 0.0),     # the ibu points the way, he walks on smiling
        (bt(19), bt(23), "../new/b2", 1, 1.0, 0.0),       # rings the bell: the music falls silent
        (bt(23), H_START, "../new/b2", 64, 1.0, 0.0),     # the gate opens: the music returns, warm
        (H_START, bt(34), "../new/h", 41, 0.75, 0.0),    # handover, gentle 0.75x: release, bow, hand on chest
    ]
    NIGHT_START, WALK_START = 10.9, 10.9
    T1 = (bt(13.6), bt(19) - 0.2)                     # "Kurir kami tidak." as he turns back determined
    T2 = (bt(23) + 0.15, H_START - 0.1)               # "Buat yang kirim..." as the gate opens
    T3 = (bt(30.5), bt(34) - 0.15)                    # "Satu paket, satu penghasilan." over his hand on chest
    S4_START = WALKIN_END = S3_END = bt(19)
    BELL_REACH, BELL_T = bt(19), bt(19) + 0.35        # ding-dong on finger contact (frame 7-17 of clip B)
    LIGHT_T = bt(23) + 0.05
    DOOR_OPEN_T = bt(23) + (100 - 64) / 24             # gate latch in Clip B shot 2
    GIVE_T = BADGE_T = bt(28)                          # she holds the parcel = badge = key lift
    RUSTLE_T = bt(28) - 0.2
    LINE1_T = LINE2_T = 99.0
    S4_END = RECAP_T = bt(34)
    FLIP_TS = [bt(34.5) + 0.15625 * k for k in range(5)]
    RECAP_OK = bt(36)
    LOGO_T, CHIME_T, TAG_T = bt(38) - 0.1, bt(38), bt(39)
    DUR = bt(38) + 3.2                                 # room for the comment invitation
    FOOT_TS, SHIFT_T = [], None
    STEP_FWD_T, REC_OUT = bt(20), (bt(20), bt(20) + 0.1)

    def footsteps_s3():
        return []

    def footsteps_s4():
        return []


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
