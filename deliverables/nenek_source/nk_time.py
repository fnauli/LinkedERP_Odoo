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
        ("k2", 97, 121, 0.4)]    # the photo held to her, eyes closed: lingered at 0.4x

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

TRACK = "trk_emotional-cello.wav"
TRACK_SWELL = 35.782               # the cello's entry after its one-beat silence
REVEAL_T = 18.0                    # clip 2 frame 84: the photo frame faces camera
OFF = TRACK_SWELL - REVEAL_T       # track time = video time + OFF

# every text and accent sits on a cello onset
NOTIF_T = 0.03
T1A, T1B, T1_OUT = 1.4, 1.93, 4.4
NOTE_IN, NOTE_OUT = 3.72, 10.9
TICKS = [5.18, 7.64, 9.43]         # tanya warga / dekat masjid / pintu biru
STAKE_A, STAKE_B, STAKE_OUT = 9.97, 10.51, 12.6     # who is behind the door, and why it matters
KNOCKS = [8.958 + 20 / 24, 8.958 + 25 / 24]
LATCH_T, CREAK_T = 11.5, 11.62
BADGE_T, BADGE_OUT = 13.37, 15.6
GIFT_A, GIFT_B, GIFT_OUT = 18.72, 19.96, 21.75      # the payoff
DIM_T = 21.92
WAIT_A, WAIT_B = 22.27, 23.0       # 23.0 is the track's biggest hit
CARD_T = 24.43                     # white logo card + chime
TAG_A, TAG_B = 24.79, 25.13
CTA_T = 25.69
DUR = 28.2
