"""Scene 3: the courier walks the gang at night (3D-projected alley)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *
from gfx import *

S = 2                      # supersample for geometry
W2, H2 = W * S, H * S
F2 = 1000.0 * S            # focal length (px at 2x)
HORIZON = 1000             # 1x screen y of horizon when fully tilted
TILT_PX = 1750             # how far the world sits below frame at the start
CAM_X, CAM_Y = 0.35, 1.55
WALK_SPEED = 1.35          # m/s
CAM_Z0 = -1.5
MOON = (270, 1960)         # sky coords (1x)
SKY_H = H + TILT_PX
FOG = np.array([38, 44, 86], np.float32)
NIGHT = np.array([0.34, 0.40, 0.62], np.float32)
AMB = np.array([10, 12, 26], np.float32)


def cam_z(t):
    return CAM_Z0 + WALK_SPEED * max(0.0, t - WALK_START)


def tilt(t):
    return ease_io(lin(t, TILT_START, TILT_END))


# ------------------------------------------------------------------ sky
def make_sky():
    r = np.random.default_rng(11)
    ys = np.arange(SKY_H)[:, None]
    p = ys / SKY_H
    top = np.array([4, 6, 18], np.float32)
    mid = np.array([14, 18, 48], np.float32)
    low = np.array([52, 44, 96], np.float32)
    col = np.where(p < 0.6, top + (mid - top) * (p / 0.6), mid + (low - mid) * ((p - 0.6) / 0.4))
    arr = np.repeat(col[:, None, :], W, 1).reshape(SKY_H, W, 3).astype(np.float32)
    # milky haze band
    hz = Image.new("L", (W, SKY_H), 0)
    d = ImageDraw.Draw(hz)
    for _ in range(90):
        x, y = r.uniform(-200, W + 200), r.uniform(0, SKY_H * 0.7)
        rr = r.uniform(80, 260)
        d.ellipse((x - rr, y - rr * 0.5, x + rr, y + rr * 0.5), fill=int(r.uniform(4, 12)))
    hz = np.asarray(hz.filter(ImageFilter.GaussianBlur(80)), np.float32)
    arr += hz[..., None] * np.array([0.9, 0.9, 1.4], np.float32)
    # stars
    for _ in range(900):
        x, y = r.uniform(0, W), r.uniform(0, SKY_H - 500)
        b = r.uniform(0.25, 1) ** 2
        sz = r.choice([0.8, 1.2, 1.8, 2.6], p=[0.55, 0.28, 0.13, 0.04])
        glow_add(arr, x, y, sz, (255, 245, 230) if r.random() < 0.7 else (200, 220, 255), 200 * b)
    # moon: soft glow + crescent
    mx, my = MOON
    glow_add(arr, mx, my, 520, (60, 70, 120), 0.9)
    glow_add(arr, mx, my, 180, (150, 150, 180), 0.55)
    moon = Image.new("L", (400, 400), 0)
    dm = ImageDraw.Draw(moon)
    dm.ellipse((80, 80, 320, 320), fill=255)
    dm.ellipse((142, 50, 372, 290), fill=0)
    moon = moon.resize((200, 200), Image.LANCZOS)
    m = np.asarray(moon, np.float32)[..., None] / 255
    y0, x0 = int(my - 100), int(mx - 100)
    arr[y0:y0 + 200, x0:x0 + 200] = arr[y0:y0 + 200, x0:x0 + 200] * (1 - m) + m * np.array([255, 244, 214])
    return np.clip(arr, 0, 255)


SKY = make_sky()


# ------------------------------------------------------------------ sprites
def make_tree():
    """Mango tree, 5m x 5.5m at 300px/m. Anchor: trunk base at (x=2.2m, bottom)."""
    ppm = 300
    Wt, Ht = int(5.5 * ppm), int(5.8 * ppm)
    im = Image.new("RGBA", (Wt, Ht), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = np.random.default_rng(5)
    bx = 2.2 * ppm
    trunk = (58, 40, 38, 255)
    d.polygon([(bx - 45, Ht), (bx + 45, Ht), (bx + 70, Ht - 2.2 * ppm), (bx + 20, Ht - 2.3 * ppm)], fill=trunk)
    for (ex, ey, w) in [(3.8, 3.9, 34), (1.1, 3.8, 30), (2.9, 4.8, 26), (4.6, 3.2, 22)]:
        d.line([(bx + 45, Ht - 2.2 * ppm), (ex * ppm, Ht - ey * ppm)], fill=trunk, width=w)
    # canopy clusters, back to front, cool moon rim from upper-left
    blobs = []
    for _ in range(170):
        ang = r.uniform(0, 2 * math.pi)
        rad = r.uniform(0, 1) ** 0.6
        cx = 2.9 * ppm + math.cos(ang) * rad * 2.2 * ppm
        cy = Ht - 4.0 * ppm + math.sin(ang) * rad * 1.35 * ppm
        blobs.append((cy, cx, r.uniform(0.28, 0.55) * ppm))
    blobs.sort()
    for cy, cx, rr in blobs:
        shade = r.uniform(0.8, 1.15)
        d.ellipse((cx - rr - 10, cy - rr - 12, cx + rr - 10, cy + rr - 12),
                  fill=(int(70 * shade), int(120 * shade), int(128 * shade), 255))
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=(int(22 * shade), int(52 * shade), int(52 * shade), 255))
    # leaf texture
    for _ in range(1600):
        ang = r.uniform(0, 2 * math.pi)
        rad = r.uniform(0, 1) ** 0.5
        cx = 2.9 * ppm + math.cos(ang) * rad * 2.4 * ppm
        cy = Ht - 4.0 * ppm + math.sin(ang) * rad * 1.5 * ppm
        a = r.uniform(0, math.pi)
        L = r.uniform(20, 42)
        c = int(r.uniform(28, 70))
        d.line([(cx, cy), (cx + L * math.cos(a), cy + L * math.sin(a))], fill=(c // 2, c, c + 6, 255), width=9)
    # mangoes
    for _ in range(14):
        cx = 2.9 * ppm + r.uniform(-1.8, 1.8) * ppm
        cy = Ht - 3.2 * ppm + r.uniform(-0.3, 0.5) * ppm
        d.line([(cx, cy - 40), (cx, cy - 14)], fill=(40, 50, 40, 255), width=4)
        d.ellipse((cx - 17, cy - 14, cx + 17, cy + 30), fill=(120, 150, 70, 255))
        d.ellipse((cx - 11, cy - 10, cx + 3, cy + 6), fill=(175, 190, 110, 255))
    return im, ppm, 2.2


TREE, TREE_PPM, TREE_AX = make_tree()


def make_cat(curl=0):
    ppm = 300
    im = Image.new("RGBA", (220, 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    body = (46, 50, 72, 255) if curl == 0 else (120, 96, 80, 255)
    rim = (120, 132, 175, 255) if curl == 0 else (190, 170, 150, 255)
    d.ellipse((24, 46, 176, 134), fill=rim)
    d.ellipse((30, 52, 180, 138), fill=body)
    d.ellipse((130, 40, 205, 110), fill=rim)
    d.ellipse((134, 44, 208, 114), fill=body)
    d.polygon([(140, 58), (150, 20), (166, 50)], fill=body)
    d.polygon([(176, 50), (196, 22), (204, 60)], fill=body)
    d.line([(158, 82), (170, 86)], fill=(20, 20, 30, 255), width=3)
    d.line([(182, 84), (194, 82)], fill=(20, 20, 30, 255), width=3)
    d.arc((10, 60, 110, 150), 150, 330, fill=body, width=16)
    if curl:
        for k in range(3):
            d.arc((50 + k * 30, 70, 90 + k * 30, 120), 200, 300, fill=(90, 70, 58, 255), width=6)
    return im, ppm


CATS = [make_cat(0), make_cat(1)]


def make_mosque():
    ppm = 14  # far away; drawn big then scaled
    Wm, Hm = 900, 700
    im = Image.new("RGBA", (Wm, Hm), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    body = (24, 34, 62, 255)
    d.rectangle((180, 420, 720, 700), fill=body)
    d.ellipse((300, 200, 600, 500), fill=(30, 70, 76, 255))
    d.ellipse((316, 212, 590, 490), fill=(26, 58, 66, 255))
    d.rectangle((300, 350, 600, 460), fill=body)
    d.line([(450, 200), (450, 130)], fill=(200, 190, 130, 255), width=8)
    d.ellipse((430, 92, 470, 132), fill=(220, 205, 140, 255))
    d.ellipse((440, 90, 480, 128), fill=(0, 0, 0, 0))
    for mx in (110, 790):
        d.rectangle((mx - 26, 160, mx + 26, 700), fill=body)
        d.polygon([(mx - 34, 170), (mx + 34, 170), (mx, 60)], fill=(30, 70, 76, 255))
        d.rectangle((mx - 38, 300, mx + 38, 318), fill=(40, 52, 88, 255))
        d.rectangle((mx - 8, 220, mx + 8, 260), fill=(255, 210, 120, 255))
    for k in range(5):
        x = 240 + k * 100
        d.rounded_rectangle((x, 520, x + 40, 600), 20, fill=(255, 205, 120, 255))
    return im, 900 / 60.0  # sprite spans 60 m wide


MOSQUE, MOSQUE_PPM = make_mosque()


def make_skyline():
    r = np.random.default_rng(21)
    im = Image.new("RGBA", (3000, 400), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 0
    while x < 3000:
        w = r.uniform(80, 220)
        h = r.uniform(80, 220)
        c = (26, 30, 60, 255)
        d.polygon([(x, 400), (x, 400 - h), (x + w / 2, 400 - h - r.uniform(20, 60)), (x + w, 400 - h), (x + w, 400)],
                  fill=c)
        if r.random() < 0.35:
            d.rectangle((x + w * 0.3, 400 - h * 0.6, x + w * 0.3 + 14, 400 - h * 0.6 + 18), fill=(230, 180, 110, 255))
        x += w
    for _ in range(9):  # coconut palms
        px = r.uniform(0, 3000)
        d.line([(px, 400), (px + 20, 90)], fill=(22, 26, 52, 255), width=12)
        for a in range(8):
            ang = a / 8 * 2 * math.pi
            d.line([(px + 20, 90), (px + 20 + 110 * math.cos(ang), 90 + 50 * math.sin(ang) + 30)],
                   fill=(22, 26, 52, 255), width=14)
    return im, 3000 / 120.0   # 120 m wide


SKYLINE, SKYLINE_PPM = make_skyline()

# ------------------------------------------------------------------ world
HALF = 1.5


def night_col(c, k=1.0):
    return np.array(c, np.float32) * NIGHT * k + AMB


def fog_col(c, dz):
    f = 1 - math.exp(-max(dz, 0) / 26.0)
    v = c * (1 - f) + FOG * f
    return tuple(int(min(255, max(0, x))) for x in v)


LEFT = [(-5, 2, 3.1, (225, 170, 140), "house"), (2, 6.5, 2.8, (150, 215, 190), "house"),
        (6.5, 10, 3.3, (235, 220, 150), "house"), (10, 15, 3.0, (185, 160, 215), "house"),
        (15, 20.5, 1.5, (200, 200, 195), "low"), (20.5, 26, 3.2, (150, 185, 225), "house"),
        (26, 31, 2.9, (235, 160, 140), "house"), (31, 37, 3.1, (235, 225, 195), "house")]
RIGHT = [(-5, 3, 3.0, (170, 215, 160), "house"), (3, 7, 3.4, (235, 225, 190), "house"),
         (7, 12, 1.25, (160, 175, 200), "low"), (12, 17, 2.9, (235, 175, 190), "house"),
         (17, 23, 3.3, (130, 200, 195), "house"), (23, 29, 3.0, (235, 215, 130), "house"),
         (29, 40, 3.2, (235, 185, 150), "house")]
END_Z = 40.0
LAMPS = [(-1.42, 2.6, 5.0), (1.42, 2.6, 13.0), (-1.42, 2.7, 22.5), (1.42, 2.6, 31.0), (-0.6, 2.4, END_Z - 0.05)]
LIT_WINDOWS = {("L", 2), ("R", 3), ("L", 5), ("R", 5)}


def seg_details(side, idx, z0, z1, kind):
    """Doors/windows for a facade: list of (zc, width, y0, y1, type)."""
    if kind != "house":
        return []
    L = z1 - z0
    r = np.random.default_rng(idx * 7 + (0 if side == "L" else 100))
    dz = z0 + L * r.uniform(0.25, 0.4)
    out = [(dz, 0.9, 0.0, 2.05, "door")]
    wz = z0 + L * r.uniform(0.62, 0.78)
    out.append((wz, 1.1, 0.95, 2.0, "win_lit" if (side, idx) in LIT_WINDOWS else "win"))
    return out


class Painter:
    def __init__(self, d, cz, yoff):
        self.d, self.cz = d, cz
        self.sx0 = W2 / 2
        self.sy0 = (HORIZON + yoff) * S

    def P(self, x, y, z):
        dz = z - self.cz
        return (self.sx0 + F2 * (x - CAM_X) / dz, self.sy0 - F2 * (y - CAM_Y) / dz)

    def clip(self, pts, zn=0.3):
        zmin = self.cz + zn
        out = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            ain, bin_ = a[2] >= zmin, b[2] >= zmin
            if ain:
                out.append(a)
            if ain != bin_:
                t = (zmin - a[2]) / (b[2] - a[2])
                out.append(tuple(a[k] + t * (b[k] - a[k]) for k in range(3)))
        return out

    def quad(self, pts, col):
        pts = self.clip(pts)
        if len(pts) < 3:
            return
        self.d.polygon([self.P(*p) for p in pts], fill=col)

    def scale(self, z):
        return F2 / (z - self.cz)


def draw_facade(pn, side, idx, seg, cz):
    z0, z1, h, base, kind = seg
    if z1 <= cz + 0.3 or z0 > cz + 70:
        return
    sgn = -1 if side == "L" else 1
    x = sgn * HALF
    k = 0.78 if side == "L" else 1.0
    mid = max(z0, cz + 0.5) * 0.5 + z1 * 0.5 - cz
    base_c = night_col(base, k)
    # set-back house behind a low wall
    if kind == "low":
        xb = sgn * 4.2
        pn.quad([(xb, 0, z0), (xb, 3.0, z0), (xb, 3.0, z1), (xb, 0, z1)], fog_col(night_col((200, 190, 175), 0.7), mid + 3))
        pn.quad([(xb, 2.9, z0), (xb, 3.1, z0), (xb, 3.1, z1), (xb, 2.9, z1)], fog_col(night_col((90, 60, 50), 0.8), mid + 3))
    # near end face (visible where this segment is taller than the one in front)
    pn.quad([(x, 0, z0), (x, h, z0), (x + sgn * 3, h, z0), (x + sgn * 3, 0, z0)], fog_col(base_c * 0.72, mid))
    # facade + plinth
    pn.quad([(x, 0, z0), (x, h, z0), (x, h, z1), (x, 0, z1)], fog_col(base_c, mid))
    pn.quad([(x, 0, z0), (x, 0.45, z0), (x, 0.45, z1), (x, 0, z1)], fog_col(base_c * 0.62, mid))
    if kind == "low":
        pn.quad([(x, h, z0), (x + sgn * 0.25, h, z0), (x + sgn * 0.25, h, z1), (x, h, z1)], fog_col(base_c * 1.15, mid))
    for (zc, wd, y0, y1, typ) in seg_details(side, idx, z0, z1, kind):
        a, b = zc - wd / 2, zc + wd / 2
        xi = x - sgn * 0.01
        if typ == "door":
            pn.quad([(xi, y0, a - 0.08), (xi, y1 + 0.08, a - 0.08), (xi, y1 + 0.08, b + 0.08), (xi, y0, b + 0.08)],
                    fog_col(base_c * 0.55, zc - cz))
            pn.quad([(xi, y0, a), (xi, y1, a), (xi, y1, b), (xi, y0, b)], fog_col(night_col((120, 80, 55)), zc - cz))
        else:
            lit = typ == "win_lit"
            pn.quad([(xi, y0 - 0.06, a - 0.06), (xi, y1 + 0.06, a - 0.06), (xi, y1 + 0.06, b + 0.06), (xi, y0 - 0.06, b + 0.06)],
                    fog_col(base_c * 1.25, zc - cz))
            gc = (255, 196, 112) if lit else tuple(night_col((70, 90, 130)))
            pn.quad([(xi, y0, a), (xi, y1, a), (xi, y1, b), (xi, y0, b)], fog_col(np.array(gc, np.float32), (zc - cz) * (0.3 if lit else 1)))
            if lit:  # curtain
                pn.quad([(xi, y0, a), (xi, y1, a), (xi, y1, a + wd * 0.3), (xi, y0, a + wd * 0.22)],
                        fog_col(np.array([200, 110, 70], np.float32), (zc - cz) * 0.3))
            for kk in range(1, 5):   # teralis bars
                zz = a + wd * kk / 5
                pn.quad([(xi, y0, zz - 0.012), (xi, y1, zz - 0.012), (xi, y1, zz + 0.012), (xi, y0, zz + 0.012)],
                        fog_col(np.array([20, 22, 30], np.float32), zc - cz))
    if kind == "house":
        # eave underside + fascia
        pn.quad([(x, h, z0), (x - sgn * 0.4, h, z0), (x - sgn * 0.4, h, z1), (x, h, z1)], fog_col(base_c * 0.45, mid))
        pn.quad([(x - sgn * 0.4, h, z0), (x - sgn * 0.4, h + 0.18, z0), (x - sgn * 0.4, h + 0.18, z1), (x - sgn * 0.4, h, z1)],
                fog_col(night_col((150, 80, 60)), mid))


def sprite(img, spr, ppm, x, y, z, ax, cz, pn, ay=1.0, extra=None):
    dz = z - cz
    if dz < 0.6:
        return None
    sc = pn.scale(z) / ppm
    w, h = int(spr.width * sc), int(spr.height * sc)
    if w < 2 or h < 2 or w > 6000:
        return None
    sx, sy = pn.P(x, y, z)
    sp = spr.resize((w, h), Image.BILINEAR)
    if extra is not None:
        sp = extra(sp, dz)
    img.paste(sp, (int(sx - ax * w), int(sy - ay * h)), sp)
    return sx, sy, sc


def fog_sprite(spr, dz, strength=1.0):
    f = (1 - math.exp(-dz / 26.0)) * strength
    if f < 0.02:
        return spr
    a = spr.getchannel("A")
    col = Image.new("RGB", spr.size, tuple(int(v) for v in FOG))
    out = Image.blend(spr.convert("RGB"), col, f)
    out.putalpha(a)
    return out


def render_world(t):
    """Returns (rgb float array 1x, screen info) for the alley at time t."""
    cz = cam_z(t)
    yoff = TILT_PX * (1 - tilt(t))
    sky_y0 = int(TILT_PX * (1 - tilt(t)))
    sky = SKY[SKY_H - H - sky_y0: SKY_H - sky_y0] if sky_y0 > 0 else SKY[SKY_H - H:]
    img = Image.fromarray(sky.astype(np.uint8)).resize((W2, H2), Image.BILINEAR)
    d = ImageDraw.Draw(img)
    pn = Painter(d, cz, yoff)
    info = {"cz": cz, "yoff": yoff}
    # skyline + mosque (far)
    sprite(img, SKYLINE, SKYLINE_PPM, 0, 0, 95, 0.5, cz, pn, extra=lambda s, dz: fog_sprite(s, dz, 0.35))
    ms = sprite(img, MOSQUE, MOSQUE_PPM, 6, 0, 85, 0.5, cz, pn, extra=lambda s, dz: fog_sprite(s, dz, 0.25))
    info["mosque"] = pn.P(6, 22, 85)
    # floor: concrete strips with seams + gutters
    zs = np.arange(math.floor(cz) + 1, END_Z + 8, 1.0)[::-1]
    for z in zs:
        za, zb = max(z, cz + 0.3), z + 1.0
        if zb <= cz + 0.3:
            continue
        dz = (za + zb) / 2 - cz
        c = night_col((150, 150, 160), 0.95 if int(z) % 2 else 1.0)
        pn.quad([(-HALF, 0, za), (HALF, 0, za), (HALF, 0, zb), (-HALF, 0, zb)], fog_col(c, dz))
        for gx in (-HALF, HALF - 0.22):
            pn.quad([(gx, 0, za), (gx + 0.22, 0, za), (gx + 0.22, 0, zb), (gx, 0, zb)], fog_col(c * 0.55, dz))
        pn.quad([(-HALF, 0, za), (HALF, 0, za), (HALF, 0, za + 0.04), (-HALF, 0, za + 0.04)], fog_col(c * 0.7, dz))
    # left-turn passage floor + end wall (mentok)
    pn.quad([(-6, 0, 37), (-HALF, 0, 37), (-HALF, 0, END_Z), (-6, 0, END_Z)], fog_col(night_col((120, 120, 135)), END_Z - cz))
    pn.quad([(-6, 0, END_Z), (-6, 3.0, END_Z), (HALF, 3.0, END_Z), (HALF, 0, END_Z)], fog_col(night_col((230, 225, 215)), END_Z - cz))
    pn.quad([(-6, 3.0, END_Z), (-6, 3.2, END_Z), (HALF, 3.2, END_Z), (HALF, 3.0, END_Z)], fog_col(night_col((150, 80, 60)), END_Z - cz))
    pn.quad([(-0.2, 0, END_Z - 0.01), (-0.2, 2.0, END_Z - 0.01), (0.7, 2.0, END_Z - 0.01), (0.7, 0, END_Z - 0.01)],
            fog_col(night_col((90, 110, 90)), END_Z - cz))
    info["end"] = pn.P(-1.0, 1.8, END_Z) if END_Z - cz > 1 else None
    # tree (behind left low wall)
    tr = sprite(img, TREE, TREE_PPM, -3.0, 0, 18.3, TREE_AX / 5.5, cz, pn, extra=lambda s, dz: fog_sprite(s, dz))
    info["tree"] = pn.P(-1.2, 2.6, 18.3) if 18.3 - cz > 0.8 else None
    # facades far -> near, both sides
    items = [("L", i, s) for i, s in enumerate(LEFT)] + [("R", i, s) for i, s in enumerate(RIGHT)]
    items.sort(key=lambda it: -it[2][1])
    for side, i, seg in items:
        draw_facade(pn, side, i, seg, cz)
        if side == "R" and seg[4] == "low":
            for k, (cat, ppm) in enumerate(CATS):
                cz_ = [8.4, 9.8][k]
                sprite(img, cat, ppm, 1.62, 1.25, cz_, 0.5, cz, pn, ay=0.93, extra=lambda s, dz: fog_sprite(s, dz))
    # potted plants
    for (px, pz) in [(-1.3, 3.4), (1.3, 14.2), (-1.3, 24.0), (1.3, 26.5)]:
        if pz - cz > 0.8:
            sx, sy = pn.P(px, 0, pz)
            sc = pn.scale(pz)
            c = fog_col(night_col((60, 120, 80)), pz - cz)
            for (ox, oy, rr) in [(-0.12, 0.35, 0.2), (0.1, 0.42, 0.22), (0, 0.6, 0.2)]:
                cx, cy = sx + ox * sc, sy - oy * sc
                d.ellipse((cx - rr * sc, cy - rr * sc, cx + rr * sc, cy + rr * sc), fill=c)
            d.rectangle((sx - 0.15 * sc, sy - 0.3 * sc, sx + 0.15 * sc, sy), fill=fog_col(night_col((170, 90, 60)), pz - cz))
    # lamp brackets
    lamp_scr = []
    for (lx, ly, lz) in LAMPS:
        if lz - cz < 0.5:
            continue
        sx, sy = pn.P(lx, ly, lz)
        sc = pn.scale(lz)
        wall = pn.P(math.copysign(HALF, lx) if abs(lx) > 1 else lx, ly + 0.25, lz)
        d.line([wall, (sx, sy - 0.1 * sc)], fill=(30, 30, 40), width=max(2, int(0.05 * sc)))
        d.ellipse((sx - 0.07 * sc, sy - 0.07 * sc, sx + 0.07 * sc, sy + 0.07 * sc), fill=(255, 236, 190))
        gx, gy = pn.P(lx * 0.4, 0, lz)
        lamp_scr.append((sx / S, sy / S, sc / S, gx / S, gy / S, lz - cz))
    small = img.resize((W, H), Image.LANCZOS)
    arr = to_arr(small)
    # lamp glows + light pools on the floor
    for (sx, sy, sc, gx, gy, dz) in lamp_scr:
        fade = math.exp(-dz / 40)
        glow_add(arr, sx, sy, 0.22 * sc, (255, 220, 160), 1.2 * fade)
        glow_add(arr, sx, sy, 1.4 * sc, (255, 170, 90), 0.35 * fade)
        glow_add(arr, gx, gy, 1.5 * sc, (255, 170, 100), 0.30 * fade, squash=0.28)
    # lit window spill
    return arr, info


# ------------------------------------------------------------------ courier (from behind, 3/4)
def courier_back(phi, t):
    Wc, Hc = 940, 1440
    fx, fy = 400, 1400
    im = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rl = max(0.0, math.sin(phi))      # right foot swinging
    ll = max(0.0, -math.sin(phi))
    bob = abs(math.sin(phi)) * 22
    sway = -8 * math.cos(phi)
    oy = fy - bob
    ox = fx + sway
    RIM = (118, 146, 205, 255)
    pants = (30, 36, 56, 255)
    navy = (36, 50, 92, 255)
    red = (205, 34, 44, 255)
    redd = (150, 20, 30, 255)
    green = (0, 150, 72, 255)
    skin = (160, 112, 90, 255)

    def rim_poly(pts, col, off=(-7, -3)):
        d.polygon([(x + off[0], y + off[1]) for x, y in pts], fill=RIM)
        d.polygon(pts, fill=col)

    # legs
    for side, lift in ((-1, ll), (1, rl)):
        lx = ox + side * 64
        foot_y = fy - lift * 70
        hip_y = oy - 640
        w = 112 - lift * 12
        rim_poly([(lx - w / 2, hip_y), (lx + w / 2, hip_y), (lx + w / 2 - 6, foot_y - 70), (lx - w / 2 + 6, foot_y - 70)], pants)
        # shoe (heel up shows the sole)
        d.rounded_rectangle((lx - 66, foot_y - 92, lx + 66, foot_y - 12), 30, fill=(24, 24, 30, 255))
        if lift > 0.15:
            d.rounded_rectangle((lx - 60, foot_y - 40, lx + 60, foot_y - 10), 14, fill=(130, 136, 152, 255))
        else:
            d.rectangle((lx - 64, foot_y - 26, lx + 64, foot_y - 12), fill=(110, 116, 130, 255))
    # package in right hand (partly behind the bag)
    px0, py0 = ox + 240, oy - 910
    d.rounded_rectangle((px0, py0, px0 + 200, py0 + 170), 14, fill=(255, 70, 58, 255))
    d.polygon([(px0 + 200, py0 + 6), (px0 + 232, py0 - 16), (px0 + 232, py0 + 150), (px0 + 200, py0 + 170)], fill=(200, 40, 40, 255))
    d.polygon([(px0 + 10, py0), (px0 + 200, py0), (px0 + 232, py0 - 16), (px0 + 42, py0 - 16)], fill=(255, 120, 100, 255))
    # branded parcel: H8KI mark on the visible face
    d.rectangle((px0 + 60, py0 + 112, px0 + 200, py0 + 128), fill=(0, 150, 72, 255))
    d.text((px0 + 128, py0 + 70), "H8KI", font=font("xb", 50), fill=(255, 255, 255, 255), anchor="mm")
    # jacket
    rim_poly([(ox - 175, oy - 600), (ox + 175, oy - 600), (ox + 200, oy - 1110), (ox - 200, oy - 1110)], navy)
    d.rectangle((ox - 175, oy - 640, ox + 175, oy - 600), fill=red)
    d.rectangle((ox - 175, oy - 656, ox + 175, oy - 644), fill=green)
    # arms
    swing = 14 * math.sin(phi)
    rim_poly([(ox - 205, oy - 1100), (ox - 150, oy - 1100), (ox - 170 + swing, oy - 720), (ox - 230 + swing, oy - 720)], navy)
    d.rectangle((ox - 232 + swing, oy - 740, ox - 168 + swing, oy - 722), fill=green)
    d.ellipse((ox - 236 + swing, oy - 730, ox - 170 + swing, oy - 668), fill=skin)
    rim_poly([(ox + 150, oy - 1100), (ox + 205, oy - 1100), (ox + 250, oy - 820), (ox + 195, oy - 800)], navy)
    # neck + head
    d.rectangle((ox - 42, oy - 1190, ox + 50, oy - 1110), fill=(130, 90, 74, 255))
    hx, hy = ox + 6, oy - 1262
    d.ellipse((hx - 106, hy - 104, hx + 102, hy + 104), fill=RIM)
    d.ellipse((hx - 100, hy - 100, hx + 104, hy + 106), fill=(24, 20, 22, 255))
    d.pieslice((hx + 20, hy - 60, hx + 110, hy + 100), -70, 80, fill=skin)          # cheek sliver
    d.ellipse((hx + 84, hy - 18, hx + 122, hy + 42), fill=skin)                      # ear
    # cap
    d.chord((hx - 108, hy - 124, hx + 110, hy + 60), 180, 360, fill=red)
    d.rectangle((hx - 108, hy - 34, hx + 110, hy - 14), fill=green)
    d.polygon([(hx + 96, hy - 30), (hx + 150, hy - 18), (hx + 104, hy - 12)], fill=redd)
    d.ellipse((hx - 12, hy - 128, hx + 12, hy - 106), fill=green)
    d.text((hx, hy - 70), "H8KI", font=font("xb", 46), fill=(255, 255, 255, 255), anchor="mm")
    # big delivery bag (the weight of responsibility)
    bx0, by0, bx1, by1 = ox - 225, oy - 1190, ox + 240, oy - 690
    d.polygon([(bx1, by0 + 10), (bx1 + 46, by0 - 20), (bx1 + 46, by1 - 36), (bx1, by1)], fill=redd)
    d.polygon([(bx0 + 20, by0), (bx1 - 10, by0), (bx1 + 40, by0 - 26), (bx0 + 70, by0 - 26)], fill=(225, 60, 64, 255))
    d.rounded_rectangle((bx0 - 7, by0 - 3, bx1 - 7, by1 - 3), 30, fill=(236, 120, 130, 255))
    d.rounded_rectangle((bx0, by0, bx1, by1), 30, fill=red)
    d.rectangle((bx0, by0 + 290, bx1, by0 + 360), fill=green)
    d.text(((bx0 + bx1) / 2, by0 + 160), "H8KI", font=font("xb", 150), fill=(255, 255, 255, 255), anchor="mm")
    d.text(((bx0 + bx1) / 2, by0 + 326), "LOGISTIK LIONINDO", font=font("b", 34), fill=(255, 255, 255, 255), anchor="mm")
    d.line([(bx0 + 30, by0 + 30), (bx1 - 30, by0 + 30)], fill=redd, width=6)
    # straps
    for sx in (ox - 150, ox + 150):
        d.rounded_rectangle((sx - 22, oy - 1200, sx + 22, oy - 1150), 10, fill=(20, 22, 30, 255))
    # right hand gripping the parcel
    d.ellipse((px0 + 170, py0 + 110, px0 + 234, py0 + 170), fill=skin)
    out = im.resize((Wc // 2, Hc // 2), Image.LANCZOS)
    return out, (fx // 2, fy // 2), ((px0 + 120) / 2, (py0 + 85) / 2)


# ------------------------------------------------------------------ fog overlay
def make_mist():
    r = np.random.default_rng(2)
    n = r.random((60, 34)).astype(np.float32)
    im = Image.fromarray((n * 255).astype(np.uint8)).resize((W * 2, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(30))
    a = np.asarray(im, np.float32) / 255
    ys = np.arange(H)[:, None] / H
    band = np.exp(-((ys - 0.52) / 0.18) ** 2)
    return a * band


MIST = make_mist()


def scene3(t):
    arr, info = render_world(t)
    yoff = info["yoff"]
    # mist drifting across the alley
    off = int((t * 40) % W)
    m = MIST[:, off:off + W][..., None]
    arr = arr + m * np.array([70, 76, 120], np.float32) * 0.5
    # depth of field: soften background before the hero
    img = to_img(arr).filter(ImageFilter.GaussianBlur(1.3))
    # courier
    phi = math.pi * (t - WALK_START - 0.25) / STEP
    spr, (ax, ay), pk = courier_back(phi, t)
    k = 1.28
    spr = spr.resize((int(spr.width * k), int(spr.height * k)), Image.LANCZOS)
    ax, ay, pk = ax * k, ay * k, (pk[0] * k, pk[1] * k)
    cx, feet = 420, 1850 + yoff
    # soft contact shadow
    arr = to_arr(img)
    glow_add(arr, cx + 10, feet - 8, 190, (-60, -60, -50), 1.0, squash=0.16)
    img = to_img(arr)
    img.paste(spr, (int(cx - ax), int(feet - ay)), spr)
    arr = to_arr(img)
    # the package is the heart of the mission: warm red glow
    pgx, pgy = cx - ax + pk[0], feet - ay + pk[1]
    beat = 0.85 + 0.15 * math.sin(t * 5)
    glow_add(arr, pgx, pgy, 120, (255, 60, 40), 0.55 * beat)
    glow_add(arr, pgx, pgy, 320, (255, 90, 60), 0.18 * beat)
    # grade + vignette
    arr = arr * VIG
    grain(arr, 4.0, int(t * FPS))
    img = to_img(arr)
    # landmark payoffs (what GPS couldn't find, the courier does)
    if info.get("mosque"):
        mx, my = info["mosque"]
        draw_chip(img, "Dekat masjid", mx / S, my / S - 40, t, 13.9, 1.7)
    if info.get("tree"):
        tx, ty = info["tree"]
        draw_chip(img, "Depan pohon mangga", max(220, tx / S), ty / S + 40, t, 16.4, 1.7)
    if info.get("end"):
        ex, ey = info["end"]
        draw_chip(img, "Masuk gang, mentok, belok kiri", 540, ey / S - 20, t, 19.6, 1.8)
    # story text
    a1 = ease_io(lin(t, T1[0], T1[0] + 0.6)) * (1 - lin(t, T1[1] - 0.4, T1[1]))
    draw_text(img, "Kurir kami tidak.", font("xb", 88), 540, 420, (255, 255, 255), a1,
              0.96 + 0.04 * ease_out(lin(t, T1[0], T1[0] + 1.2)), blur=16)
    a2 = ease_io(lin(t, T2[0], T2[0] + 0.5)) * (1 - lin(t, T2[1] - 0.4, T2[1]))
    draw_text(img, "Buat yang kirim, ini order", font("sb", 54), 540, 390, (255, 255, 255), a2, blur=14)
    a2b = ease_io(lin(t, T2[0] + 0.5, T2[0] + 1.0)) * (1 - lin(t, T2[1] - 0.4, T2[1]))
    draw_text(img, "yang sudah lama ditunggu.", font("sb", 54), 540, 462, (255, 222, 160), a2b, blur=14)
    for k, (txt, y, dt) in enumerate([("Satu paket,", 390, 0.05), ("satu penghasilan.", 480, 1.25)]):
        tt = T3[0] + dt
        a = ease_out(lin(t, tt, tt + 0.25)) * (1 - lin(t, T3[1] - 0.4, T3[1]))
        pulse = 1 + 0.10 * math.exp(-max(0, t - tt) * 6) * (t >= tt)
        draw_text(img, txt, font("xb", 80), 540, y, (255, 255, 255) if k == 0 else (255, 212, 140), a, pulse, blur=16)
    return to_arr(img)


def reveal(t):
    """10.9 -> 11.1: black screen gains depth - stars appear, 'GPS menyerah.' fades."""
    pass
