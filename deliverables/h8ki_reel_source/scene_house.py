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
PPM = 365          # px per metre (1x)
PKG_POS = (560, TERRACE)   # where the parcel is set down (bottom centre)
BELL = (392, 1318)
DOOR = (430, 870, 740, TERRACE)
LAMP = (585, 800)


def night(c, k=1.0):
    return tuple(int(v) for v in SN.night_col(c, k))


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
    # mango branch framing top-left
    r = np.random.default_rng(9)
    d.line(s(-40, 250, 260, 330), fill=(28, 22, 22), width=22 * S)
    d.line(s(120, 290, 330, 470), fill=(28, 22, 22), width=12 * S)
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


def courier_side(x, phi, walk, bend, reach, carry, warm):
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

    lean = math.radians(6 + 60 * bend)
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
        tgt = (sh[0] + 0.36 * m, sh[1] + 0.42 * m)
    elif carry == "place":
        tgt = (PKG_POS[0] - 20, PKG_POS[1] - 60)
    else:
        tgt = None
    # far arm
    far_t = tgt if tgt else (sh[0] + 0.12 * m, sh[1] + 0.55 * m)
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
    bag = [rot(px, py, lean, hip[0], hip[1]) for px, py in bag]
    d.polygon([P(px + 4, py - 5) for px, py in bag], fill=(236, 120, 130, 255))
    d.polygon([P(*p) for p in bag], fill=red)
    band = [(hip[0] - 0.14 * m, hip[1] - 0.3 * m), (hip[0] - 0.14 * m, hip[1] - 0.38 * m),
            (hip[0] - 0.55 * m, hip[1] - 0.38 * m), (hip[0] - 0.55 * m, hip[1] - 0.3 * m)]
    d.polygon([P(*rot(px, py, lean, hip[0], hip[1])) for px, py in band], fill=green)
    bl = rot(hip[0] - 0.345 * m, hip[1] - 0.46 * m, lean, hip[0], hip[1])
    d.text(P(*bl), "H8KI", font=font("xb", 64), fill=(255, 255, 255, 255), anchor="mm")
    # near leg
    k, a = lg[1]
    limb(hip, k, 46, pants)
    limb(k, a, 42, pants)
    d.rounded_rectangle((*P(a[0] - 18, a[1] - 16), *P(a[0] + 56, a[1] + 24)), 10 * S, fill=(24, 24, 30, 255))
    d.rectangle((*P(a[0] - 18, a[1] + 14), *P(a[0] + 56, a[1] + 24)), fill=(120, 124, 140, 255))
    # head + cap
    hx, hy = head
    d.ellipse((*P(hx - 42 + 4, hy - 44 - 3), *P(hx + 42 + 4, hy + 44 - 3)), fill=rimc)
    d.ellipse((*P(hx - 42, hy - 44), *P(hx + 42, hy + 44)), fill=skin)
    d.pieslice((*P(hx - 44, hy - 46), *P(hx + 40, hy + 44)), 110, 260, fill=(24, 20, 22, 255))
    d.ellipse((*P(hx - 8, hy - 6), *P(hx + 10, hy + 14)), fill=(140, 96, 78, 255))
    d.ellipse((*P(hx + 22, hy - 12), *P(hx + 30, hy - 4)), fill=(20, 20, 20, 255))
    d.chord((*P(hx - 46, hy - 60), *P(hx + 44, hy + 16)), 180, 360, fill=red)
    d.polygon([P(hx + 30, hy - 24), P(hx + 78, hy - 16), P(hx + 72, hy - 8), P(hx + 30, hy - 12)], fill=redd)
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
    # near arm
    if reach > 0:
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


def light_level(t):
    if t < LIGHT_T:
        return 0.0
    dt = t - LIGHT_T
    if dt < 0.05:
        return 0.8
    if dt < 0.11:
        return 0.2
    return min(1.0, 0.85 + dt * 0.6)


