"""Back view (clip A 1-80) and bell shot (clip B 1-63): one bag, one print.

Kling drew a different label in each shot (59% vs 84% of the bag face) and lit it like a glowing sticker
(up to 3x brighter than the bag's own silver strip). Here the Kling label is painted out with the bag's
fabric, and the real H8KI print is laid onto the fabric:
  * same size and place on the bag face in both shots (face coordinates: 70% wide, 30% tall, centre v=0.64)
  * texture-locked: chained ECC homographies of the bag face, so it rides the fabric exactly
  * lit like the bag: panel brightness = white-fabric albedo x the light measured on the red fabric, tint
    from the scene light; follows the fabric's own shading gradient, carries its grain
  * printed, not stuck: no white border, soft edge, a faint stitched seam, ink slightly translucent,
    same softness as the footage."""
import json, os
import numpy as np, cv2
from PIL import Image

SCENES = {
    "a": dict(ref=1, frames=range(1, 74),
              face=[[405, 800], [700, 800], [705, 1140], [410, 1140]],
              label=[[460, 994], [633, 994], [633, 1080], [460, 1080]]),
    "b": dict(ref=1, frames=range(1, 64),
              face=[[800, 868], [990, 866], [992, 1180], [802, 1182]],
              label=[[822, 996], [982, 994], [983, 1133], [824, 1136]]),
}
PANEL_UV = (0.15, 0.49, 0.85, 0.79)            # u0, v0, u1, v1 on the bag face
UNIT = np.float32([[0, 0], [1, 0], [1, 1], [0, 1]])


def rd(clip, i):
    return cv2.cvtColor(cv2.imread(f"../new/{clip}/{i:03d}.jpg"), cv2.COLOR_BGR2RGB)


def lin(x):
    x = x / 255.0
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def srgb(x):
    x = np.clip(x, 0, 1)
    return 255.0 * np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055)


# ------------------------------------------------------------------ tracking
def track(clip):
    path = f"track_{clip}.json"
    if os.path.exists(path):
        return [np.array(h, np.float64) for h in json.load(open(path))]
    S = SCENES[clip]
    face = np.float32(S["face"])
    g = lambda i: cv2.GaussianBlur(cv2.cvtColor(rd(clip, i), cv2.COLOR_RGB2GRAY).astype(np.float32), (0, 0), 1.0)
    Hc = np.eye(3)
    Hs = [Hc.copy()]
    prev = g(S["frames"][0])
    crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-5)
    for i in list(S["frames"])[1:]:
        cur = g(i)
        q = cv2.perspectiveTransform(face[None], Hc.astype(np.float32))[0]
        c = q.mean(0)
        qi = c + (q - c) * 0.94
        x, y, w, h = cv2.boundingRect(q.astype(np.int32))
        X0, Y0 = max(0, x - 50), max(0, y - 50)
        X1, Y1 = min(1080, x + w + 50), min(1916, y + h + 50)
        m = np.zeros((Y1 - Y0, X1 - X0), np.uint8)
        cv2.fillConvexPoly(m, (qi - [X0, Y0]).astype(np.int32), 255)
        dH = np.eye(3, dtype=np.float32)
        try:
            _, dH = cv2.findTransformECC(prev[Y0:Y1, X0:X1], cur[Y0:Y1, X0:X1], dH, cv2.MOTION_HOMOGRAPHY, crit, m, 5)
        except cv2.error:
            dH = np.eye(3, dtype=np.float32)
        T = np.array([[1, 0, X0], [0, 1, Y0], [0, 0, 1]], np.float64)
        Hc = T @ dH.astype(np.float64) @ np.linalg.inv(T) @ Hc
        Hc /= Hc[2, 2]
        Hs.append(Hc.copy())
        prev = cur
    json.dump([h.tolist() for h in Hs], open(path, "w"))
    return Hs


# ------------------------------------------------------------------ the print
def _logo():
    im = np.asarray(Image.open("logo.jpg").convert("RGB"), np.float32)
    dist = np.max(np.abs(im - 247.0), axis=2)
    a = np.clip((dist - 6) / 40, 0, 1)
    col = np.clip((im - 247 * (1 - a[..., None])) / np.maximum(a[..., None], 1e-3), 0, 255)
    lg = Image.fromarray(np.dstack([col, a * 255]).astype(np.uint8), "RGBA")
    return lg.crop(lg.getbbox())


