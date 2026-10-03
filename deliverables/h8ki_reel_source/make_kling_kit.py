"""Clean start frames + character refs for Kling image-to-video (no text, no logos)."""
import math
from PIL import Image, ImageDraw
import gfx

# Clean mode: no captions/tags, and logos become a plain white label panel.
_orig_text = ImageDraw.ImageDraw.text
def _text(self, xy, text, *a, **k):
    if any(w in str(text) for w in ("H8KI", "LOGISTIK", "No. 8", "WARUNG", "BU ANI")):
        return
    return _orig_text(self, xy, text, *a, **k)
ImageDraw.ImageDraw.text = _text
gfx.draw_text = lambda *a, **k: None
gfx.draw_chip = lambda *a, **k: None

import scene_night as SN, scene_house as SH
SN.draw_text = SH.draw_text = gfx.draw_text
SN.draw_chip = SH.draw_chip = gfx.draw_chip
SH.badge = lambda: Image.new("RGBA", (1, 1))

OUT = "/home/user/LinkedERP_Odoo/deliverables/kling_kit/"
frames = {
    "clip1_establishing_start.png": lambda: gfx.to_img(SN.scene3(13.7)),
    "clip2_tracking_start.png": lambda: gfx.to_img(SN.scene3(17.2)),
    "clip3_arrival_start.png": lambda: SH.scene4(23.05, raw=True),
    "clip4_handover_start.png": lambda: SH.scene4(25.5, raw=True),
}
for name, fn in frames.items():
    fn().save(OUT + name)
    print("saved", name)

# character reference sheet: back view + side view on a neutral backdrop
bg = (58, 66, 96)
spr, _, _ = SN.courier_back(math.pi * 0.5, 0)
spr = spr.resize((spr.width * 2, spr.height * 2), Image.LANCZOS)
ref = Image.new("RGB", (1080, 1920), bg)
ref.paste(spr, ((1080 - spr.width) // 2, 1920 - spr.height - 120), spr)
ref.save(OUT + "courier_ref_back.png")
side, (ox, oy), _ = SH.courier_side(450, 0.0, 0.0, 0.0, 0.0, "carry", 0.0)
side = side.resize((side.width * 2, side.height * 2), Image.LANCZOS)
ref = Image.new("RGB", (1080, 1920), bg)
ref.paste(side, ((1080 - side.width) // 2, 1920 - side.height - 120), side)
ref.save(OUT + "courier_ref_side.png")
print("refs saved")
