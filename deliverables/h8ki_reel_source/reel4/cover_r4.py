"""Cover for Reel #4 (inside the profile grid's 3:4 crop, y 240..1680) + the "Cerita Kurir" highlight cover.
  python3 cover_r4.py OUTDIR"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
import render_r4 as R
from gfx import font, draw_text

OUT = sys.argv[1]
img = Image.new("RGBA", (R.W, R.H), R.BG + (255,))
R.part_pill(img, R.W / 2, 300)
draw_text(img, "Alamatnya cuma", font("b", 60), R.W / 2, 385, R.INK, shadow=0)
draw_text(img, "“pintu biru dekat masjid”", font("xb", 66), R.W / 2, 465, R.RED, shadow=0)
m, mask = R.draw_map(1.0)
img.paste(m, (R.MX, 540), mask)
R.label(img, "DI APLIKASI", R.MX + 18, 558, (255, 255, 255), R.INK + (230,))
card = Image.new("RGBA", (R.W, R.H), (0, 0, 0, 0))
R.status_card(card, 0.5)
img.alpha_composite(card.crop((0, 690, R.W, 900)), (0, 870))
fo = R.footage(2.7, R.H - 1080)                       # the courier asking, the old man smiling and pointing
img.paste(Image.fromarray(fo), (0, 1080))
R.label(img, "KENYATAANNYA", 30, 1106, R.INK, (255, 255, 255, 235))
out = img.convert("RGB")
out.save(os.path.join(OUT, "COVER_H8KI_Reel4_Kenyataannya2.jpg"), quality=97, subsampling=0)
out.save(os.path.join(OUT, "COVER_H8KI_Reel4_Kenyataannya2.png"))
L = "/home/user/LinkedERP_Odoo/deliverables/launch"
covs = [out, Image.open(f"{L}/reel3_tracking/COVER_H8KI_Reel3_Tracking.jpg"),
        Image.open(f"{L}/reel2_nenek/COVER_H8KI_Kiriman_untuk_Nenek_v4.jpg")]
g = Image.new("RGB", (3 * 360 + 8, 480), (255, 255, 255))
for i, c in enumerate(covs):
    g.paste(c.convert("RGB").crop((0, 240, 1080, 1680)).resize((360, 480), Image.LANCZOS), (i * 364, 0))
g.save(os.path.join(OUT, "grid_preview_reel4.jpg"), quality=92)

# highlight cover "Cerita Kurir": a film frame with a play button, white on dark navy (centre = the circle crop)
S = 4
big = Image.new("RGB", (1080 * S // 2, 1920 * S // 2), R.INK)
d = ImageDraw.Draw(big)
cx, cy, s = big.width / 2, big.height / 2, 300 * S / 2
d.rounded_rectangle((cx - 0.9 * s, cy - 0.62 * s, cx + 0.9 * s, cy + 0.62 * s), int(0.16 * s), fill=(255, 255, 255))
for k in range(5):                                    # film perforations
    x = cx - 0.66 * s + k * 0.33 * s
    for yy in (cy - 0.5 * s, cy + 0.42 * s):
        d.rounded_rectangle((x - 0.07 * s, yy, x + 0.07 * s, yy + 0.08 * s), int(0.02 * s), fill=R.INK)
d.polygon([(cx - 0.2 * s, cy - 0.26 * s), (cx - 0.2 * s, cy + 0.26 * s), (cx + 0.28 * s, cy)], fill=R.RED)
hc = big.resize((1080, 1920), Image.LANCZOS)
hc.save(os.path.join(OUT, "COVER_Cerita_Kurir.png"))
hc.crop((0, 420, 1080, 1500)).save(os.path.join(OUT, "COVER_Cerita_Kurir_square.png"))
print("ok")
