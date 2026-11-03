"""Cover for Reel #3: the same split, rearranged so everything sits inside the profile grid's 3:4 crop
(y 240..1680): hook, stuck dot + 10:00 card, and the courier's puzzled face.
  python3 cover_r3.py OUTDIR"""
import sys, os
import numpy as np, cv2
from PIL import Image, ImageDraw
import render_r3 as R
from gfx import font, draw_text

OUT = sys.argv[1]
img = Image.new("RGBA", (R.W, R.H), R.BG + (255,))
draw_text(img, "Titik kurir diem", font("xb", 84), R.W / 2, 330, R.INK, shadow=0)
draw_text(img, "10 menit?", font("xb", 100), R.W / 2, 432, R.RED, shadow=0)
m, mask = R.draw_map(1.9)
img.paste(m, (R.MX, 520), mask)
R.label(img, "DI APLIKASI", R.MX + 18, 538, (255, 255, 255), R.INK + (230,))
card = Image.new("RGBA", (R.W, R.H), (0, 0, 0, 0))
R.status_card(card, 1.9)                       # drawn centred at y 800; move it under the map
img.alpha_composite(card.crop((0, 690, R.W, 900)), (0, 880))
# the courier, puzzled (dead-end take, frame 108), filling the lower part
a = R.raw("d2", 108)
cw = 760; ch = cw * (R.H - 1090) / R.W
x0, y0 = 594 - cw / 2, 820 - ch / 2
M = np.float32([[R.W / cw, 0, -x0 * R.W / cw], [0, (R.H - 1090) / ch, -y0 * (R.H - 1090) / ch]])
fo = cv2.warpAffine(a, M, (R.W, R.H - 1090), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
img.paste(Image.fromarray(fo), (0, 1090))
R.label(img, "KENYATAANNYA", 30, 1116, R.INK, (255, 255, 255, 235))
out = img.convert("RGB")
out.save(os.path.join(OUT, "COVER_H8KI_Reel3_Tracking.jpg"), quality=97, subsampling=0)
out.save(os.path.join(OUT, "COVER_H8KI_Reel3_Tracking.png"))
# profile grid preview: Reel 3 next to Reels 2 and 1 (3:4 centre crops)
L = "/home/user/LinkedERP_Odoo/deliverables/launch"
covs = [out, Image.open(f"{L}/reel2_nenek/COVER_H8KI_Kiriman_untuk_Nenek_v4.jpg"),
        Image.open(f"{L}/COVER_H8KI_Human_Algorithm_v29.jpg")]
g = Image.new("RGB", (3 * 360 + 8, 480), (255, 255, 255))
for i, c in enumerate(covs):
    g.paste(c.convert("RGB").crop((0, 240, 1080, 1680)).resize((360, 480), Image.LANCZOS), (i * 364, 0))
g.save(os.path.join(OUT, "grid_preview_reel3.jpg"), quality=92)
print("ok")