def panel_texture(pw=1400, ph=600):
    """Albedo-relative texture of a SEWN-ON patch (1 = white twill), in panel space:
    merrowed (overlocked) navy border with its diagonal wrap stitches, a running stitch just inside it,
    twill weave, and embroidered letters with a hint of relief."""
    tex = Image.new("RGB", (pw, ph), (255, 255, 255))
    lg = _logo()
    asp = lg.width / lg.height
    lw = int(min(pw * 0.76, ph * 0.66 * asp))
    lh = int(lw / asp)
    lg = lg.resize((lw, lh), Image.LANCZOS)
    tex.paste(lg, ((pw - lw) // 2, (ph - lh) // 2), lg)
    t = lin(np.asarray(tex, np.float32))
    ink = 1 - np.clip(t.mean(2), 0, 1)                                   # 0 = twill, ~1 = thread
    # embroidered letters: thread sits slightly proud of the twill (lit from above)
    gy = np.gradient(cv2.GaussianBlur(ink, (0, 0), 3), axis=0)
    t = t * (1 - 3.0 * gy[..., None]).clip(0.85, 1.15)
    yy, xx = np.mgrid[0:ph, 0:pw].astype(np.float32)
    t = t * (1 + 0.035 * np.sin((xx + yy) * 2 * np.pi / 9))[..., None]  # twill weave
    navy = lin(np.float32([[[48, 62, 112]]]))[0, 0]
    bw = int(ph * 0.075)                                                  # merrowed border
    d = np.minimum(np.minimum(xx, pw - 1 - xx), np.minimum(yy, ph - 1 - yy))
    border = d < bw
    wrap = 0.82 + 0.18 * (0.5 + 0.5 * np.sin((xx - yy) * 2 * np.pi / 22))  # diagonal wrap stitches
    roll = 1.10 - 0.25 * ((d - bw / 2) / (bw / 2)) ** 2                    # rounded, rolled edge
    t[border] = (navy[None, :] * (wrap * roll)[border][:, None])
    # bevel: the padded patch catches light on its top edge, falls off at the bottom
    t[border & (yy < ph / 2)] *= 1.12
    t[border & (yy > ph / 2)] *= 0.86
    # running stitch inside the border (navy thread, dashed)
    si = bw + int(ph * 0.035)
    th = max(6, int(ph * 0.014))
    run = np.zeros((ph, pw), bool)
    for (y0, y1, x0, x1, horiz) in [(si, si + th, si, pw - si, True), (ph - si - th, ph - si, si, pw - si, True),
                                    (si, ph - si, si, si + th, False), (si, ph - si, pw - si - th, pw - si, False)]:
        seg = np.zeros((ph, pw), bool)
        seg[y0:y1, x0:x1] = True
        pos = xx if horiz else yy
        seg &= ((pos - si) % 34) < 22
        run |= seg
    t[run] = navy[None, :] * 1.1
    return t


TEX = panel_texture()
_hue_cache = {}


def _hue(clip, raw, Lq):
    """Scene light tint: half Kling's label white, half the bag's silver lid strip, desaturated."""
    if clip in _hue_cache:
        return _hue_cache[clip]
    S = SCENES[clip]
    f = lin(raw.astype(np.float32))
    m = np.zeros(raw.shape[:2], np.uint8)
    cv2.fillConvexPoly(m, Lq.astype(np.int32), 255)
    px = f[m > 0]
    lum = px.mean(1)
    kw = np.median(px[lum > np.percentile(lum, 75)], 0)
    F = np.float32(S["face"])
    y = int(F[0, 1] + 0.08 * (F[3, 1] - F[0, 1]))   # strip just under the lid edge
    x0, x1 = int(F[0, 0] + 0.15 * (F[1, 0] - F[0, 0])), int(F[0, 0] + 0.85 * (F[1, 0] - F[0, 0]))
    st = np.median(f[y - 5:y + 6, x0:x1].reshape(-1, 3), 0)
    h = 0.5 * kw / kw[0] + 0.5 * st / st[0]
    h = 0.5 * h + 0.5
    _hue_cache[clip] = (h.astype(np.float32), kw.astype(np.float32))
    return _hue_cache[clip]


def apply(clip, i, frame=None):
    S = SCENES[clip]
    raw = rd(clip, i) if frame is None else frame
    if i not in S["frames"]:
        return raw
    Hs = track(clip)
    H = Hs[i - S["frames"][0]]
    F0, L0 = np.float32(S["face"]), np.float32(S["label"])
    G = H @ cv2.getPerspectiveTransform(UNIT, F0).astype(np.float64)     # face (u,v) -> image
    Fq = cv2.perspectiveTransform(F0[None], H.astype(np.float32))[0]
    Lq = cv2.perspectiveTransform(L0[None], H.astype(np.float32))[0]
    u0, v0, u1, v1 = PANEL_UV
    Pq = cv2.perspectiveTransform(np.float32([[u0, v0], [u1, v0], [u1, v1], [u0, v1]])[None], G.astype(np.float32))[0]
    hue, kw = _hue(clip, rd(clip, S["ref"]), L0)

    # working ROI
    allq = np.vstack([Fq, Lq, Pq])
    x, y, w, h = cv2.boundingRect(allq.astype(np.int32))
    X0, Y0 = max(0, x - 8), max(0, y - 8)
    X1, Y1 = min(raw.shape[1], x + w + 8), min(raw.shape[0], y + h + 8)
    roi = lin(raw[Y0:Y1, X0:X1].astype(np.float32))
    off = np.array([X0, Y0], np.float32)
    mk = lambda q, s=1.0: _poly(roi.shape[:2], q - off, s)
    face_m = mk(Fq, 0.97)
    lab_m = cv2.dilate(mk(Lq), np.ones((15, 15), np.uint8))
    pan_m = mk(Pq)
    fill_m = cv2.dilate(np.maximum(mk(Lq), pan_m), np.ones((9, 9), np.uint8)) & face_m

    # (u, v) of every ROI pixel on the bag face
    Gi = np.linalg.inv(G)
    yy, xx = np.mgrid[Y0:Y1, X0:X1].astype(np.float64)
    den = Gi[2, 0] * xx + Gi[2, 1] * yy + Gi[2, 2]
    U = (Gi[0, 0] * xx + Gi[0, 1] * yy + Gi[0, 2]) / den
    V = (Gi[1, 0] * xx + Gi[1, 1] * yy + Gi[1, 2]) / den

    # fabric model from the bag's own red cloth around the label (quadratic shading + its grain)
    samp = (face_m > 0) & (lab_m == 0) & (V > 0.16)
    A = np.stack([np.ones_like(U), U, V, U * V, U * U, V * V], -1)
    fab = np.zeros_like(roi)
    res_sd = np.zeros(3)
    for ch in range(3):
        coef, *_ = np.linalg.lstsq(A[samp], roi[..., ch][samp], rcond=None)
        fab[..., ch] = A @ coef
        r_ = roi[..., ch][samp] - fab[..., ch][samp]
        res_sd[ch] = 1.4826 * np.median(np.abs(r_ - np.median(r_)))      # robust: ignore seams/piping
    rng = np.random.default_rng(i * 13 + (7 if clip == "b" else 0))
    grain = cv2.GaussianBlur(rng.normal(0, 1, roi.shape[:2]).astype(np.float32), (0, 0), 0.9)
    grain /= grain.std() + 1e-6
    rel = grain * 0.35                                           # fabric weave, relative
    cloth = fab * (1 + rel[..., None] * (res_sd / np.maximum(fab.mean((0, 1)), 1e-4)).astype(np.float32) * 0.6)

    # printed panel: white fabric (0.85) under the light measured on the red fabric (red albedo ~0.45)
    E = np.maximum(fab[..., 0], 1e-5) / 0.45
    pan = 0.85 * E[..., None] * hue[None, None, :]
    # never brighter than 80% of Kling's glowing label (it was right about the light, wrong about the level)
    pin = pan[pan_m > 0].mean(0) if (pan_m > 0).any() else kw
    pan = pan * min(1.0, float(np.min(0.8 * kw / np.maximum(pin, 1e-6))))
    th, tw = TEX.shape[:2]
    Mp = cv2.getPerspectiveTransform(np.float32([[0, 0], [tw, 0], [tw, th], [0, th]]), Pq - off)
    tex = cv2.warpPerspective(TEX, Mp, (X1 - X0, Y1 - Y0), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)
    pan = pan * tex * (1 + rel[..., None] * 0.05)

    pa = cv2.GaussianBlur(pan_m.astype(np.float32) / 255, (0, 0), 0.7)[..., None]
    # the padded patch stands ~2 mm off the bag: a soft contact shadow below it, and the cloth
    # puckers slightly where the stitches pull it
    sc = max(1.0, (Pq[2, 1] - Pq[1, 1]) / 60.0)                   # shadow scale ~ patch size on screen
    Ms = np.float32([[1, 0, 0.6 * sc], [0, 1, 1.6 * sc]])
    sh = cv2.warpAffine(pan_m.astype(np.float32) / 255, Ms, (pan_m.shape[1], pan_m.shape[0]))
    sh = cv2.GaussianBlur(sh, (0, 0), 1.3 * sc)[..., None] * (1 - pa)
    ring = cv2.GaussianBlur(cv2.dilate(pan_m, np.ones((5, 5), np.uint8)).astype(np.float32) / 255, (0, 0), 2.0 * sc)[..., None] * (1 - pa)
    cloth = cloth * (1 - 0.45 * sh) * (1 - 0.10 * ring * (0.5 + 0.5 * np.sign(rel[..., None])))
    out = cloth * (1 - pa) + pan * pa
    out = cv2.GaussianBlur(out, (0, 0), 0.75)                    # same softness as the footage
    fa = cv2.GaussianBlur(fill_m.astype(np.float32) / 255, (0, 0), 1.2)[..., None]
    res = roi * (1 - fa) + out * fa
    res = srgb(res) + rng.normal(0, 1.2, res.shape)
    final = raw.copy()
    final[Y0:Y1, X0:X1] = np.clip(res, 0, 255).astype(np.uint8)
    return final


def _poly(shape, q, s=1.0):
    m = np.zeros(shape, np.uint8)
    c = q.mean(0)
    cv2.fillConvexPoly(m, (c + (q - c) * s).astype(np.int32), 255)
    return m
