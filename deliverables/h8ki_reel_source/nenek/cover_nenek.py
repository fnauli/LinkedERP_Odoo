"""Cover for Reel #2 'Kiriman untuk Nenek': Nenek's smile as she takes the parcel (clean footage, no badge),
two lines in the same layout as the Reel #1 cover, gold accent as in the film.
  python3 cover_nenek.py OUTDIR"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
import render_nenek as R
from gfx import font, draw_text, to_img

OUT = sys.argv[1]
K = int(round(14.9 * R.FPS))
arr = R.footage(K)
arr = arr * (1 - 0.66 * R.SCRIM_LOW)
img = to_img(arr)
draw_text(img, "3 Lebaran menunggu.", font("sb", 80), 540, 1335, (255, 255, 255), 1.0, 1.0, blur=14)
draw_text(img, "Akhirnya sampai.", font("xb", 100), 540, 1462, R.GOLD, 1.0, 1.0, blur=18)
img.save(os.path.join(OUT, "COVER_H8KI_Kiriman_untuk_Nenek_v4.png"))
img.save(os.path.join(OUT, "COVER_H8KI_Kiriman_untuk_Nenek_v4.jpg"), quality=98, subsampling=0)
# how it sits in the profile grid (3:4 centre crop) next to Reel #1
c1 = Image.open("/home/user/LinkedERP_Odoo/deliverables/launch/COVER_H8KI_Human_Algorithm_v29.jpg").convert("RGB")
g = Image.new("RGB", (3 * 360 + 8, 480), (255, 255, 255))
for i, im in enumerate([img, c1]):
    g.paste(im.crop((0, 240, 1080, 1680)).resize((360, 480), Image.LANCZOS), (i * 364, 0))
g.save(os.path.join(OUT, "grid_preview_reel2.jpg"), quality=92)
