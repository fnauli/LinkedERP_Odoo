"""Print the real H8KI logo into the tracked white bag label.

Multiply-blend (like ink on fabric): the label's own folds, lighting, grain and motion blur from the
footage stay visible through the logo. Dark marks inside the label (e.g. fake letters an AI model drew)
are inpainted away first so only the real logo shows.
"""
import json, numpy as np, cv2
from PIL import Image

_L = json.load(open("labels.json"))


def _logo_rgba():
    im = Image.open("logo.jpg").convert("RGB")
    a = np.asarray(im, np.float32)
    dist = np.max(np.abs(a - 247.0), axis=2)
    alpha = np.clip((dist - 6) / 40, 0, 1)
    col = np.clip((a - 247 * (1 - alpha[..., None])) / np.maximum(alpha[..., None], 1e-3), 0, 255)
    lg = Image.fromarray(np.dstack([col, alpha * 255]).astype(np.uint8), "RGBA")
    return lg.crop(lg.getbbox())


LOGO = _logo_rgba()
_tex_cache = {}
FULL_CLEAN = {1}


def ink(w, h):
    """Multiply map in label space: 1.0 = no ink, logo colours below 1 (4x supersampled)."""
    key = (int(w), int(h))
    if key in _tex_cache:
        return _tex_cache[key]
    S = 4
    Wt, Ht = max(8, int(w * S)), max(8, int(h * S))
    tex = Image.new("RGB", (Wt, Ht), (255, 255, 255))
    lw = int(Wt * 0.78)
    lh = int(LOGO.height * lw / LOGO.width)
    lg = LOGO.resize((lw, lh), Image.LANCZOS)
    tex.paste(lg, ((Wt - lw) // 2, int(Ht * 0.42 - lh / 2)), lg)
    m = np.asarray(tex, np.float32) / 255.0
    m = 1 - (1 - m) * 0.92                       # ink is slightly translucent, like a printed patch
    _tex_cache[key] = m
    return m


def apply(frame, clip, idx, strength=1.0):
    d = _L[str(clip)]
    idx = max(0, min(idx, len(d["quads"]) - 1))
    q = np.array(d["quads"][idx], np.float32)
    Hh, Ww = frame.shape[:2]
    # label mask (slightly inset so the printed border of the real label stays untouched)
    c = q.mean(0)
    lab = np.zeros((Hh, Ww), np.uint8)
    cv2.fillConvexPoly(lab, (c + (q - c) * 0.96).astype(np.int32), 255)
    x, y, bw, bh = cv2.boundingRect((c + (q - c) * 1.1).astype(np.int32))
    x, y = max(0, x), max(0, y)
    x2, y2 = min(Ww, x + bw), min(Hh, y + bh)
    if x2 - x < 8 or y2 - y < 8:
        return frame
    roi = frame[y:y2, x:x2].copy()
    mroi = lab[y:y2, x:x2]
    # remove dark marks (fake letters) inside the label, keep the fabric
    g = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    inner = cv2.erode((mroi > 0).astype(np.uint8), np.ones((5, 5), np.uint8))
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (27, 27))
    closed = cv2.morphologyEx(roi, cv2.MORPH_CLOSE, k)            # fabric with dark strokes filled in
    gc = cv2.cvtColor(closed, cv2.COLOR_RGB2GRAY)
    marks = ((gc.astype(np.int16) - g.astype(np.int16)) > 8) & (inner > 0)
    if clip in FULL_CLEAN:                                         # AI drew letters here: rebuild the label
        from track_clip1 import label_mask as _lm
        real = _lm(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))[y:y2, x:x2]
        inner = cv2.erode(real, np.ones((3, 3), np.uint8))           # exactly the label's own shape
        rng = np.random.default_rng(idx * 7 + clip)
        gi = g[inner > 0].astype(np.float32)
        med = np.median(gi)
        good = (inner > 0) & (np.abs(g.astype(np.float32) - med) < 8)
        yy, xx = np.nonzero(good)
        A = np.stack([np.ones_like(xx), xx, yy], 1).astype(np.float32)
        Yg, Xg = np.mgrid[0:roi.shape[0], 0:roi.shape[1]]
        G = np.stack([np.ones_like(Xg), Xg, Yg], -1).astype(np.float32)
        fabric = np.zeros(roi.shape, np.float32)
        for ch in range(3):                                         # smooth lighting gradient of the fabric
            coef, *_ = np.linalg.lstsq(A, roi[yy, xx, ch].astype(np.float32), rcond=None)
            fabric[..., ch] = G @ coef
        fabric += rng.normal(0, 2.2, fabric.shape[:2])[..., None]   # footage-like grain
        mk = cv2.GaussianBlur(inner.astype(np.float32), (0, 0), 1.0)[..., None]
        roi = np.clip(roi * (1 - mk) + fabric * mk, 0, 255).astype(np.uint8)
    elif marks.any():
        mk = cv2.GaussianBlur(cv2.dilate(marks.astype(np.uint8) * 255, np.ones((5, 5), np.uint8)).astype(np.float32) / 255,
                              (0, 0), 2.0)[..., None]
        smooth_fabric = cv2.GaussianBlur(closed, (0, 0), 3.0).astype(np.float32)
        grain = (roi.astype(np.float32) - cv2.GaussianBlur(roi, (0, 0), 1.0).astype(np.float32)) * 0.6
        roi = np.clip(roi * (1 - mk) + (smooth_fabric + grain) * mk, 0, 255).astype(np.uint8)
    # ink map warped into the frame
    w = max(np.linalg.norm(q[1] - q[0]), np.linalg.norm(q[2] - q[3]))
    h = max(np.linalg.norm(q[3] - q[0]), np.linalg.norm(q[2] - q[1]))
    m = ink(w, h)
    th, tw = m.shape[:2]
    src = np.array([[0, 0], [tw, 0], [tw, th], [0, th]], np.float32)
    M = cv2.getPerspectiveTransform(src, q - np.array([x, y], np.float32))
    warped = cv2.warpPerspective(m, M, (x2 - x, y2 - y), flags=cv2.INTER_AREA, borderValue=(1, 1, 1))
    warped = cv2.GaussianBlur(warped, (0, 0), 0.9)          # match the footage's softness
    pm = inner if clip in FULL_CLEAN else (mroi > 0)
    feather = cv2.GaussianBlur(pm.astype(np.float32), (0, 0), 1.2)[..., None] * strength
    printed = roi.astype(np.float32) * warped
    base = frame[y:y2, x:x2].astype(np.float32)
    out = base * (1 - feather) + printed * feather
    res = frame.copy()
    res[y:y2, x:x2] = np.clip(out, 0, 255).astype(np.uint8)
    return res
