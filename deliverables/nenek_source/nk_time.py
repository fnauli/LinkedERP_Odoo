"""'Kiriman untuk Nenek' timeline (24 fps). Every overlay and accent sits on an onset of the piano
track, and the track's swell (50.69 s) lands on the frame the family photo comes out of the box."""
FPS = 24
# (clip, first src frame, last src frame, speed)
SEGS = [("k1", 1, 72, 1.0),      # shot 1: GPS fails at the alley mouth
        ("k1", 73, 143, 1.0),    # shot 2: asks the old man, he points
        ("k1", 144, 215, 1.0),   # shot 3: walks to the minaret (logo fixed)
        ("k1", 216, 269, 1.0),   # shot 4: blue door, knocks
        ("k1", 270, 350, 1.0),   # shot 5: Nenek opens, two-handed handover
        ("k2", 2, 96, 1.0),      # clip 2: he bows and leaves, she opens the box (seamless join)
        ("k2", 97, 121, 0.5)]    # the photo against her heart, lingered at half speed

SRC = []                          # output frame -> (clip, fractional src frame, segment)
for si, (c, a, b, sp) in enumerate(SEGS):
    n = round((b - a + 1) / sp)
    for j in range(n):
        SRC.append((c, min(b, a + j * sp), si))
SEG_T = []
_k = 0
for si, (c, a, b, sp) in enumerate(SEGS):
    SEG_T.append(_k / FPS)
    _k += round((b - a + 1) / sp)
FOOT_END = len(SRC) / FPS          # 20.625 s

TRACK_SWELL = 50.69
REVEAL_T = 18.0                    # clip 2 frame 84: the photo frame faces camera
OFF = TRACK_SWELL - REVEAL_T       # track time = video time + OFF

NOTIF_T = 0.03
T1A, T1B, T1_OUT = 1.9, 2.64, 4.5
NOTE_IN, NOTE_OUT = 3.31, 10.92
TICKS = [5.59, 7.5, 9.48]          # tanya warga / dekat masjid / pintu biru
KNOCKS = [8.958 + 20 / 24, 8.958 + 25 / 24]
LATCH_T, CREAK_T = 11.5, 11.62
BADGE_T, BADGE_OUT = 13.56, 15.9
RUSTLE_T = 16.3
GIFT_A, GIFT_B, GIFT_OUT = 18.67, 19.28, 20.45
DIM_T = 20.03
WAIT_A, WAIT_B = 20.58, 21.01
CARD_T = 22.56                     # white logo card + chime
TAG_A, TAG_B = 23.08, 23.34
CTA_T = 24.13
DUR = 26.4
