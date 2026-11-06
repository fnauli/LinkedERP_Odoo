"""Reel #4 "MISI KURIR #1", v2: same modern mission look, rebuilt around emotion.
- One continuous piece of music (Pixabay piano, already in Hoki's library) instead of stitched synth parts; its swell
  (track 50.74 s) lands on the frame the photo comes out of the box, and every cut sits on the track's beat (0.68 s).
- The stake is set early ("Paket dari anaknya. Sudah 3 Lebaran nggak pulang."), "MISI SELESAI" keeps one question
  open ("Hadiah misi: ???"), the reveal gets room (slow motion, no buttons on screen), and the game pays off in
  feeling: "Hadiah misinya: senyum Nenek." The asks wait for the closing card.
Re-uses the HUD drawing of render_misi.py.
  python3 render_misi2.py OUT.mp4 [preview t ...]"""
import sys, math, subprocess
from multiprocessing import Pool
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
from gfx import font, paste_layer, draw_text, check_icon, pop, back_in_out
from common import clamp, lin, ease_io, ease_out
import render_misi as M
import render_r4 as R

W, H, FPS = 1080, 1920, 24
GOLD, RED, GREEN, INK = M.GOLD, M.RED, M.GREEN, M.INK
BEAT = 0.68
T_REVEAL = 11.6                       # photo out of the box (k2 76) = the swell of the piano
TRACK_SWELL = 50.74
OFF = TRACK_SWELL - T_REVEAL          # track time = video time + OFF
END_T = 16.6                          # last footage frame; then the closing card
DUR = 18.6

M.SHOTS = [
    (0.0, 2.76, "k1", 73, 143, 1.0),     # asks the way; the old man smiles and points
    (2.76, 4.80, "k1", 152, 200, 0.3),   # walks towards the minaret
    (4.80, 6.84, "k1", 226, 262, 1.0),   # knocks on the blue door
    (6.84, 9.56, "k1", 274, 346, 1.0),   # the door opens, Nenek takes the parcel
    (9.56, T_REVEAL, "k2", 20, 76, 1.0),  # he bows and leaves, she opens the box
    (T_REVEAL, 12.9, "k2", 76, 97, 1.0),  # the photo comes out (0.67x)
    (12.9, END_T, "k2", 97, 121, 1.0),    # she holds it close, eyes closed (0.27x, near still)
]
st = M.src_time
T_ASK, T_DOOR, T_GIVE = st("k1", 133), st("k1", 238), st("k1", 320)
M.OBJ = [("Tanya warga", T_ASK), ("Cari masjid", 3.9), ("Temukan pintu biru", T_DOOR), ("Paket diterima", T_GIVE)]
HUD_IN, HUD_OUT = 1.45, (9.4, 9.85)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
SCRIM_TOP = np.clip((440 - yy) / 440, 0, 1)[..., None] ** 1.5