def scene4(t, raw=False):
    L = light_level(t)
    arr = HOUSE_DARK * (1 - L) + HOUSE_LIT * L
    img = to_img(arr)
    # courier choreography
    walk_end_x = 300
    if t < WALKIN_END:
        p = lin(t, S4_START, WALKIN_END)
        x = -160 + (walk_end_x + 160) * (1 - (1 - p) ** 1.6)
        phi = math.pi * (t - S4_START - 0.12) / S4_STEP
        pose = dict(walk=1.0 - 0.6 * lin(t, WALKIN_END - 0.35, WALKIN_END), bend=0, reach=0, carry="carry")
    elif t < PLACE_END:
        p = lin(t, PLACE_START, PLACE_END)
        b = math.sin(math.pi * p)
        x, phi = walk_end_x, 0
        pose = dict(walk=0, bend=0.85 * b, reach=0, carry="place" if p > 0.2 and p < 0.62 else ("carry" if p <= 0.2 else "none"))
    else:
        x, phi = walk_end_x, 0
        r = ease_io(lin(t, BELL_REACH, BELL_T)) * (1 - ease_io(lin(t, BELL_T + 0.25, BELL_T + 0.6)))
        step_back = ease_io(lin(t, LIGHT_T + 0.3, LIGHT_T + 0.8))
        x -= 40 * step_back
        phi = math.pi * 0.5 * step_back
        pose = dict(walk=0.4 * math.sin(math.pi * step_back), bend=0, reach=r, carry="none")
    placed = t >= PLACE_START + 0.62 * (PLACE_END - PLACE_START)
    arr = to_arr(img)
    glow_add(arr, x + 10, GROUND + 6, 110, (-50, -50, -40), 1.0, squash=0.18)
    if placed:
        img = to_img(arr)
        d = ImageDraw.Draw(img)
        pw, ph = 0.3 * PPM, 0.24 * PPM
        cx = PKG_POS[0]
        d.rounded_rectangle((cx - pw / 2, PKG_POS[1] - ph, cx + pw / 2, PKG_POS[1]), 5, fill=(240, 62, 52))
        d.rectangle((cx - pw / 2, PKG_POS[1] - ph * 0.28, cx + pw / 2, PKG_POS[1] - ph * 0.18), fill=(0, 150, 72))
        d.text((cx, PKG_POS[1] - ph * 0.58), "H8KI", font=font("xb", 26), fill=(255, 255, 255), anchor="mm")
        arr = to_arr(img)
    img = to_img(arr)
    spr, (ox, oy), pc = courier_side(x, phi, warm=L, **pose)
    img.paste(spr, (int(ox), int(oy)), spr)
    arr = to_arr(img)
    # parcel glow follows it
    g = (PKG_POS[0], PKG_POS[1] - 45) if placed else pc
    if g:
        glow_add(arr, g[0], g[1], 110, (255, 60, 40), 0.45 * (1 - 0.5 * L))
    # warm bloom when the light comes on
    if L > 0:
        glow_add(arr, LAMP[0], LAMP[1], 70, (255, 230, 170), 1.3 * L)
        glow_add(arr, LAMP[0], LAMP[1] + 200, 520, (255, 160, 80), 0.22 * L)
        glow_add(arr, 200, 1090, 240, (255, 170, 90), 0.18 * L)
    # bell press flash
    if BELL_T <= t < BELL_T + 0.3:
        glow_add(arr, BELL[0], BELL[1], 30, (255, 80, 80), 1.2 * (1 - lin(t, BELL_T, BELL_T + 0.3)))
    # gentle push-in
    z = 1 + 0.06 * ease_io(lin(t, S4_START, S4_END))
    arr = arr * (VIG * (1 - 0.5 * L) + VIG_SOFT * 0.5 * L + (1 - VIG) * 0 )
    grain(arr, 3.5, int(t * FPS) + 999)
    img = to_img(arr)
    if z > 1.001:
        cw, ch = W / z, H / z
        x0, y0 = (W - cw) / 2, (H - ch) * 0.62
        img = img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BICUBIC)
    if raw:
        return img
    draw_chip(img, "Rumah cat hijau", 330, 760, t, 21.75, 1.5)
    draw_chip(img, "Warung Bu Ani", 1050, 1080, t, 22.15, 1.5, anchor="r")
    draw_chip(img, "Pagar hitam", 180, 1420, t, 22.55, 1.5)
    if t >= BADGE_T:
        p = t - BADGE_T
        paste_layer(img, badge(), 540, 250, lin(p, 0, 0.1), 0.55 + 0.45 * back_out(p / 0.3))
    a1 = ease_out(lin(t, LINE1_T, LINE1_T + 0.4))
    draw_text(img, "Alamatnya ketemu.", font("xb", 70), 540, 440 - 14 * (1 - a1), (255, 255, 255), a1, blur=16)
    a2 = ease_out(lin(t, LINE2_T, LINE2_T + 0.45))
    draw_text(img, "Sejauh apa pun alamatnya.", font("sb", 50), 540, 520 - 14 * (1 - a2), (255, 214, 150), a2, blur=14)
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
        d.text((40 + 160, 40 + 128), "5 dari 5 alamat ditemukan", font=font("m", 28), fill=(90, 100, 110), anchor="lm")
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


def scene5(t):
    if t < WHITE_T:
        p = ease_io(lin(t, S4_END, WHITE_T))
        img = scene4(min(t, S4_END - 0.001) if t < S4_END else t)
        img = img.filter(ImageFilter.GaussianBlur(2 + 40 * p))
        arr = to_arr(img)
        arr = arr * (1 - p) + WHITE_BG * p
        img = to_img(arr)
    else:
        img = to_img(WHITE_BG)
    p = lin(t, LOGO_T, LOGO_T + 0.7)
    if p > 0:
        lg = LOGO
        # light sweep across the logo
        sp = lin(t, 29.4, 30.3)
        if 0 < sp < 1:
            lg = LOGO.copy()
            band = np.zeros((lg.height, lg.width), np.float32)
            gx = np.arange(lg.width)[None, :] + np.arange(lg.height)[:, None] * 0.4
            c = -200 + sp * (lg.width + 400)
            band = np.exp(-((gx - c) / 60) ** 2) * 0.55
            arr = np.asarray(lg, np.float32)
            arr[..., :3] = arr[..., :3] + (255 - arr[..., :3]) * band[..., None]
            lg = Image.fromarray(arr.astype(np.uint8), "RGBA")
        paste_layer(img, lg, 540, 800, ease_out(p), 0.9 + 0.1 * back_out(p, 1.4))
    q = lin(t, TAG_T, TAG_T + 0.5)
    if q > 0:
        draw_text(img, "Kurir yang", font("xb", 92), 540, 1180 + 20 * (1 - ease_out(q)), (30, 36, 48), ease_out(q), shadow=0.12, blur=12)
    q2 = lin(t, TAG_T + 0.3, TAG_T + 0.8)
    if q2 > 0:
        draw_text(img, "nggak nyerah.", font("xb", 104), 540, 1295 + 20 * (1 - ease_out(q2)), (228, 20, 30), ease_out(q2),
                  0.94 + 0.06 * back_out(q2), shadow=0.15, blur=12)
        u = ease_out(lin(t, TAG_T + 0.8, TAG_T + 1.3))
        d = ImageDraw.Draw(img)
        if u > 0:
            half = 330 * u
            d.rounded_rectangle((540 - half, 1378, 540 + half, 1390), 6, fill=(0, 150, 70))
    return img
