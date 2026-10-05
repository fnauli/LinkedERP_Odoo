"""Shot 3: Kling printed only the left half of the logo on the bag label. Rebuild the label's fabric
and print the full H8KI logo into it (multiply blend, so folds, light and blur stay real)."""
import json
import numpy as np, cv2
from PIL import Image

_Q = np.array(json.load(open("../k1/shot3_quads.json")), np.float32)   # src frames 144..215


def _stabilise(Q):
    tl, tr, br, bl = Q[:, 0], Q[:, 1], Q[:, 2], Q[:, 3]
    left = bl - tl
    hl = np.linalg.norm(left, axis=1)
    right = br - tr
    cosang = np.sum(left * right, 1) / (hl * np.linalg.norm(right, axis=1) + 1e-6)
    r = np.linalg.norm(tr - tl, axis=1) / hl
    good = (cosang > 0.985) & (r > 1.0) & (r < 1.75)
    idx = np.arange(len(Q))
    r = np.interp(idx, idx[good], r[good])
    v = left / hl[:, None]
    perp = np.stack([v[:, 1], -v[:, 0]], 1)
    perp[perp[:, 0] < 0] *= -1
    out = np.stack([tl, tl + perp * (r * hl)[:, None], bl + perp * (r * hl)[:, None], bl], 1)
    k = np.exp(-0.5 * (np.arange(-3, 4) / 1.3) ** 2)
    k /= k.sum()
    pad = np.concatenate([out[:1].repeat(3, 0), out, out[-1:].repeat(3, 0)])
    sm = np.stack([np.tensordot(k, pad[i:i + 7], axes=(0, 0)) for i in range(len(out))])
    return sm


QS = _stabilise(_Q)


def _logo():
    im = np.asarray(Image.open("logo.jpg").convert("RGB"), np.float32)
    dist = np.max(np.abs(im - 247.0), axis=2)
    a = np.clip((dist - 6) / 40, 0, 1)
    col = np.clip((im - 247 * (1 - a[..., None])) / np.maximum(a[..., None], 1e-3), 0, 255)
    lg = Image.fromarray(np.dstack([col, a * 255]).astype(np.uint8), "RGBA")
    return lg.crop(lg.getbbox())


LOGO = _logo()
_ink = {}


def ink(w, h):
    key = (int(w), int(h))
    if key not in _ink:
        S = 4
        Wt, Ht = int(w * S), int(h * S)
        tex = Image.new("RGB", (Wt, Ht), (255, 255, 255))
        asp = LOGO.width / LOGO.height
        lw = int(min(Wt * 0.93, Ht * 0.86 * asp))
        lh = int(lw / asp)
        lg = LOGO.resize((lw, lh), Image.LANCZOS)
        tex.paste(lg, ((Wt - lw) // 2, (Ht - lh) // 2), lg)
        m = np.asarray(tex, np.float32) / 255.0
        _ink[key] = 1 - (1 - m) * 0.93
    return _ink[key]


W_C = float(np.percentile(np.linalg.norm(QS[:, 1] - QS[:, 0], axis=1), 90))
H_C = float(np.median(np.linalg.norm(QS[:, 3] - QS[:, 0], axis=1)))


def apply(frame, src_idx):
    """frame: HxWx3 uint8 RGB at the clip's native 1080x1916; src_idx: Kling frame number."""
    i = int(round(src_idx)) - 144
    if i < 0 or i >= len(QS):
        return frame
    q = QS[i]
    Hh, Ww = frame.shape[:2]
    c = q.mean(0)
    qc = c + (q - c) * 1.05                       # cover the old print right to the label edges
    x, y, bw, bh = cv2.boundingRect(np.vstack([qc, c + (q - c) * 1.15]).astype(np.int32))
    x, y = max(0, x), max(0, y)
    x2, y2 = min(Ww, x + bw), min(Hh, y + bh)
    roi = frame[y:y2, x:x2].astype(np.float32)
    mask = np.zeros((y2 - y, x2 - x), np.uint8)
    cv2.fillConvexPoly(mask, (qc - [x, y]).astype(np.int32), 255)
    hsv = cv2.cvtColor(frame[y:y2, x:x2], cv2.COLOR_RGB2HSV)
    inner = cv2.erode(mask, np.ones((9, 9), np.uint8)) > 0
    white = inner & (hsv[..., 1] < 60) & (hsv[..., 2] > 100)
    yy, xx = np.nonzero(white)
    if len(yy) < 50:
        return frame
    A = np.stack([np.ones_like(xx), xx, yy, xx * yy, xx * xx, yy * yy], 1).astype(np.float32)
    Yg, Xg = np.mgrid[0:roi.shape[0], 0:roi.shape[1]].astype(np.float32)
    G = np.stack([np.ones_like(Xg), Xg, Yg, Xg * Yg, Xg * Xg, Yg * Yg], -1)
    fabric = np.zeros_like(roi)
    for ch in range(3):
        coef, *_ = np.linalg.lstsq(A, roi[yy, xx, ch], rcond=None)
        fabric[..., ch] = G @ coef
    rng = np.random.default_rng(i)
    fabric += rng.normal(0, 2.0, fabric.shape[:2])[..., None]
    fabric = cv2.GaussianBlur(fabric, (0, 0), 0.6)
    m = ink(W_C, H_C)
    th, tw = m.shape[:2]
    src = np.array([[0, 0], [tw, 0], [tw, th], [0, th]], np.float32)
    M = cv2.getPerspectiveTransform(src, (q - [x, y]).astype(np.float32))
    warped = cv2.warpPerspective(m, M, (x2 - x, y2 - y), flags=cv2.INTER_AREA, borderValue=(1, 1, 1))
    warped = cv2.GaussianBlur(warped, (0, 0), 1.0)
    printed = fabric * warped
    feather = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 1.5)[..., None]
    out = roi * (1 - feather) + printed * feather
    res = frame.copy()
    res[y:y2, x:x2] = np.clip(out, 0, 255).astype(np.uint8)
    return res
