import sys, os
sys.path.insert(0, "../reel")
sys.argv = ["x", "/tmp/claude-0/-home-user-LinkedERP-Odoo/f8290da5-facb-5b8e-b306-57169bc461b3/scratchpad/pptx/_unused"]
import highlights as h
from PIL import Image, ImageDraw
os.makedirs("assets", exist_ok=True)
h.logo(600).save("assets/logo.png")
T = (0, 0, 0, 0); WH = (255, 255, 255, 255)
def ic(name, fn):
    S = 1600
    im = Image.new("RGBA", (S, S), T); d = ImageDraw.Draw(im)
    hole = fn(d, S / 2, S / 2, 600)
    if hole: d.ellipse(hole, fill=T)
    im = im.crop(im.getbbox()); im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
    im.save(f"assets/icon_{name}.png"); print(name, im.size)
ic("box", lambda d, x, y, s: h.icon_box(d, x, y, s, WH))
ic("pin", lambda d, x, y, s: h.icon_pin(d, x, y, s, WH))
ic("chat", lambda d, x, y, s: h.icon_chat(d, x, y, s, WH, T))
ic("star", lambda d, x, y, s: h.icon_star(d, x, y, s, WH))
# where the icon sits on the 1080x1920 cover (bbox of non-bg pixels)
import numpy as np
for n, c in [("Layanan", h.RED), ("Area", h.INDIGO), ("Cara_Order", h.GREEN), ("Testimoni", h.RED)]:
    a = np.asarray(Image.open(f"/home/user/LinkedERP_Odoo/deliverables/launch/highlights/COVER_{n}.png").convert("RGB")).astype(int)
    m = np.abs(a - np.array(c)).sum(2) > 60
    ys, xs = np.where(m); print(n, xs.min(), ys.min(), xs.max(), ys.max())
