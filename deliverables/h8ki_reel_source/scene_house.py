"""Scene 4 (delivery at the green house) and Scene 5 (brand end card)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *
from gfx import *
import scene_night as SN

S = 2
GROUND = 1660      # street level (feet)
TERRACE = 1604     # terrace floor
LIFT = 200
PPM = 365          # px per metre (1x)
PKG_POS = (560, TERRACE)   # where the parcel is set down (bottom centre)
BELL = (392, 1318)
DOOR = (430, 870, 740, TERRACE)
LAMP = (585, 800)


def night(c, k=1.0):
    return tuple(int(v) for v in SN.night_col(c, k))


def make_branch():
    """Mango branch framing top-left, drawn as its own foreground layer (defocused)."""
    im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = lambda *v: [x * S for x in v]
    # mango branch framing top-left
    r = np.random.default_rng(9)
    d.line(s(-40, 250, 260, 330), fill=(28, 22, 22, 255), width=22 * S)
    d.line(s(120, 290, 330, 470), fill=(28, 22, 22, 255), width=12 * S)
    for _ in range(220):
        cx, cy = r.uniform(-40, 380), r.uniform(180, 520) - max(0, r.uniform(-40, 380) - 250) * 0.3
        a = r.uniform(0, math.pi)
        L = r.uniform(40, 80)
        c = int(r.uniform(22, 55))
        ca, sa = math.cos(a), math.sin(a)
        wv = L * 0.28
        pts = [(cx, cy), (cx + L * 0.5 * ca - wv * sa, cy + L * 0.5 * sa + wv * ca), (cx + L * ca, cy + L * sa),
               (cx + L * 0.5 * ca + wv * sa, cy + L * 0.5 * sa - wv * ca)]
        rim = r.random() < 0.3
        col = (c // 2 + 30, c + 50, c + 60) if rim else (c // 2, c + 5, c + 8)
        d.polygon([(px * S, py * S) for px, py in pts], fill=col)
    for (mx, my) in [(170, 470), (250, 520), (90, 430)]:
        d.ellipse(s(mx - 16, my - 12, mx + 16, my + 32), fill=night((180, 200, 90), 1.2))
    lay = im.resize((W, H), Image.LANCZOS).crop((0, 0, 520, 640))
    return lay.filter(ImageFilter.GaussianBlur(4.5))


def build_house(lit):
    im = Image.new("RGB", (W * S, H * S))
    # sky: bottom of the night sky, moon upper right
    sky = SN.SKY[SN.SKY_H - H:].copy()
    im.paste(Image.fromarray(sky.astype(np.uint8)).resize((W * S, H * S)))
    d = ImageDraw.Draw(im)
    s = lambda *v: [x * S for x in v]
    # neighbour roofs far back
    d.polygon(s(0, 560, 300, 430, 1080, 430, 1080, 700, 0, 700), fill=night((70, 60, 90), 0.8))
    # roof (terracotta) with eave
    d.polygon(s(-40, 650, 150, 470, 930, 470, 1000, 650), fill=night((170, 80, 60)))
    for k in range(9):
        y = 480 + k * 20
        d.line(s(150 - (y - 470) * 1.05, y, 930 + (y - 470) * 0.39, y), fill=night((120, 55, 45)), width=3 * S)
    d.rectangle(s(-40, 640, 1000, 668), fill=night((90, 40, 36)))
    # green house wall
    wall = (80, 175, 125)
    d.rectangle(s(-40, 668, 880, TERRACE), fill=night(wall))
    d.rectangle(s(-40, 668, 880, 700), fill=night(wall, 0.6))    # eave shadow
    d.rectangle(s(-40, TERRACE - 70, 880, TERRACE), fill=night((70, 120, 110), 0.8))  # plinth tiles
    # door
    x0, y0, x1, y1 = DOOR
    d.rectangle(s(x0 - 18, y0 - 60, x1 + 18, y1), fill=night((235, 235, 220), 0.9))
    d.rectangle(s(x0, y0 - 48, x1, y0 - 8), fill=(255, 200, 120) if lit else night((70, 90, 130)))
    d.rectangle(s(x0, y0, x1, y1), fill=night((40, 120, 80), 1.1))
    mid = (x0 + x1) / 2
    d.line(s(mid, y0, mid, y1), fill=night((20, 60, 40)), width=4 * S)
    for (a, b) in [(x0 + 22, mid - 20), (mid + 20, x1 - 22)]:
        d.rectangle(s(a, y0 + 40, b, y0 + 300), outline=night((20, 70, 45)), width=5 * S)
        d.rectangle(s(a, y0 + 360, b, y1 - 40), outline=night((20, 70, 45)), width=5 * S)
    d.ellipse(s(mid - 38, 1250, mid - 18, 1270), fill=(200, 170, 90) if lit else night((200, 170, 90)))
    # window with teralis + curtain
    wx0, wy0, wx1, wy1 = 70, 930, 330, 1250
    d.rectangle(s(wx0 - 16, wy0 - 16, wx1 + 16, wy1 + 16), fill=night((235, 235, 220), 0.9))
    d.rectangle(s(wx0, wy0, wx1, wy1), fill=(255, 196, 110) if lit else night((60, 80, 130)))
    d.polygon(s(wx0, wy0, wx0 + 90, wy0, wx0 + 60, wy1, wx0, wy1), fill=(215, 120, 70) if lit else night((110, 90, 120)))
    d.polygon(s(wx1, wy0, wx1 - 70, wy0, wx1 - 40, wy1, wx1, wy1), fill=(215, 120, 70) if lit else night((110, 90, 120)))
    for k in range(1, 6):
        xx = wx0 + (wx1 - wx0) * k / 6
        d.line(s(xx, wy0, xx, wy1), fill=(22, 22, 28), width=5 * S)
    for k in range(1, 4):
        yy = wy0 + (wy1 - wy0) * k / 4
        d.line(s(wx0, yy, wx1, yy), fill=(22, 22, 28), width=4 * S)
    # house number plate: No. 8
    d.rounded_rectangle(s(x0 - 160, y0 - 76, x0 - 30, y0 - 12), 10 * S, fill=night((245, 245, 235), 1.3),
                        outline=night((40, 40, 50)), width=3 * S)
    d.text(s(x0 - 95, y0 - 43), "No. 8", font=font("xb", 34 * S), fill=night((25, 25, 35), 1.0), anchor="mm")
    # porch lamp
    lx, ly = LAMP
    d.rectangle(s(lx - 6, ly - 50, lx + 6, ly - 20), fill=(30, 30, 36))
    d.ellipse(s(lx - 22, ly - 26, lx + 22, ly + 18), fill=(255, 240, 200) if lit else night((180, 180, 170)))
    # Warung Bu Ani next door
    d.rectangle(s(880, 700, 1080, GROUND), fill=night((210, 190, 150)))
    d.rectangle(s(880, 690, 1080, 720), fill=night((120, 70, 50)))
    for k in range(14):
        y = 1010 + k * 42
        d.rectangle(s(900, y, 1080, y + 34), fill=night((120, 110, 100)))
    d.rectangle(s(890, 790, 1080, 960), fill=night((30, 90, 170), 1.2))
    d.rectangle(s(890, 790, 1080, 960), outline=night((255, 255, 255)), width=4 * S)
    d.text(s(985, 840), "WARUNG", font=font("xb", 42 * S), fill=night((255, 235, 120), 1.4), anchor="mm")
    d.text(s(985, 905), "BU ANI", font=font("xb", 42 * S), fill=night((255, 255, 255), 1.4), anchor="mm")
    for k in range(6):   # hanging sachet strips
        x = 900 + k * 30
        d.rectangle(s(x, 965, x + 18, 1000 + (k % 3) * 20), fill=night([(220, 60, 60), (60, 160, 220), (240, 200, 60)][k % 3]))
    # terrace + step + street
    d.rectangle(s(-40, TERRACE, 880, GROUND), fill=night((190, 180, 170), 0.9))
    d.rectangle(s(-40, TERRACE, 880, TERRACE + 10), fill=night((230, 225, 215)))
    d.rectangle(s(-40, GROUND, 1080, H), fill=night((140, 140, 150)))
    for k in range(6):
        y = GROUND + 30 + k * k * 12
        d.line(s(0, y, W, y), fill=night((110, 110, 125)), width=2 * S)
    d.rectangle(s(-40, GROUND, 1080, GROUND + 22), fill=night((80, 80, 95)))
    # black iron fence (pagar hitam) with pillars, gate open
    black = (18, 18, 24)
    for (a, b) in [(-40, 350), (800, 880)]:
        d.rectangle(s(a, 1250, b, 1266), fill=black)
        d.rectangle(s(a, 1560, b, 1576), fill=black)
        x = a + 10
        while x < b:
            d.rectangle(s(x, 1236, x + 9, TERRACE), fill=black)
            d.polygon(s(x - 5, 1240, x + 14, 1240, x + 4.5, 1212), fill=black)
            x += 36
    # gate leaves swung inward (foreshortened)
    for (a, sign) in [(400, 1), (760, -1)]:
        for k in range(4):
            x = a + sign * (8 + k * 18)
            d.rectangle(s(min(x, x + 7), 1280 - k * 6, max(x, x + 7), TERRACE - 20 - k * 4), fill=black)
        d.line(s(a, 1285, a + sign * 70, 1262), fill=black, width=6 * S)
    for px in (350, 760):
        d.rectangle(s(px, 1170, px + 50, TERRACE), fill=night((225, 225, 215)))
        d.rectangle(s(px - 8, 1150, px + 58, 1176), fill=night((200, 200, 190)))
    # doorbell on the left pillar
    bx, by = BELL
    d.rounded_rectangle(s(bx - 14, by - 20, bx + 14, by + 20), 5 * S, fill=night((240, 240, 240)))
    d.ellipse(s(bx - 7, by - 7, bx + 7, by + 7), fill=(220, 40, 40))
    img = im.resize((W, H), Image.LANCZOS)
    arr = to_arr(img)
    if lit:
        warm = np.array([255, 170, 90], np.float32)
        light = np.zeros((H, W, 1), np.float32)
        yy, xx = np.mgrid[0:H, 0:W]
        light[..., 0] += np.exp(-(((xx - LAMP[0]) / 520) ** 2 + ((yy - LAMP[1] - 350) / 700) ** 2)) * 1.0
        light[..., 0] += np.exp(-(((xx - 200) / 260) ** 2 + ((yy - 1090) / 320) ** 2)) * 0.5
        # spill through the gate opening onto the street
        light[..., 0] += np.exp(-(((xx - 580) / 300) ** 2 + ((yy - 1720) / 180) ** 2)) * 0.9
        # fence bars cast long shadows toward the viewer
        sh = Image.new("L", (W, H), 0)
        ds = ImageDraw.Draw(sh)
        for a in list(range(-30, 350, 36)) + list(range(810, 880, 36)):
            x = a + 14
            ex = LAMP[0] + (x - LAMP[0]) * 2.1
            ds.polygon([(x, GROUND), (x + 9, GROUND), (ex + 20, H), (ex, H)], fill=150)
        sh = np.asarray(sh.filter(ImageFilter.GaussianBlur(4)), np.float32)[..., None] / 255
        light = light * (1 - sh * (yy[..., None] > GROUND))
        arr = arr * (1 + light * 1.6 * np.array([1.25, 0.95, 0.6])) + light * warm * 0.28
    return np.clip(arr, 0, 255)


HOUSE_DARK = build_house(False)
HOUSE_LIT = build_house(True)
BRANCH = make_branch()
_dr = np.random.default_rng(44)
DUST = [(_dr.uniform(430, 760), _dr.uniform(0, 720), _dr.uniform(8, 22), _dr.uniform(0, 6.28)) for _ in range(28)]


def _soften_sky(a):
    b = to_arr(to_img(a).filter(ImageFilter.GaussianBlur(2.2)))
    m = np.clip((470 - np.arange(H)) / 50.0, 0, 1)[:, None, None].astype(np.float32)
    return a * (1 - m) + b * m


HOUSE_DARK, HOUSE_LIT = _soften_sky(HOUSE_DARK), _soften_sky(HOUSE_LIT)
try:
    from scene_night import BUSH as _BUSH
except Exception:
    _BUSH = None
FG_L = _BUSH.resize((560, 560)).filter(ImageFilter.GaussianBlur(16)) if _BUSH else None
FG_R = FG_L.transpose(Image.FLIP_LEFT_RIGHT) if FG_L else None


def draw_parcel(d, P, c, m, k=S):
    """Branded H8KI parcel centred at scene point c."""
    pw, ph_ = 0.3 * m, 0.24 * m
    cx, cy = c
    d.rounded_rectangle((*P(cx - pw / 2, cy - ph_ / 2), *P(cx + pw / 2, cy + ph_ / 2)), 8 * k, fill=(255, 70, 58, 255))
    d.rectangle((*P(cx - pw / 2, cy + ph_ * 0.22), *P(cx + pw / 2, cy + ph_ * 0.32)), fill=(0, 150, 72, 255))
    d.text(P(cx, cy - ph_ * 0.08), "H8KI", font=font("xb", 25 * k), fill=(255, 255, 255, 255), anchor="mm")
    return c


def recipient(img, x, feet, hand_tgts, warm, alpha=1.0, bob=0.0, sway=0.0, breath=0.0, nod=0.0):
    """Recipient (hijab, long dress) facing left, backlit gold from the doorway."""
    m = PPM
    ox, oy = x - 260, feet - 700
    lay = Image.new("RGBA", (520 * S, 740 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    P = lambda px, py: ((px - ox) * S, (py - oy) * S)
    fy = feet - bob
    rim = (255, 204, 128, 255)
    dress, hij, skin = (112, 70, 116, 255), (222, 176, 124, 255), (182, 124, 96, 255)
    sh = (x - 0.03 * m, fy - 1.26 * m)

    def body(off, cd, ch, cs):
        o = lambda p: (p[0] + off[0], p[1] + off[1])
        d.polygon([P(*o((x - 0.24 * m, fy))), P(*o((x + 0.24 * m, fy))), P(*o((x + 0.17 * m, fy - 1.28 * m))),
                   P(*o((x - 0.17 * m, fy - 1.28 * m)))], fill=cd)
        d.polygon([P(*o((x - 0.21 * m + sway, fy - 1.12 * m - breath))), P(*o((x + 0.21 * m + sway * 0.7, fy - 1.12 * m - breath))),
                   P(*o((x + 0.11 * m, fy - 1.42 * m))), P(*o((x - 0.11 * m, fy - 1.42 * m)))], fill=ch)
        hc = o((x - 3 * nod, fy - 1.45 * m + 6 * nod - breath))
        d.ellipse((*P(hc[0] - 0.125 * m, hc[1] - 0.14 * m), *P(hc[0] + 0.125 * m, hc[1] + 0.12 * m)), fill=ch)
        if cs:
            d.ellipse((*P(hc[0] - 0.105 * m, hc[1] - 0.075 * m), *P(hc[0] + 0.01 * m, hc[1] + 0.085 * m)), fill=cs)
            d.ellipse((*P(hc[0] - 0.07 * m, hc[1] - 0.02 * m), *P(hc[0] - 0.052 * m, hc[1])), fill=(30, 20, 20, 255))
            d.arc((*P(hc[0] - 0.08 * m, hc[1] + 0.015 * m), *P(hc[0] - 0.035 * m, hc[1] + 0.05 * m)), 20, 160,
                  fill=(90, 40, 40, 255), width=3 * S)

    body((5, -3), rim, rim, None)
    body((0, 0), dress, hij, skin)
    for i, tg in enumerate(hand_tgts or [(x - 0.08 * m, fy - 0.72 * m), (x - 0.02 * m, fy - 0.72 * m)]):
        s0 = (sh[0] + (0.02 * m if i else 0), sh[1])
        e, h = ik(s0[0], s0[1], tg[0], tg[1], 0.28 * m, 0.27 * m, bend=-1)
        col = dress if i == 0 else tuple(int(c * 0.8) for c in dress[:3]) + (255,)
        for a, b, w in ((s0, e, 30), (e, h, 26)):
            d.line([P(*a), P(*b)], fill=col, width=w * S)
            for q in (a, b):
                q = P(*q)
                d.ellipse((q[0] - w * S / 2, q[1] - w * S / 2, q[0] + w * S / 2, q[1] + w * S / 2), fill=col)
        q = P(*h)
        d.ellipse((q[0] - 15 * S, q[1] - 15 * S, q[0] + 15 * S, q[1] + 15 * S), fill=skin)
    lay = lay.resize((520, 740), Image.LANCZOS)
    if alpha < 0.999:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
    img.paste(lay, (int(ox), int(oy)), lay)


def ik(sx, sy, tx, ty, l1, l2, bend=1):
    dx, dy = tx - sx, ty - sy
    dd = min(math.hypot(dx, dy), l1 + l2 - 0.5)
    a = math.atan2(dy, dx)
    c = (l1 * l1 + dd * dd - l2 * l2) / (2 * l1 * dd)
    b = math.acos(max(-1, min(1, c)))
    ea = a + bend * b
    ex, ey = sx + l1 * math.cos(ea), sy + l1 * math.sin(ea)
    hx, hy = ex + l2 * math.cos(math.atan2(ty - ey, tx - ex)), ey + l2 * math.sin(math.atan2(ty - ey, tx - ex))
    return (ex, ey), (hx, hy)


def courier_side(x, phi, walk, bend, reach, carry, warm, pbox=None, hands=None, nod=0.0):
    """Side view facing right. Returns RGBA canvas (1x) + its top-left and parcel centre if carried."""
    ox, oy = x - 450, 900
    im = Image.new("RGBA", (900 * S, 800 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    P = lambda px, py: ((px - ox) * S, (py - oy) * S)
    m = PPM
    L1 = L2 = 0.45 * m
    rimc = tuple(int(v) for v in (np.array([118, 146, 205]) * (1 - warm) + np.array([255, 190, 120]) * warm)) + (255,)
    navy, pants, red, redd, green = (36, 50, 92, 255), (30, 36, 56, 255), (205, 34, 44, 255), (150, 20, 30, 255), (0, 150, 72, 255)
    skin = (160, 112, 90, 255)
    hip = [x - bend * 0.2 * m, 0]
    legs = []
    for ph in (phi, phi + math.pi):
        a = walk * math.radians(26) * math.sin(ph) + bend * math.radians(75)
        flex = walk * math.radians(55) * max(0, math.cos(ph)) + bend * math.radians(120)
        legs.append((a, flex))
    # solve hip height so the lowest foot touches the ground
    def ankles(hy):
        out = []
        for a, flex in legs:
            kx, ky = hip[0] + L1 * math.sin(a), hy + L1 * math.cos(a)
            ax, ay = kx + L2 * math.sin(a - flex), ky + L2 * math.cos(a - flex)
            out.append(((kx, ky), (ax, ay)))
        return out
    a0 = ankles(0)
    hip[1] = GROUND - 0.07 * m - max(p[1][1] for p in a0)
    lg = ankles(hip[1])

    def limb(p0, p1, w, col):
        d.line([P(*p0), P(*p1)], fill=col, width=int(w * S))
        for p in (p0, p1):
            q = P(*p)
            d.ellipse((q[0] - w * S / 2, q[1] - w * S / 2, q[0] + w * S / 2, q[1] + w * S / 2), fill=col)

    lean = math.radians(6 + 60 * bend + 8 * nod) + walk * math.radians(2.5) * math.sin(2 * phi - 0.6)
    tl = 0.55 * m
    sh = (hip[0] + tl * math.sin(lean), hip[1] - tl * math.cos(lean))
    head = (sh[0] + 0.2 * m * math.sin(lean) + 8, sh[1] - 0.2 * m * math.cos(lean))
    # far leg (darker) then near leg drawn after torso
    for i, ((k, a), shade) in enumerate(zip(lg, (0.7, 1.0))):
        if i == 1:
            continue
        col = tuple(int(c * shade) for c in pants[:3]) + (255,)
        limb(hip, k, 44, col)
        limb(k, a, 40, col)
        d.rounded_rectangle((*P(a[0] - 18, a[1] - 14), *P(a[0] + 52, a[1] + 24)), 10 * S, fill=(20, 20, 26, 255))
    # parcel target
    if carry == "carry":
        tgt = (sh[0] + 0.36 * m, sh[1] + 0.42 * m + walk * 7 * math.sin(2 * phi - 1.2))
    elif carry == "place":
        tgt = (PKG_POS[0] - 20, PKG_POS[1] - 60)
    else:
        tgt = None
    # far arm
    far_t = tgt if tgt else (sh[0] + 0.12 * m, sh[1] + 0.55 * m)
    if hands:
        far_t = hands[1]
    e, h = ik(sh[0] - 6, sh[1] + 6, far_t[0] - 10, far_t[1], 0.3 * m, 0.3 * m, bend=1)
    limb((sh[0] - 6, sh[1] + 6), e, 34, (26, 36, 66, 255))
    limb(e, h, 30, (26, 36, 66, 255))
    # torso as rotated rounded poly
    def rot(px, py, ang, cx, cy):
        c, s_ = math.cos(ang), math.sin(ang)
        return (cx + (px - cx) * c - (py - cy) * s_, cy + (px - cx) * s_ + (py - cy) * c)
    tor = [(hip[0] - 0.14 * m, hip[1] + 0.08 * m), (hip[0] + 0.14 * m, hip[1] + 0.08 * m),
           (hip[0] + 0.15 * m, hip[1] - tl), (hip[0] - 0.15 * m, hip[1] - tl)]
    tor = [rot(px, py, lean, hip[0], hip[1]) for px, py in tor]
    d.polygon([P(px + 5, py - 4) for px, py in tor], fill=rimc)
    d.polygon([P(*p) for p in tor], fill=navy)
    hem = [rot(px, py, lean, hip[0], hip[1]) for px, py in [(hip[0] - 0.14 * m, hip[1] + 0.02 * m), (hip[0] + 0.14 * m, hip[1] + 0.02 * m),
                                                              (hip[0] + 0.14 * m, hip[1] + 0.08 * m), (hip[0] - 0.14 * m, hip[1] + 0.08 * m)]]
    d.polygon([P(*p) for p in hem], fill=red)
    # bag on back
    bag = [(hip[0] - 0.14 * m, hip[1] - 0.12 * m), (hip[0] - 0.14 * m, hip[1] - tl - 0.05 * m),
           (hip[0] - 0.55 * m, hip[1] - tl - 0.05 * m), (hip[0] - 0.55 * m, hip[1] - 0.12 * m)]
    # the bag lags the torso: extra swing a few frames behind the step
    bag_ang = lean + walk * math.radians(4) * math.sin(2 * phi - 1.1) - math.radians(3) * nod
    bag = [rot(px, py, bag_ang, hip[0], hip[1]) for px, py in bag]
    d.polygon([P(px + 4, py - 5) for px, py in bag], fill=(236, 120, 130, 255))
    d.polygon([P(*p) for p in bag], fill=red)
    band = [(hip[0] - 0.14 * m, hip[1] - 0.3 * m), (hip[0] - 0.14 * m, hip[1] - 0.38 * m),
            (hip[0] - 0.55 * m, hip[1] - 0.38 * m), (hip[0] - 0.55 * m, hip[1] - 0.3 * m)]
    d.polygon([P(*rot(px, py, bag_ang, hip[0], hip[1])) for px, py in band], fill=green)
    bl = rot(hip[0] - 0.345 * m, hip[1] - 0.46 * m, bag_ang, hip[0], hip[1])
    d.text(P(*bl), "H8KI", font=font("xb", 64), fill=(255, 255, 255, 255), anchor="mm")
    # near leg
    k, a = lg[1]
    limb(hip, k, 46, pants)
    limb(k, a, 42, pants)
    d.rounded_rectangle((*P(a[0] - 18, a[1] - 16), *P(a[0] + 56, a[1] + 24)), 10 * S, fill=(24, 24, 30, 255))
    d.rectangle((*P(a[0] - 18, a[1] + 14), *P(a[0] + 56, a[1] + 24)), fill=(120, 124, 140, 255))
    # head + cap
    hx, hy = head
    hy += walk * 6 * math.sin(2 * phi - 1.3)            # head settles a beat late
    brim = walk * 5 * math.sin(2 * phi - 1.8) + 4 * nod
    d.ellipse((*P(hx - 42 + 4, hy - 44 - 3), *P(hx + 42 + 4, hy + 44 - 3)), fill=rimc)
    d.ellipse((*P(hx - 42, hy - 44), *P(hx + 42, hy + 44)), fill=skin)
    d.pieslice((*P(hx - 44, hy - 46), *P(hx + 40, hy + 44)), 110, 260, fill=(24, 20, 22, 255))
    d.ellipse((*P(hx - 8, hy - 6), *P(hx + 10, hy + 14)), fill=(140, 96, 78, 255))
    d.ellipse((*P(hx + 22, hy - 12), *P(hx + 30, hy - 4)), fill=(20, 20, 20, 255))
    d.chord((*P(hx - 46, hy - 60), *P(hx + 44, hy + 16)), 180, 360, fill=red)
    d.polygon([P(hx + 30, hy - 24), P(hx + 78, hy - 16 + brim), P(hx + 72, hy - 8 + brim), P(hx + 30, hy - 12)], fill=redd)
    d.rectangle((*P(hx - 46, hy - 26), *P(hx + 38, hy - 18)), fill=green)
    d.text(P(hx - 2, hy - 38), "H8KI", font=font("xb", 22), fill=(255, 255, 255, 255), anchor="mm")
    # parcel
    pc = None
    if tgt:
        pw, ph_ = 0.3 * m, 0.24 * m
        cx, cy = tgt[0] + 20, tgt[1] + (0 if carry == "carry" else 60 - ph_ / 2)
        if carry == "place":
            cy = PKG_POS[1] - ph_ / 2
        d.rounded_rectangle((*P(cx - pw / 2, cy - ph_ / 2), *P(cx + pw / 2, cy + ph_ / 2)), 8 * S, fill=(255, 70, 58, 255))
        d.rectangle((*P(cx - pw / 2, cy + ph_ * 0.22), *P(cx + pw / 2, cy + ph_ * 0.32)), fill=(0, 150, 72, 255))
        d.text(P(cx, cy - ph_ * 0.08), "H8KI", font=font("xb", 50), fill=(255, 255, 255, 255), anchor="mm")
        pc = (cx, cy)
    if pbox is not None:
        pc = draw_parcel(d, P, pbox, m)
    # near arm
    if hands and reach <= 0:
        rt = hands[0]
    elif reach > 0:
        rt = (sh[0] + (BELL[0] - sh[0]) * reach, sh[1] + 0.5 * m * (1 - reach) + (BELL[1] - sh[1]) * reach)
    else:
        rt = ((pc[0] - 0.12 * m, pc[1] + 0.1 * m) if pc else (tgt[0] + 14, tgt[1])) if tgt else (sh[0] + 0.1 * m, sh[1] + 0.56 * m)
    e, h = ik(sh[0], sh[1] + 6, rt[0], rt[1], 0.3 * m, 0.3 * m, bend=1)
    limb((sh[0], sh[1] + 6), e, 38, navy)
    limb(e, h, 34, navy)
    # H8KI sleeve patch on the uniform
    pt = P(sh[0] + (e[0] - sh[0]) * 0.38, sh[1] + 6 + (e[1] - sh[1] - 6) * 0.38)
    d.rounded_rectangle((pt[0] - 34, pt[1] - 20, pt[0] + 34, pt[1] + 20), 8, fill=red, outline=(255, 255, 255, 255), width=3)
    d.text(pt, "H8KI", font=font("xb", 24), fill=(255, 255, 255, 255), anchor="mm")
    q = P(*h)
    d.ellipse((q[0] - 17 * S, q[1] - 17 * S, q[0] + 17 * S, q[1] + 17 * S), fill=skin)
    out = im.resize((900, 800), Image.LANCZOS)
    return out, (ox, oy), pc


def open_door(img, t):
    """Double door swings open; the recipient stands backlit in the doorway."""
    o = ease_io(lin(t, DOOR_OPEN_T, DOOR_OPEN_T + 0.55))
    x0, y0, x1, y1 = DOOR
    mid = (x0 + x1) / 2
    gap = (x1 - x0) * 0.86 * o
    if gap < 2:
        return img
    k = 2
    ww, hh = int((x1 - x0) * k), int((y1 - y0) * k)
    lay = Image.new("RGBA", (ww, hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    # warm interior with a soft vertical falloff
    for yy in range(0, hh, 4):
        f = yy / hh
        c = (int(255 - 20 * f), int(214 - 50 * f), int(150 - 70 * f), 255)
        d.rectangle((0, yy, ww, yy + 4), fill=c)
    # recipient silhouette (hijab, long dress), rim-lit
    cx = ww / 2 + 6 * k
    base = hh
    fig = (58, 34, 30, 255)
    rim = (255, 196, 120, 255)
    wave = max(0.0, lin(t, DOOR_OPEN_T + 0.7, DOOR_OPEN_T + 1.0))
    wv = math.sin((t - DOOR_OPEN_T) * 9) * 0.35 * wave
    kf = k * 0.88
    def figure(dx, col):
        d.polygon([(cx - 88 * kf + dx, base), (cx + 88 * kf + dx, base), (cx + 62 * kf + dx, base - 330 * kf),
                   (cx + 70 * kf + dx, base - 420 * kf), (cx - 70 * kf + dx, base - 420 * kf), (cx - 62 * kf + dx, base - 330 * kf)], fill=col)
        d.ellipse((cx - 64 * kf + dx, base - 540 * kf, cx + 64 * kf + dx, base - 400 * kf), fill=col)   # hijab
        d.ellipse((cx - 44 * kf + dx, base - 520 * kf, cx + 44 * kf + dx, base - 426 * kf), fill=col)
        if wave > 0:
            sx, sy = cx + 52 * kf + dx, base - 405 * kf
            ex, ey = sx + 42 * kf, sy - 75 * kf
            hx, hy = ex + math.sin(wv) * 40 * kf, ey - math.cos(wv) * 80 * kf
            d.line([(sx, sy), (ex, ey), (hx, hy)], fill=col, width=int(30 * kf), joint="curve")
            d.ellipse((hx - 20 * kf, hy - 20 * kf, hx + 20 * kf, hy + 20 * kf), fill=col)
    lay = lay.resize(((x1 - x0), (y1 - y0)), Image.LANCZOS)
    # clip to the opening, then draw the door leaves swung inward at the edges
    mask = Image.new("L", lay.size, 0)
    ImageDraw.Draw(mask).rectangle((mid - gap / 2 - x0, 0, mid + gap / 2 - x0, lay.height), fill=255)
    img = img.copy()
    img.paste(lay.convert("RGB"), (x0, y0), mask)
    d = ImageDraw.Draw(img)
    leaf = (x1 - x0) / 2 - gap / 2
    for side in (-1, 1):
        edge = mid + side * gap / 2
        d.rectangle((min(edge, edge + side * leaf), y0, max(edge, edge + side * leaf), y1), fill=(52, 120, 84))
        d.line([(edge, y0), (edge, y1)], fill=(30, 70, 50), width=3)
    arr = to_arr(img)
    glow_add(arr, mid, y1 - 280, 260, (255, 170, 90), 0.35 * o)
    return to_img(arr)


def light_level(t):
    """Porch bulb: a stutter, then it warms up and the glow grows and spills."""
    if t < LIGHT_T:
        return 0.0
    dt = t - LIGHT_T
    if dt < 0.06:
        return 0.3
    if dt < 0.12:
        return 0.06
    return ease_out((dt - 0.12) / 0.9) * (1 + 0.025 * math.sin(t * 29) + 0.015 * math.sin(t * 53))


def scene4(t, raw=False):
    L = light_level(t)
    arr = HOUSE_DARK * (1 - L) + HOUSE_LIT * L
    img = to_img(arr)
    if t >= DOOR_OPEN_T:
        img = open_door(img, t)
    # courier choreography: walk in, ring (parcel in hand), hand it over, nod
    m = PPM
    walk_end_x = 300
    M = (452, 1188)                                # hand-over point, chest height
    carry_c = lambda cx: (cx + 172, 1259)
    nod = 0.0

    def x_walk(tt):
        p = lin(tt, S4_START, WALKIN_END)
        return -160 + (walk_end_x + 160) * (1 - (1 - p) ** 1.6)

    def rx_of(tt):
        return 585 - 37 * ease_io(lin(tt, *REC_OUT)) + 26 * ease_io(lin(tt, GIVE_T, GIVE_T + 0.5))

    def box_at(tt, x_):
        off_ = back_in_out(lin(tt, *OFFER), 0.9)            # tiny pull-back, reach, overshoot, settle
        pull_ = ease_io(lin(tt, GIVE_T, GIVE_T + 0.4))
        cc = carry_c(x_)
        b = (cc[0] + (M[0] - cc[0]) * off_, cc[1] + (M[1] - cc[1]) * off_)
        ch_ = (rx_of(tt) - 0.14 * m, 1222)
        return (b[0] + (ch_[0] - b[0]) * pull_, b[1] + (ch_[1] - b[1]) * pull_)

    if t < WALKIN_END:
        x = x_walk(t)
        phi = math.pi * (t - S4_START - 0.12) / S4_STEP
        pose = dict(walk=1.0 - 0.6 * lin(t, WALKIN_END - 0.35, WALKIN_END), bend=0, reach=0, carry="carry")
    else:
        sf = ease_io(lin(t, *STEP_FWD))
        back = ease_io(lin(t, GIVE_T + 0.05, NOD[0] + 0.2))
        x = walk_end_x + 45 * sf - 34 * back
        phi = math.pi * 0.5 * sf
        r = back_in_out(lin(t, BELL_REACH, BELL_T), 0.8) * (1 - ease_io(lin(t, BELL_T + 0.2, BELL_T + 0.5)))
        pull = ease_io(lin(t, GIVE_T, GIVE_T + 0.4))
        nod = math.sin(math.pi * lin(t, *NOD)) if NOD[0] < t < NOD[1] else 0.0
        pose = dict(walk=0.4 * math.sin(math.pi * sf), bend=0, reach=r, carry="none")
    rx = rx_of(t)
    rec_on = t >= DOOR_OPEN_T + 0.2
    if t >= WALKIN_END:
        box = box_at(t, x)
        box_late = box_at(t - 0.08, x)                       # far hand trails by ~2-3 frames
        left = [(box[0] - 0.13 * m, box[1] + 0.05 * m), (box_late[0] - 0.12 * m, box_late[1] - 0.06 * m)]
        rest = [(x + 0.1 * m, 1320), (x + 0.04 * m, 1320)]
        wd0 = ease_io(lin(t, GIVE_T + 0.05, GIVE_T + 0.45))
        wd1 = ease_io(lin(t, GIVE_T + 0.13, GIVE_T + 0.53))
        hands = [(a[0] + (b[0] - a[0]) * w_, a[1] + (b[1] - a[1]) * w_) for a, b, w_ in zip(left, rest, (wd0, wd1))]
        pose.update(pbox=None if pull > 0 else box, hands=hands, nod=nod)
    arr = to_arr(img)
    glow_add(arr, x + 10, GROUND + 6, 110, (-50, -50, -40), 1.0, squash=0.18)
    img = to_img(arr)
    rhands = None
    if t >= WALKIN_END:
        hold = [(box[0] - 0.08 * m, box[1] + 0.11 * m), (box[0] + 0.1 * m, box[1] + 0.1 * m)]
        rhands = []
        for i_, lagt in enumerate((0.0, 0.08)):
            tk = ease_io(lin(t - lagt, *TAKE))
            b_ = box_at(t - lagt, x)
            rest_ = (rx - 0.08 * m + 0.06 * m * i_, 1300)
            on_ = (b_[0] + 0.13 * m - 0.01 * m * i_, b_[1] - 0.05 * m + 0.11 * m * i_)
            h_ = (rest_[0] + (on_[0] - rest_[0]) * tk, rest_[1] + (on_[1] - rest_[1]) * tk)
            h_ = (h_[0] + (hold[i_][0] - h_[0]) * pull, h_[1] + (hold[i_][1] - h_[1]) * pull)
            rhands.append(h_)
    if rec_on:
        rbob = 8 * abs(math.sin(math.pi * 2 * lin(t, *REC_OUT))) if REC_OUT[0] < t < REC_OUT[1] else 0
        vel = (rx_of(t - 0.1) - rx_of(t - 0.2)) * 10         # hijab trails her movement
        rnod = math.sin(math.pi * lin(t, GIVE_T + 0.25, GIVE_T + 0.85)) if GIVE_T + 0.25 < t < GIVE_T + 0.85 else 0
        recipient(img, rx, TERRACE, rhands, L, ease_io(lin(t, DOOR_OPEN_T + 0.2, DOOR_OPEN_T + 0.5)), rbob,
                  sway=-vel * 0.35 + 3 * math.sin(t * 1.7), breath=2.5 * math.sin(t * 2.4), nod=rnod)
    # courier with motion blur while walking (3 sub-frames)
    if t < WALKIN_END + 0.05:
        subs = []
        for dt_ in (-1 / 120, 0.0, 1 / 120):
            tt = min(t + dt_, WALKIN_END)
            ph_ = math.pi * (tt - S4_START - 0.12) / S4_STEP
            sp_, (ox, oy), pc = courier_side(x_walk(tt), ph_, warm=L, **pose)
            subs.append(np.asarray(sp_, np.float32))
        st = np.stack(subs)
        al = st[..., 3:4] / 255.0
        rgb = (st[..., :3] * al).sum(0) / np.maximum(al.sum(0), 1e-4)
        spr = Image.fromarray(np.dstack([rgb, al.mean(0)[..., 0] * 255]).clip(0, 255).astype(np.uint8), "RGBA")
        ox, oy = x - 450, 900
    else:
        spr, (ox, oy), pc = courier_side(x, phi, warm=L, **pose)
    img.paste(spr, (int(ox), int(oy)), spr)
    if t >= WALKIN_END and pose.get("pbox") is None:
        # after the hand-over the recipient holds the parcel at her chest
        d = ImageDraw.Draw(img)
        draw_parcel(d, lambda px, py: (px, py), box, m, k=1)
        pc = box
    if rec_on and rhands and t >= TAKE[0]:
        d = ImageDraw.Draw(img)
        for h in rhands[:1]:
            d.ellipse((h[0] - 15, h[1] - 15, h[0] + 15, h[1] + 15), fill=(182, 124, 96))
    arr = to_arr(img)
    if pc:
        glow_add(arr, pc[0], pc[1], 110, (255, 60, 40), 0.45 * (1 - 0.4 * L))
    # living light: the glow grows and spills out rather than switching on
    if L > 0:
        grow = 0.5 + 0.5 * L
        glow_add(arr, LAMP[0], LAMP[1], 70 * grow, (255, 230, 170), 1.3 * L)
        glow_add(arr, LAMP[0], LAMP[1] + 200, 520 * grow, (255, 160, 80), 0.22 * L)
        glow_add(arr, 200, 1090, 240 * grow, (255, 170, 90), 0.18 * L)
        o_ = ease_io(lin(t, DOOR_OPEN_T, DOOR_OPEN_T + 0.9))
        glow_add(arr, 585, 1560, 420 * (0.4 + 0.6 * o_), (255, 175, 95), 0.22 * o_, squash=0.35)
        if L > 0.4:  # moths around the porch bulb
            for k_ in range(6):
                a1 = t * (2.3 + 0.41 * k_) + k_ * 1.9
                rr = 38 + 22 * math.sin(t * 1.4 + k_ * 2.3)
                glow_add(arr, LAMP[0] + rr * math.cos(a1) + 5 * math.sin(t * 19 + k_),
                         LAMP[1] + 0.6 * rr * math.sin(a1 * 1.3) + 5 * math.cos(t * 15 + k_), 2.2, (255, 240, 210), 0.9 * L)
        # dust drifting through the doorway light
        o_ = ease_io(lin(t, DOOR_OPEN_T, DOOR_OPEN_T + 0.6))
        for (mx_, my_, sp_, ph_) in DUST:
            yy = 880 + ((my_ - t * sp_) % 720)
            xx = mx_ + 14 * math.sin(t * 0.8 + ph_)
            glow_add(arr, xx, yy, 2.0, (255, 225, 170), 0.45 * o_ * L)
    # bell press flash
    if BELL_T <= t < BELL_T + 0.3:
        glow_add(arr, BELL[0], BELL[1], 30, (255, 80, 80), 1.2 * (1 - lin(t, BELL_T, BELL_T + 0.3)))
    img = to_img(arr)
    # foreground branch, defocused, with parallax against the camera drift
    drift = 16 * math.sin(0.55 * (t - S4_START))
    img.paste(BRANCH, (int(-12 - 1.8 * drift), int(-8 - 0.6 * drift)), BRANCH)
    arr = to_arr(img)
    # camera: slow push-in + lateral drift (never static)
    z = 1 + 0.05 * ease_io(lin(t, S4_START, S4_END + 0.4))
    arr = arr * (VIG * (1 - 0.5 * L) + VIG_SOFT * 0.5 * L)
    grain(arr, 3.5, int(t * FPS) + 999)
    # lift the whole stage 200px so nothing sits in the Reels caption zone (y > 1500)
    arr = np.concatenate([arr[LIFT:], np.repeat(arr[-1:], LIFT, 0)], 0)
    img = to_img(arr)
    cw, ch = W / z, H / z
    x0 = (W - cw) / 2 + drift * 0.8
    y0 = (H - ch) * 0.62
    x0 = min(max(0, x0), W - cw)
    img = img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BICUBIC)
    # blurred foreground plants in the bottom corners, moving faster than the stage
    if FG_L is not None:
        img.paste(FG_L, (int(-230 - 2.6 * drift), 1480), FG_L)
        img.paste(FG_R, (int(W - 330 - 2.6 * drift), 1510), FG_R)
    if raw:
        return img
    draw_chip(img, "Rumah cat hijau", 330, 560, t, 21.75, 1.5)
    draw_chip(img, "Warung Bu Ani", 1050, 880, t, 22.15, 1.5, anchor="r")
    draw_chip(img, "Pagar hitam", 180, 1220, t, 22.55, 1.5)
    if t >= BADGE_T:
        p = t - BADGE_T
        a_, s_, dy_ = pop(t, BADGE_T, 0.5, rise=30)
        paste_layer(img, badge(), 540, 250 + dy_, a_, 0.6 + 0.4 * s_ if s_ < 1 else s_)
    a1 = ease_out(lin(t, LINE1_T, LINE1_T + 0.4))
    if a1 > 0:  # soft scrim so the lines read over the lit wall
        sa = to_arr(img)
        glow_add(sa, 540, 485, 600, (-190, -185, -170), 0.9 * a1, squash=0.24)
        img = to_img(sa)
    pa, ps, pd = pop(t, LINE1_T, 0.5)
    draw_text(img, "Alamatnya ketemu.", font("xb", 70), 540, 440 + pd, (255, 255, 255), pa, ps, blur=16)
    pa, ps, pd = pop(t, LINE2_T, 0.5)
    draw_text(img, "Sejauh apa pun alamatnya.", font("xb", 52), 540, 522 + pd, (255, 56, 64), pa, ps, blur=16)
    return img


_badge = None


def badge():
    global _badge
    if _badge is None:
        w, h = 720, 170
        k = 2
        im = Image.new("RGBA", ((w + 80) * k, (h + 80) * k), (0, 0, 0, 0))
        sh = Image.new("L", im.size, 0)
        ImageDraw.Draw(sh).rounded_rectangle((40 * k, 52 * k, (40 + w) * k, (52 + h) * k), 40 * k, fill=170)
        im.putalpha(sh.filter(ImageFilter.GaussianBlur(18 * k)))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((40 * k, 40 * k, (40 + w) * k, (40 + h) * k), 40 * k, fill=(255, 255, 255))
        im = im.resize((w + 80, h + 80), Image.LANCZOS)
        im.alpha_composite(check_icon(104, (0, 160, 72)), (40 + 30, 40 + 33))
        d = ImageDraw.Draw(im)
        d.text((40 + 158, 40 + 70), "PAKET DITERIMA", font=font("xb", 56), fill=(0, 140, 64), anchor="lm")
        d.text((40 + 160, 40 + 128), "Diterima  ·  23:48  ·  H8KI Logistik Lionindo", font=font("m", 26), fill=(90, 100, 110), anchor="lm")
        _badge = im
    return _badge


# ------------------------------------------------------------------ Scene 5
def make_logo():
    im = Image.open("logo.jpg").convert("RGB")
    a = np.asarray(im, np.float32)
    bg = 247.0
    dist = np.max(np.abs(a - bg), axis=2)
    alpha = np.clip((dist - 6) / 40, 0, 1)
    col = (a - bg * (1 - alpha[..., None])) / np.maximum(alpha[..., None], 1e-3)
    col = np.clip(col, 0, 255)
    rgba = np.dstack([col, alpha * 255]).astype(np.uint8)
    lg = Image.fromarray(rgba, "RGBA")
    lg = lg.crop(lg.getbbox())
    w = 860
    return lg.resize((w, int(lg.height * w / lg.width)), Image.LANCZOS)


LOGO = make_logo()
yy, xx = np.mgrid[0:H, 0:W]
WHITE_BG = (255 - 12 * np.clip(np.sqrt(((xx - 540) / 900.0) ** 2 + ((yy - 900) / 1300.0) ** 2), 0, 1) ** 2)[..., None].repeat(3, 2).astype(np.float32)
WHITE_BG[..., 2] += 2


def x_badge(size):
    k = 4
    im = Image.new("RGBA", (size * k, size * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    S_ = size * k
    d.ellipse((0, 0, S_ - 1, S_ - 1), fill=(228, 28, 44))
    w = int(S_ * 0.11)
    d.line([(S_ * .32, S_ * .32), (S_ * .68, S_ * .68)], fill=(255, 255, 255), width=w)
    d.line([(S_ * .68, S_ * .32), (S_ * .32, S_ * .68)], fill=(255, 255, 255), width=w)
    return im.resize((size, size), Image.LANCZOS)


ICON_X = x_badge(64)
ICON_OK = check_icon(64, (0, 160, 72))


def recap_bg():
    """Night delivery scene, darkened (no blur) as the recap backdrop."""
    global _rbg
    if _rbg is None:
        a = np.asarray(scene4(S4_END - 0.001, raw=True), np.float32)
        g = a.mean(axis=2, keepdims=True)
        a = (a * 0.5 + g * 0.5) * 0.28 + np.array([4, 6, 16], np.float32)
        _rbg = a
    return _rbg


_rbg = None


def recap_frame(t):
    """A-style recap: search-history panel, red X flip to green check, then big 'KETEMU.'"""
    bg = to_img(recap_bg())
    zz = 1 + 0.045 * ease_io(lin(t, RECAP_T, LOGO_T))           # slow push-in, never static
    cw, ch = W / zz, H / zz
    img = bg.crop((int((W - cw) / 2), int((H - ch) * 0.45), int((W + cw) / 2), int((H - ch) * 0.45 + ch))).resize((W, H), Image.BICUBIC)
    out = ease_in(lin(t, LOGO_T - 0.12, LOGO_T))
    enter = back_in_out(lin(t, RECAP_T, RECAP_T + 0.5), 1.1)
    dy = 70 * (1 - enter) - 40 * out
    alpha = clamp(enter) * (1 - out)
    # panel
    px0, py0, px1, py1 = 80, 470 + dy, 1000, 1020 + dy
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(panel)
    d.rounded_rectangle((px0, py0, px1, py1), 28, fill=(14, 20, 36, int(235 * alpha)),
                        outline=(52, 70, 110, int(255 * alpha)), width=3)
    d.text((px0 + 44, py0 + 58), "RIWAYAT PENCARIAN", font=font("mono", 28), fill=(110, 140, 200, int(255 * alpha)), anchor="lm")
    img.paste(panel, (0, 0), panel)
    d = ImageDraw.Draw(img, "RGBA")
    for k, q in enumerate(QUERIES):
        y = py0 + 150 + k * 82
        fk = FLIP_TS[k]
        flipped = t >= fk + 0.07
        p = lin(t, fk, fk + 0.14)
        sx = abs(math.cos(math.pi * p)) if 0 < p < 1 else 1.0
        icon = ICON_OK if flipped else ICON_X
        if sx > 0.04:
            ic = icon.resize((max(1, int(54 * sx)), 54), Image.LANCZOS)
            paste_layer(img, ic, px0 + 72, y, alpha)
        f = font("sb", 36 if len(q) < 32 else 33)
        col = (238, 242, 250) if flipped else (150, 90, 100)
        d.text((px0 + 118, y), q, font=f, fill=col + (int(255 * alpha),), anchor="lm")
        if not flipped:  # struck through while still 'not found'
            tw = d.textlength(q, font=f)
            d.line([(px0 + 118, y + 2), (px0 + 118 + tw, y + 2)], fill=(228, 60, 72, int(230 * alpha)), width=4)
    # verdict
    draw_text(img, "5 dari 5 alamat", font("b", 64), 540, 1120 + dy, (240, 244, 250), alpha, blur=14)
    if t >= RECAP_OK:
        q = t - RECAP_OK
        pop = 0.7 + 0.3 * back_in_out(q / 0.45, 1.3)
        a2 = lin(q, 0, 0.08) * (1 - out)
        glow = Image.new("RGBA", (1, 1))
        draw_text(img, "KETEMU.", font("xb", 200), 540, 1300 + dy, (70, 220, 120), a2, pop, blur=24, glow=(0, 170, 80))
    return img


def scene5(t):
    if t < LOGO_T:
        rec = recap_frame(t)
        p = ease_io(lin(t, RECAP_T, RECAP_T + 0.18))
        if p >= 1:
            return rec
        # quick dip: the night scene dims into the recap (no blur)
        under = np.asarray(scene4(t), np.float32)
        return to_img(under * (1 - p) + np.asarray(rec, np.float32) * p)
    img = to_img(WHITE_BG)
    p = lin(t, LOGO_T, LOGO_T + 0.45)
    lg = LOGO
    sp = lin(t, LOGO_T + 0.7, LOGO_T + 1.4)
    if 0 < sp < 1:  # light sweep across the logo
        lg = LOGO.copy()
        gx = np.arange(lg.width)[None, :] + np.arange(lg.height)[:, None] * 0.4
        c = -200 + sp * (lg.width + 400)
        band = np.exp(-((gx - c) / 60) ** 2) * 0.55
        arr = np.asarray(lg, np.float32).copy()
        arr[..., :3] = arr[..., :3] + (255 - arr[..., :3]) * band[..., None]
        lg = Image.fromarray(arr.astype(np.uint8), "RGBA")
    drift = 1 + 0.03 * ease_io(lin(t, LOGO_T + 0.4, DUR))
    paste_layer(img, lg, 540, 800, ease_out(p), (0.9 + 0.1 * back_in_out(p, 1.2)) * drift)
    q = lin(t, TAG_T, TAG_T + 0.4)
    ta, ts_, tdy = pop(t, TAG_T, 0.5)
    tb, tbs, tbdy = pop(t, TAG_T + 0.2, 0.5)
    if q > 0:
        draw_text(img, "Kurir yang", font("xb", 92), 540, 1180 + tdy, (30, 36, 48), ta, ts_, shadow=0.12, blur=12)
    q2 = lin(t, TAG_T + 0.2, TAG_T + 0.6)
    if q2 > 0:
        draw_text(img, "nggak nyerah.", font("xb", 104), 540, 1295 + tbdy, (228, 20, 30), tb,
                  tbs, shadow=0.15, blur=12)
        u = ease_out(lin(t, TAG_T + 0.6, TAG_T + 1.0))
        if u > 0:
            half = 330 * u
            ImageDraw.Draw(img).rounded_rectangle((540 - half, 1378, 540 + half, 1390), 6, fill=(0, 150, 70))
    return img
