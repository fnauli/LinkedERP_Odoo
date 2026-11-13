"""Reel #5 "200 KARDUS. 1 HARI." - the Hoki team's real job for MIDO Indonesia, told as a race against the clock.
Real footage (stabilised, labels blurred, upscaled by prep.py) + a live clock and box counter, a dive into the
cartons that turns into an animated map of where they went, and a thank-you to the customer.
Every cut sits on the beat of the piano (0.68 s); its swell (track 50.74 s) lands on the map.
  python3 render_r5.py OUT.mp4 [preview t ...]"""
import sys, os, math, json, subprocess
from multiprocessing import Pool
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
from gfx import font, paste_layer, draw_text, text_size, check_icon, pop, back_in_out
from common import clamp, lin, ease_io, ease_out, ease_in

W, H, FPS = 1080, 1920, 24
DUR = 18.4
BEAT = 0.68
T_MAP = 8.4
TRACK_SWELL = 50.74
OFF = TRACK_SWELL - T_MAP
GOLD, RED, GREEN, NAVY = (255, 200, 50), (228, 30, 42), (37, 211, 102), (8, 14, 30)
WHITE = (255, 255, 255)
PRE = "../pre3/"
FPS_SRC = {"A": 30.0, "B": 29.97, "C": 30.0}
NFR = {"A": 235, "B": 166, "C": 334}

# (t0, t1, clip, src0, src1)
SHOTS = [
    (0.00, 2.28, "C", 5.0, 7.3),       # hook: the yard full of cartons
    (2.28, 5.00, "A", 3.0, 8.1),       # the team stacks the MIDO boxes (1.9x)
    (5.00, 6.36, "B", 0.0, 1.9),       # arranging by the scale
    (6.36, T_MAP, "B", 2.2, 4.4),      # close: labels on, boxes checked
    (13.16, 15.8, "C", 7.4, 10.3),     # back to the yard, the pan ends on the Lion Parcel x H8KI sign
    (15.8, DUR, "C", 10.3, 10.3),      # hold on the sign (slow push-in)
]
T_END = 15.2                            # closing card


# ------------------------------------------------------------------ footage
_cache = {}


def src_frame(clip, i):
    i = int(clamp(i, 0, NFR[clip] - 1))
    key = (clip, i)
    if key not in _cache:
        if len(_cache) > 40:
            _cache.clear()
        _cache[key] = cv2.cvtColor(cv2.imread(f"{PRE}{clip}/f{i + 1:04d}.jpg"), cv2.COLOR_BGR2RGB).astype(np.float32)
    return _cache[key]


def src_at(clip, s, blur=0.0):
    """Frame at source time s; blur>0 averages frames over +-blur s (motion blur for the sped-up shots)."""
    f = s * FPS_SRC[clip]
    if blur <= 0:
        i0 = int(math.floor(f)); a = f - i0
        return src_frame(clip, i0) * (1 - a) + src_frame(clip, i0 + 1) * a
    n = 3
    acc = 0
    for k in range(n):
        acc = acc + src_frame(clip, round(f + (k - (n - 1) / 2) * blur * FPS_SRC[clip]))
    return acc / n