def done_banner(img, t):
    a, s, dy = pop(t, T_GIVE + 0.05, 0.5, 9.5, 0.35)
    if a <= 0:
        return
    L = Image.new("RGBA", (820, 210), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    d.rounded_rectangle((0, 0, 819, 209), 40, fill=(16, 18, 28, 225), outline=GOLD + (255,), width=5)
    L.alpha_composite(check_icon(84), (44, 30))
    d.text((150, 26), "MISI SELESAI", font=font("xb", 72), fill=GOLD)
    d.text((152, 126), "+400 XP   ·   Hadiah misi:  ???", font=font("sb", 34), fill=(255, 255, 255))
    paste_layer(img, L, W / 2, 330 + dy, a, s)


def caption(img, t, l1, l2, t1, t2, t_out, col2=GOLD, s1=70, s2=66):
    a1, sc1, d1 = pop(t, t1, 0.6, t_out, 0.45, rise=30)
    draw_text(img, l1, font("xb", s1), W / 2, 215 + d1, (255, 255, 255), a1, sc1, shadow=0.85, blur=14)
    if l2:
        a2, sc2, d2 = pop(t, t2, 0.6, t_out, 0.45, rise=30)
        draw_text(img, l2, font("xb", s2), W / 2, 310 + d2, col2, a2, sc2, shadow=0.85, blur=14)


LOGO_W = R.logo(380)


def closing(img, t):
    """The last frame softens and dims; the line, the logo and the two asks."""
    a, s, dy = pop(t, END_T + 0.25, 0.6)
    draw_text(img, "Ada yang menunggu", font("sb", 64), W / 2, 760 + dy, (255, 255, 255), a, s, shadow=0.8, blur=14)
    a, s, dy = pop(t, END_T + 0.55, 0.6)
    draw_text(img, "di ujung setiap alamat.", font("xb", 76), W / 2, 860 + dy, GOLD, a, s, shadow=0.85, blur=14)
    a, s, dy = pop(t, END_T + 0.9, 0.5)
    if a > 0:
        plate = Image.new("RGBA", (LOGO_W.width + 60, LOGO_W.height + 40), (0, 0, 0, 0))
        ImageDraw.Draw(plate).rounded_rectangle((0, 0, plate.width - 1, plate.height - 1), 28, fill=(255, 255, 255, 240))
        plate.alpha_composite(LOGO_W, (30, 20))
        paste_layer(img, plate, W / 2, 470 + dy, a, s)
    a, s, dy = pop(t, END_T + 1.1, 0.5)
    if a > 0:
        f = font("b", 40); txt = "Kirim ke yang lagi jauh dari keluarga"
        tw = f.getlength(txt)
        L = Image.new("RGBA", (int(tw) + 150, 96), (0, 0, 0, 0))
        ImageDraw.Draw(L).rounded_rectangle((0, 0, L.width - 1, 95), 48, fill=(16, 18, 28, 220))
        ImageDraw.Draw(L).text((40, 21), txt, font=f, fill=(255, 255, 255))
        L.alpha_composite(R.send_icon(56), (int(tw) + 62, 20))
        paste_layer(img, L, W / 2, 1110 + dy, a, s)
    a, s, dy = pop(t, END_T + 1.3, 0.5)
    if a > 0:
        f = font("b", 40); txt = "Follow buat Misi #2"
        L = Image.new("RGBA", (int(f.getlength(txt)) + 90, 96), (0, 0, 0, 0))
        ImageDraw.Draw(L).rounded_rectangle((0, 0, L.width - 1, 95), 48, fill=GREEN + (255,))
        ImageDraw.Draw(L).text((45, 20), txt, font=f, fill=(255, 255, 255))
        paste_layer(img, L, W / 2, 1230 + dy, a, s)


def frame(k):
    t = k / FPS
    f = M.footage(min(t, END_T - 1e-3)).astype(np.float32)
    hud_a = ease_out(lin(t, HUD_IN, HUD_IN + 0.35)) * (1 - ease_io(lin(t, *HUD_OUT)))
    low = max(1.0 if t < HUD_IN + 0.35 else 0.0, hud_a)
    top = max(ease_out(lin(t, 2.9, 3.2)) * (1 - ease_io(lin(t, 4.6, 4.9))),          # the stake
              ease_out(lin(t, T_GIVE, T_GIVE + 0.3)) * (1 - ease_io(lin(t, 9.4, 9.8))),  # mission done
              ease_out(lin(t, 10.0, 10.4)))                                         # the reveal
    f = f * (1 - 0.55 * low * M.SCRIM_LOW) * (1 - 0.62 * top * SCRIM_TOP)
    if t >= END_T:                                     # closing: soften and dim the last frame
        p = ease_io(lin(t, END_T, END_T + 0.7))
        small = cv2.resize(f, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        bl = cv2.resize(cv2.GaussianBlur(small, (0, 0), 1 + 5 * p), (W, H), interpolation=cv2.INTER_LINEAR)
        f = (f * (1 - p) + bl * p) * (1 - 0.55 * p)
    img = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).convert("RGBA")
    if t < HUD_IN + 0.35:                              # hook: the big mission card
        q = ease_io(lin(t, HUD_IN - 0.05, HUD_IN + 0.3))
        a = 1 - ease_out(lin(t, HUD_IN - 0.05, HUD_IN + 0.3))
        s = (1.1 - 0.1 * ease_out(lin(t, 0, 0.2))) * (1 - 0.25 * q)
        paste_layer(img, M.mission_card(t), W / 2 - 160 * q, 1300, a, s)
    if hud_a > 0:
        paste_layer(img, M.hud(t), 36 + 330 - 40 * (1 - hud_a), 1360, hud_a)
    caption(img, t, "Paket dari anaknya.", "Sudah 3 Lebaran nggak pulang.", 2.95, 3.35, 4.85, s2=58)
    done_banner(img, t)
    caption(img, t, "Isinya bukan barang...", None, 10.2, 0, T_REVEAL - 0.1)
    caption(img, t, "Isinya foto cucu", "yang belum pernah ia peluk.", T_REVEAL + 0.15, T_REVEAL + 0.75, 13.75)
    caption(img, t, "Hadiah misinya:", "senyum Nenek.", 14.1, 14.6, END_T + 0.05, s1=64, s2=88)
    if t >= END_T:
        closing(img, t)
    return np.asarray(img.convert("RGB"))


def frame_bytes(k):
    return frame(k).tobytes()


if __name__ == "__main__":
    out = sys.argv[1]
    if len(sys.argv) > 2:
        for tt in map(float, sys.argv[2:]):
            Image.fromarray(frame(int(round(tt * FPS)))).save(f"{out}_{tt:05.2f}.jpg", quality=90)
        sys.exit()
    n = int(round(DUR * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", "audio_misi2.wav", "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-tune", "film",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", "-shortest", out + ".master.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for b in pool.imap(frame_bytes, range(n), chunksize=4):
            p.stdin.write(b)
    p.stdin.close(); p.wait()
    for ps in (1, 2):
        c = ["ffmpeg", "-v", "error", "-y", "-i", out + ".master.mp4", "-c:v", "libx264", "-preset", "veryslow",
             "-b:v", "8000k", "-maxrate", "10000k", "-bufsize", "16000k", "-pix_fmt", "yuv420p", "-pass", str(ps),
             "-passlogfile", out + ".p2"]
        c += (["-an", "-f", "mp4", "/dev/null"] if ps == 1 else ["-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out])
        subprocess.run(c, check=True)
    print("done", out)
