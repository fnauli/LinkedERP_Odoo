"""Composite the real H8KI logo onto the tracked white bag label (perspective-correct, lit to match)."""
import json, numpy as np, cv2
from PIL import Image

_L = json.load(open("labels.json"))


def _logo_rgba():
    im = Image.open("logo.jpg").convert("RGB")
    a = np.asarray(im, np.float32)
    dist = np.max(np.abs(a - 247.0), axis=2)
    alpha = np.clip((dist - 6) / 40, 0, 1)
    col = np.clip((a - 247 * (1 - alpha[..., None])) / np.maximum(alpha[..., None], 1e-3), 0, 255)
    rgba = np.dstack([col, alpha * 255]).astype(np.uint8)
    lg = Image.fromarray(rgba, "RGBA")
    return lg.crop(lg.getbbox())


LOGO = _logo_rgba()


def texture(w, h):
    """Portrait white label with the logo centred (texture space, 4x supersampled)."""
    S = 4
    W, H = int(w * S), int(h * S)
    tex = Image.new("RGB", (W, H), (255, 255, 255))
    lw = int(W * 0.86)
    lh = int(LOGO.height * lw / LOGO.width)
    lg = LOGO.resize((lw, lh), Image.LANCZOS)
    tex.paste(lg, ((W - lw) // 2, int(H * 0.40 - lh / 2)), lg)
    return np.asarray(tex, np.float32)


def apply(frame, clip, idx, strength=1.0):
    """frame: HxWx3 uint8 RGB (clip native res). idx: 0-based frame index."""
    d = _L[str(clip)]
    idx = max(0, min(idx, len(d["quads"]) - 1))
    q = np.array(d["quads"][idx], np.float32)
    col = np.array(d["colors"][idx], np.float32)
    c = q.mean(0)
    q = c + (q - c) * 1.06                      # cover the printed edge / any fake letters
    w = max(np.linalg.norm(q[1] - q[0]), np.linalg.norm(q[2] - q[3]))
    h = max(np.linalg.norm(q[3] - q[0]), np.linalg.norm(q[2] - q[1]))
    tex = texture(w, h)
    th, tw = tex.shape[:2]
    src = np.array([[0, 0], [tw, 0], [tw, th], [0, th]], np.float32)
    M = cv2.getPerspectiveTransform(src, q)
    Hh, Ww = frame.shape[:2]
    warped = cv2.warpPerspective(tex, M, (Ww, Hh), flags=cv2.INTER_AREA)
    mask = cv2.warpPerspective(np.ones((th, tw), np.float32), M, (Ww, Hh), flags=cv2.INTER_LINEAR)
    mask = cv2.GaussianBlur(mask, (0, 0), 1.2) * strength
    lit = warped * (col / 255.0)[None, None, :] * 1.02
    lit = cv2.GaussianBlur(lit, (0, 0), 0.6)
    out = frame.astype(np.float32) * (1 - mask[..., None]) + lit * mask[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)