def zoom(img, z, cx=W / 2, cy=H / 2):
    if abs(z - 1) < 1e-3:
        return img
    M = np.float32([[z, 0, cx - z * cx], [0, z, cy - z * cy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def zoom_blur(img, z, amt):
    """Radial 'punch' blur: average of a few progressively larger copies."""
    acc = zoom(img, z)
    for k in range(1, 4):
        acc = acc + zoom(img, z * (1 + amt * k / 3))
    return acc / 4


def footage(t):
    for t0, t1, c, s0, s1 in SHOTS:
        if t0 <= t < t1 + 1e-6:
            p = (t - t0) / (t1 - t0)
            s = s0 + (s1 - s0) * p
            speed = (s1 - s0) / (t1 - t0)
            f = src_at(c, s, blur=(0.5 / FPS_SRC[c]) if speed > 1.3 else 0)
            return f, t0, t1
    return None, 0, 0


# ------------------------------------------------------------------ grade + scrims
yy = np.mgrid[0:H, 0:W][0].astype(np.float32)
SCRIM_TOP = (np.clip((760 - yy) / 760, 0, 1) ** 1.6)[..., None]
SCRIM_BOT = (np.clip((yy - 900) / 1020, 0, 1) ** 1.4)[..., None]
VIG = None


def vignette():
    global VIG
    if VIG is None:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((x - W / 2) / (W * 0.62)) ** 2 + ((y - H / 2) / (H * 0.62)) ** 2)
        VIG = (1 - 0.32 * np.clip(r, 0, 1.4) ** 2.2)[..., None]
    return VIG


# ------------------------------------------------------------------ the map
GEO = json.load(open("../geo/IDN.geo.json"))
LON0, LAT0, KB = 90.0, 10.0, 80.0                # base map: 80 px per degree
BW, BH = int(34 * KB), int(22 * KB)              # lon 90..124, lat 10..-12


def b_xy(lon, lat):
    return (lon - LON0) * KB, (LAT0 - lat) * KB


def build_base():
    S = 1
    land = Image.new("L", (BW, BH), 0)
    d = ImageDraw.Draw(land)
    polys = []
    for feat in GEO["features"]:
        g = feat["geometry"]
        ps = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in ps:
            ring = [b_xy(lo, la) for lo, la in poly[0]]
            polys.append(ring)
            d.polygon(ring, fill=255)
    land_a = np.asarray(land, np.float32) / 255
    edge = np.asarray(land.filter(ImageFilter.FIND_EDGES), np.float32) / 255
    edge = cv2.GaussianBlur(cv2.dilate(edge, np.ones((3, 3), np.uint8)), (0, 0), 1.2)
    outer = cv2.GaussianBlur(land_a, (0, 0), 26)
    y, x = np.mgrid[0:BH, 0:BW].astype(np.float32)
    bg = np.zeros((BH, BW, 3), np.float32) + np.array(NAVY, np.float32)
    bg += (np.clip(1 - np.sqrt(((x - BW * 0.55) / BW) ** 2 + ((y - BH * 0.5) / BH) ** 2) * 1.6, 0, 1) ** 2)[..., None] * np.array([10, 26, 52], np.float32)
    grid = np.zeros((BH, BW), np.float32)          # faint graticule every 2 degrees
    for lo in range(90, 124, 2):
        grid[:, int((lo - LON0) * KB)] = 1
    for la in range(-10, 11, 2):
        grid[int((LAT0 - la) * KB), :] = 1
    grid = cv2.GaussianBlur(grid, (0, 0), 0.8) * 0.9
    bg += grid[..., None] * np.array([18, 34, 60], np.float32)
    bg += outer[..., None] * np.array([20, 70, 140], np.float32) * 0.55     # glow of the sea around the islands
    # land: a dotted, slightly lit surface
    dots = np.zeros((BH, BW), np.float32)
    dots[::9, ::9] = 1
    dots = cv2.GaussianBlur(cv2.dilate(dots, np.ones((3, 3), np.uint8)), (0, 0), 0.7)
    landcol = np.array([26, 52, 92], np.float32) + dots[..., None] * np.array([40, 80, 130], np.float32)
    out = bg * (1 - land_a[..., None]) + landcol * land_a[..., None]
    out += edge[..., None] * np.array([90, 190, 255], np.float32) * 0.9
    fx = np.clip(np.minimum(x, BW - 1 - x) / (3 * KB), 0, 1)
    fy = np.clip(np.minimum(y, BH - 1 - y) / (3 * KB), 0, 1)
    fade = (fx * fy)[..., None]                    # melt the edges of the base into the plain navy around it
    out = np.array(NAVY, np.float32) + (out - np.array(NAVY, np.float32)) * fade
    return np.clip(out, 0, 255)


BASE = None
ORIGIN = (106.63, -6.13)                          # Lion Parcel Cabang Airport, Tangerang
ISLANDS = [  # name, label lon/lat, arrival start, destination dots (no city names: addresses stay private)
    ("JAWA", (110.2, -8.75), 9.08, [(108.3, -7.2), (110.4, -7.0), (112.6, -7.4), (114.0, -8.0), (111.6, -7.8)]),
    ("SUMATERA", (99.6, 1.2), 9.76, [(104.8, -3.0), (101.4, 0.4), (98.7, 3.5), (105.3, -5.3), (100.4, -0.9)]),
    ("KALIMANTAN", (113.6, 1.3), 10.44, [(109.3, -0.1), (114.6, -3.4), (116.9, -1.3), (113.9, -2.3), (117.1, 0.4)]),
]
ARC_DUR = 0.9


def cam(t):
    """Map camera: (centre lon, lat, px per degree in the output)."""
    p = ease_io(lin(t, T_MAP, T_MAP + 1.3))
    q = ease_in(lin(t, 12.55, 13.16))                # dive back into Tangerang before the yard
    lon = ORIGIN[0] + (107.6 - ORIGIN[0]) * p
    lat = ORIGIN[1] + (-1.6 - ORIGIN[1]) * p
    k = 120 * (1 - p) + 40.5 * p
    k = k * (1 + 0.03 * lin(t, T_MAP + 1.3, 12.55))  # a slow drift-in while the arcs fly
    lon = lon + (ORIGIN[0] - lon) * q
    lat = lat + (ORIGIN[1] - lat) * q
    k = k * (1 + 5 * q * q)
    return lon, lat, k


def o_xy(lon, lat, c):
    clon, clat, k = c
    return W / 2 + (lon - clon) * k, 905 + (clat - lat) * k


def bez(p0, p2, h, s):
    mx, my = (p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2
    dx, dy = p2[0] - p0[0], p2[1] - p0[1]
    L = math.hypot(dx, dy) + 1e-6
    c = (mx + dy / L * h * L * 0.0 - 0, my - h * L)   # lift the arc upwards
    u = 1 - s
    return (u * u * p0[0] + 2 * u * s * c[0] + s * s * p2[0], u * u * p0[1] + 2 * u * s * c[1] + s * s * p2[1])


def plane_icon(size, ang):
    S = size * 4
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    pts = [(c + 0.48 * S, c), (c - 0.1 * S, c - 0.07 * S), (c - 0.22 * S, c - 0.42 * S), (c - 0.32 * S, c - 0.42 * S),
           (c - 0.26 * S, c - 0.06 * S), (c - 0.42 * S, c - 0.05 * S), (c - 0.5 * S, c - 0.2 * S), (c - 0.56 * S, c - 0.2 * S),
           (c - 0.52 * S, c), ]
    pts = pts + [(x, 2 * c - y) for x, y in reversed(pts[:-1])]
    d.polygon(pts, fill=(255, 255, 255, 255))
    im = im.rotate(-math.degrees(ang), resample=Image.BICUBIC)
    return im.resize((size, size), Image.LANCZOS)


def draw_map(t):
    global BASE
    if BASE is None:
        BASE = build_base()
    c = cam(t)
    clon, clat, k = c
    sc = k / KB
    bx, by = b_xy(clon, clat)
    M = np.float32([[sc, 0, W / 2 - sc * bx], [0, sc, 905 - sc * by]])
    img = cv2.warpAffine(BASE, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=NAVY)
    glow = np.zeros((H, W), np.float32)
    glowc = np.zeros((H, W, 3), np.float32)
    lay = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))     # supersampled lines and dots
    d = ImageDraw.Draw(lay)
    o = o_xy(*ORIGIN, c)
    planes = []
    for name, lab, ta, dests in ISLANDS:
        for j, dst in enumerate(dests):
            t0 = ta + j * 0.09
            s = ease_io(lin(t, t0, t0 + ARC_DUR))
            if s <= 0:
                continue
            p2 = o_xy(*dst, c)
            n = max(2, int(40 * s))
            pts = [bez(o, p2, 0.22, s * i / n) for i in range(n + 1)]
            pts2 = [(x * 2, y * 2) for x, y in pts]
            d.line(pts2, fill=GOLD + (235,), width=6, joint="curve")
            cv2.polylines(glow, [np.int32(pts)], False, 1.0, 9, cv2.LINE_AA)
            if s < 1 and j == 0:
                a = bez(o, p2, 0.22, max(0, s - 0.02))
                planes.append((pts[-1], math.atan2(pts[-1][1] - a[1], pts[-1][0] - a[0])))
            if s >= 1:                                   # arrival: a dot with a ring that pops out once
                q = lin(t, t0 + ARC_DUR, t0 + ARC_DUR + 0.6)
                x, y = p2[0] * 2, p2[1] * 2
                d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=WHITE + (255,))
                d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=GOLD + (255,))
                if q < 1:
                    r = 14 + 46 * ease_out(q)
                    d.ellipse((x - r, y - r, x + r, y + r), outline=GOLD + (int(255 * (1 - q)),), width=4)
                cv2.circle(glow, (int(p2[0]), int(p2[1])), 10, 1.0, -1, cv2.LINE_AA)
    # the origin: a pulsing Lion-red pin
    x, y = o[0] * 2, o[1] * 2
    for ph in (0.0, 0.5):
        q = ((t - T_MAP) * 0.9 + ph) % 1.0
        r = 20 + 70 * q
        d.ellipse((x - r, y - r, x + r, y + r), outline=RED + (int(220 * (1 - q)),), width=5)
    d.ellipse((x - 20, y - 20, x + 20, y + 20), fill=WHITE + (255,))
    d.ellipse((x - 13, y - 13, x + 13, y + 13), fill=RED + (255,))
    cv2.circle(glow, (int(o[0]), int(o[1])), 16, 1.4, -1, cv2.LINE_AA)
    glow = cv2.GaussianBlur(glow, (0, 0), 14)
    img = img + glow[..., None] * np.array([255, 170, 40], np.float32) * 0.55
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
    pil.alpha_composite(lay.resize((W, H), Image.LANCZOS))
    for (px, py), ang in planes:
        pl = plane_icon(46, ang)
        pil.alpha_composite(pl, (int(px - 23), int(py - 23)))
    # labels
    a, s_, dy = pop(t, T_MAP + 0.55, 0.5, 12.6, 0.3, rise=16)
    ox, oy = o_xy(*ORIGIN, c)
    if a > 0:
        f = font("b", 30)
        txt = "Tangerang"
        L = Image.new("RGBA", (int(f.getlength(txt)) + 44, 58), (0, 0, 0, 0))
        ImageDraw.Draw(L).rounded_rectangle((0, 0, L.width - 1, 57), 29, fill=RED + (255,))
        ImageDraw.Draw(L).text((22, 9), txt, font=f, fill=WHITE)
        paste_layer(pil, L, ox - 30, oy + 62 + dy, a, s_, anchor="r")
    for name, lab, ta, dests in ISLANDS:
        a, s_, dy = pop(t, ta + 0.55, 0.5, 12.6, 0.3, rise=16)
        lx, ly = o_xy(*lab, c)
        draw_text(pil, name, font("xb", 42), lx, ly + dy, WHITE, a, s_, shadow=0.9, blur=10)
    return pil


# ------------------------------------------------------------------ overlays
def pill(txt, f, bg, fg=WHITE, padx=40, h=None, icon=None):
    tw, th, b = text_size(txt, f)
    h = h or int(f.size * 2.1)
    iw = icon.width + 16 if icon is not None else 0
    w = int(tw + 2 * padx + iw)
    L = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new("L", L.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((20, 26, 20 + w, 26 + h), h // 2, fill=140)
    L.putalpha(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(L)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), h // 2, fill=bg)
    x = 20 + padx
    if icon is not None:
        L.alpha_composite(icon, (x, 20 + (h - icon.height) // 2))
        x += iw
    d.text((x - b[0], 20 + (h - th) // 2 - b[1]), txt, font=f, fill=fg)
    return L


def stamp(t, t0):
    """Hard 'stamp' entrance: big -> settle with a little bounce. Visible from t0 (t0<0 = already there)."""
    if t < t0:
        return 0, 1
    x = lin(t, t0, t0 + 0.28)
    s = 1.0 + 0.45 * (1 - ease_out(x)) - 0.06 * math.sin(math.pi * x) * (x < 1)
    return min(1, (t - t0) / 0.08 + (1 if t0 < 0 else 0)), s


def clock_face(size, hrs):
    S = size * 3
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((4, 4, S - 4, S - 4), outline=WHITE, width=int(S * 0.08))
    c = S / 2
    for ang, ln, wd in ((hrs / 12 * 2 * math.pi, 0.25, 0.09), (hrs % 1 * 2 * math.pi, 0.36, 0.06)):
        d.line([(c, c), (c + math.sin(ang) * S * ln, c - math.cos(ang) * S * ln)], fill=WHITE, width=int(S * wd))
    return im.resize((size, size), Image.LANCZOS)


T_C0, T_C1 = 2.28, 8.0                                     # clock 07.00 -> 21.00, counter 0 -> 200


def hours(t):
    return 7 + 14 * ease_io(lin(t, T_C0, T_C1)) ** 0.9


def count(t):
    return int(round(200 * (lin(t, T_C0, T_C1) ** 1.15)))


def phase(h):
    return "PAGI" if h < 11 else "SIANG" if h < 15 else "SORE" if h < 18.3 else "MALAM"


def hud_clock(img, t):
    a = ease_out(lin(t, T_C0, T_C0 + 0.3)) * (1 - ease_io(lin(t, T_MAP - 0.15, T_MAP)))
    if a <= 0:
        return
    h = hours(t)
    hh, mm = int(h), int((h % 1) * 60) // 15 * 15
    done = t >= T_C1
    L = Image.new("RGBA", (500, 130), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    d.rounded_rectangle((0, 0, 499, 129), 65, fill=(12, 16, 28, 215), outline=(GOLD if done else (255, 255, 255)) + (200,), width=3)
    L.alpha_composite(clock_face(78, h), (30, 26))
    d.text((128, 12), f"{hh:02d}.{mm:02d}", font=font("xb", 70), fill=GOLD if done else WHITE)
    d.text((345, 44), phase(h), font=font("b", 34), fill=(200, 210, 230))
    pulse = 1 + 0.06 * math.exp(-max(0, t - T_C1) * 6) * (t >= T_C1)
    paste_layer(img, L, W / 2, 250, a, pulse)


def hud_counter(img, t):
    a = ease_out(lin(t, T_C0, T_C0 + 0.3)) * (1 - ease_io(lin(t, T_MAP - 0.15, T_MAP)))
    if a <= 0:
        return
    n = count(t)
    done = n >= 200
    pulse = 1 + 0.12 * math.exp(-max(0, t - T_C1) * 5) * (t >= T_C1)
    f = font("xb", 150)
    txt = f"{n}"
    tw = f.getlength("200")
    draw_text(img, txt, f, W / 2 - 40, 1440, GOLD if done else WHITE, a, pulse, shadow=0.9, blur=16, anchor="r")
    draw_text(img, "/ 200", font("xb", 64), W / 2 - 20, 1410, (255, 255, 255), a * 0.9, 1, shadow=0.9, blur=12, anchor="l")
    draw_text(img, "kardus", font("sb", 44), W / 2 - 20, 1478, (220, 225, 235), a * 0.9, 1, shadow=0.9, blur=12, anchor="l")
    # progress bar
    p = min(1, n / 200)
    bar = Image.new("RGBA", (640, 22), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bar)
    bd.rounded_rectangle((0, 0, 639, 21), 11, fill=(255, 255, 255, 70))
    if p > 0.02:
        bd.rounded_rectangle((0, 0, int(639 * p), 21), 11, fill=GOLD + (255,))
    paste_layer(img, bar, W / 2, 1560, a)


CHECKS = [("Pickup", 6.36), ("Packing", 7.04), ("Loading", 7.72)]


def hud_checks(img, t):
    for k, (txt, t0) in enumerate(CHECKS):
        a, s, dy = pop(t, t0, 0.45, T_MAP, 0.15, rise=0)
        if a <= 0:
            continue
        x_off = -60 * (1 - ease_out(lin(t, t0, t0 + 0.3)))
        L = pill(txt, font("b", 44), (12, 16, 28, 220), icon=check_icon(56), padx=26, h=88)
        paste_layer(img, L, 40 + x_off, 860 + k * 112, a, s, anchor="l")


def hook(img, t):
    a, s = stamp(t, -1)
    draw_text(img, "200 KARDUS.", font("xb", 138), W / 2, 400, WHITE, a, s * (1 + 0.012 * t), shadow=0.9, blur=18)
    a, s = stamp(t, 0.42)
    if a > 0:
        draw_text(img, "1 HARI.", font("xb", 138), W / 2, 560, GOLD, a, s, shadow=0.9, blur=18)
    a, s = stamp(t, 0.95)
    if a > 0:
        L = pill("Bisa nggak?", font("xb", 62), RED + (255,), padx=46, h=118)
        L = L.rotate(-3, resample=Image.BICUBIC, expand=True)
        paste_layer(img, L, W / 2, 735, a, s)


def caption(img, t, l1, l2, t1, t2, t_out, y=330, s1=60, s2=78, col2=GOLD):
    a, sc, dy = pop(t, t1, 0.6, t_out, 0.4, rise=30)
    draw_text(img, l1, font("sb", s1), W / 2, y + dy, WHITE, a, sc, shadow=0.85, blur=14)
    if l2:
        a, sc, dy = pop(t, t2, 0.6, t_out, 0.4, rise=30)
        draw_text(img, l2, font("xb", s2), W / 2, y + 100 + dy, col2, a, sc, shadow=0.85, blur=14)


def wa_icon(size):
    S = size * 4
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((S * 0.1, S * 0.08, S * 0.92, S * 0.9), outline=WHITE, width=int(S * 0.09))
    d.polygon([(S * 0.12, S * 0.95), (S * 0.2, S * 0.66), (S * 0.36, S * 0.82)], fill=WHITE)
    return im.resize((size, size), Image.LANCZOS)


def closing(img, t):
    a, s, dy = pop(t, T_END + 0.15, 0.6)
    draw_text(img, "Kirim banyak?", font("sb", 66), W / 2, 1170 + dy, WHITE, a, s, shadow=0.9, blur=14)
    a, s, dy = pop(t, T_END + 0.45, 0.6)
    draw_text(img, "Serahkan ke kami.", font("xb", 92), W / 2, 1280 + dy, GOLD, a, s, shadow=0.9, blur=16)
    a, s, dy = pop(t, T_END + 0.85, 0.5)
    if a > 0:
        paste_layer(img, pill("Chat WhatsApp  ·  link di bio", font("b", 40), GREEN + (255,), icon=wa_icon(48), padx=36, h=96),
                    W / 2, 1420 + dy, a, s)
    a, s, dy = pop(t, T_END + 1.1, 0.5)
    if a > 0:
        paste_layer(img, pill("Follow untuk cerita tim kami", font("b", 36), (12, 16, 28, 225), padx=36, h=84),
                    W / 2, 1530 + dy, a, s)


# ------------------------------------------------------------------ frame
def flash(t, t0, d=0.12):
    return max(0.0, 1 - abs(t - t0) / d)


def frame(k):
    t = k / FPS
    in_map = T_MAP <= t < 13.16
    if not in_map:
        f, t0, t1 = footage(min(t, DUR - 1e-3))
        # punch-in on every cut, a slow push on the hook
        z = 1 + 0.035 * (1 - ease_out(lin(t, t0, t0 + 0.3)))
        if t0 == 0.0:
            z = 1.0 + 0.10 * ease_io(lin(t, 0, 2.28))
        if t0 == 13.16:
            z = 1.0 + 0.06 * (1 - ease_out(lin(t, 13.16, 14.2)))
        if t0 == 15.8:
            z = 1.0 + 0.07 * ease_io(lin(t, 15.8, DUR))
        # transition hook -> montage: zoom-blur punch over the cut
        if 2.28 - 0.17 <= t < 2.28:
            q = lin(t, 2.11, 2.28)
            f = zoom_blur(f, z * (1 + 0.25 * q * q), 0.12 * q)
        elif 2.28 <= t < 2.45:
            q = 1 - lin(t, 2.28, 2.45)
            f = zoom_blur(f, z * (1 + 0.25 * q * q), 0.12 * q)
        elif T_MAP - 0.42 <= t < T_MAP:                  # dive into the cartons...
            q = ease_in(lin(t, T_MAP - 0.42, T_MAP))
            f = zoom_blur(f, z * (1 + 1.6 * q), 0.25 * q)
        elif 13.16 <= t < 13.4:                          # ...and out of the map into the yard
            q = 1 - ease_out(lin(t, 13.16, 13.4))
            f = zoom_blur(f, z * (1 + 0.8 * q), 0.18 * q)
        elif t0 == 15.8:
            f = zoom(f, z, 380, 640)
        else:
            f = zoom(f, z)
        # a touch of golden light through the long day
        g = lin(t, 2.28, T_MAP) * (t < T_MAP)
        f = f * np.array([1 + 0.05 * g, 1 + 0.01 * g, 1 - 0.06 * g], np.float32)
        top = 1.0 if t < 2.28 else ease_out(lin(t, 2.28, 2.6)) * 0.55 if t < T_MAP else \
            ease_out(lin(t, 13.4, 13.8)) * (1 - ease_io(lin(t, T_END - 0.3, T_END)))
        bot = ease_out(lin(t, 2.28, 2.6)) * (t < T_MAP) * 0.85 + ease_out(lin(t, T_END, T_END + 0.5)) * (t >= T_END)
        f = f * (1 - 0.6 * top * SCRIM_TOP) * (1 - 0.72 * bot * SCRIM_BOT) * vignette()
        fl = flash(t, 2.28, 0.08) * 0.35 + flash(t, T_C1, 0.12) * 0.18
        if fl > 0:
            f = f + (255 - f) * fl
        img = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).convert("RGBA")
        if t < 2.28:
            hook(img, t)
        hud_clock(img, t)
        hud_counter(img, t)
        hud_checks(img, t)
        caption(img, t, "Terima kasih, MIDO Indonesia,", "atas kepercayaannya.", 13.45, 13.85, T_END - 0.05, y=300, s1=54, s2=72)
        if t >= T_END:
            closing(img, t)
    else:
        img = draw_map(t)
        q = 1 - ease_out(lin(t, T_MAP, T_MAP + 0.25))     # arrive out of the white of the dive
        q2 = ease_in(lin(t, 12.95, 13.16))
        if q > 0 or q2 > 0:
            arr = np.asarray(img.convert("RGB"), np.float32)
            arr = arr + (255 - arr) * max(q * 0.6, q2 * 0.5)
            img = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
        caption(img, t, "Malam itu,", "200 kardus siap berangkat.", T_MAP + 0.2, T_MAP + 0.55, 10.9, y=300, s1=58, s2=66)
        caption(img, t, "Ke 3 pulau,", "dalam 1 hari kerja.", 11.05, 11.4, 12.85, y=300, s1=58, s2=74)
        for j, (big, small) in enumerate((("200", "kardus"), ("1", "hari"), ("3", "pulau"))):
            a, s, dy = pop(t, 11.55 + j * 0.17, 0.5, 12.85, 0.3)
            if a > 0:
                L = Image.new("RGBA", (260, 200), (0, 0, 0, 0))
                dd = ImageDraw.Draw(L)
                dd.rounded_rectangle((0, 0, 259, 199), 36, fill=(18, 28, 50, 230), outline=GOLD + (160,), width=3)
                fb = font("xb", 92)
                dd.text((130 - fb.getlength(big) / 2, 8), big, font=fb, fill=GOLD)
                fs = font("sb", 38)
                dd.text((130 - fs.getlength(small) / 2, 126), small, font=fs, fill=WHITE)
                paste_layer(img, L, W / 2 + (j - 1) * 290, 1400 + dy, a, s)
        a, s, dy = pop(t, 11.25, 0.5, 12.85, 0.3)
        if a > 0:
            paste_layer(img, pill("Dikirim via Lion Parcel", font("b", 40), RED + (255,), icon=plane_icon(52, 0), padx=34, h=96),
                        W / 2, 520 + dy, a, s)
    return np.asarray(img.convert("RGB"))


def frame_bytes(k):
    return frame(k).tobytes()


if __name__ == "__main__":
    out = sys.argv[1]
    if len(sys.argv) > 2:
        for tt in map(float, sys.argv[2:]):
            Image.fromarray(frame(int(round(tt * FPS)))).save(f"{out}_{tt:05.2f}.jpg", quality=90)
        sys.exit()
    audio = os.environ.get("AUDIO", "audio_r5.wav")
    n = int(round(DUR * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", audio, "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-tune", "film",
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
