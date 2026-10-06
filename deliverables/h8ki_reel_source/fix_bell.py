"""Clip B, frames 1-63: make the courier really press the bell.

Kling's finger stops over the gate, ~45 px short of the intercom on the pillar. Two small, physical changes:
1. the intercom box moves 29 px right / 38 px down, to the pillar's edge next to the gate (where gate bells
   usually sit); its real cast shadow moves with it and the old spot is filled with the pillar's own wall;
2. his forearm/hand is stretched 27 px toward it (tapering to 0 at the elbow), so the fingertip lands on the
   call button for frames 8-16. The camera is locked off, so frame 46 (arm down) is a clean plate.
A small warm LED lights while the button is pressed."""
import numpy as np, cv2

CLEAN = 46
BOX = (153, 753, 197, 855)                     # intercom on the pillar (x0, y0, x1, y1)
PATCH = (146, 746, 205, 874)                   # box + its soft shadow below
MOVE = (29, 38)
PILLAR_EDGE = 230
# fingertip x per frame (frames 1..29), measured against the clean plate
TIP = [284, 279, 272, 267, 262, 256, 252, 249, 246, 243, 242, 241, 241, 243, 246, 250, 254, 259, 264, 269,
       272, 273, 277, 279, 287, 289, 306, 313, 341]
TIP_Y = 867
SHIFT = 27
ARM_END = 455                                   # displacement tapers to 0 here (before the shoulder)


def _rd(i):
    return cv2.cvtColor(cv2.imread(f"../new/b/{i:03d}.jpg"), cv2.COLOR_BGR2RGB)


_static = {}


def _pillar():
    """Clean-plate pillar with the box moved: (patch image, region)."""
    if _static:
        return _static["img"], _static["reg"]
    cp = _rd(CLEAN)
    x0, y0, x1, y1 = PATCH
    m = np.zeros(cp.shape[:2], np.uint8)
    cv2.rectangle(m, (x0, y0), (x1, y1), 255, -1)
    wall = cv2.inpaint(cp, m, 9, cv2.INPAINT_TELEA)
    # re-grain the inpainted wall like the surrounding plaster
    rng = np.random.default_rng(5)
    ref = cp[y0:y1, x1 + 3:x1 + 20].astype(np.float32)
    sd = float((ref - cv2.GaussianBlur(ref, (0, 0), 2)).std())
    g = cv2.GaussianBlur(rng.normal(0, sd * 1.6, (cp.shape[0], cp.shape[1])).astype(np.float32), (0, 0), 0.7)
    wall = wall.astype(np.float32)
    wall[m > 0] += g[m > 0][:, None]
    # ratio map of the box + shadow against the empty wall, moved to the new place
    cpf = cp.astype(np.float32)
    ratio = np.ones_like(cpf)
    ratio[y0:y1, x0:x1] = np.clip((cpf[y0:y1, x0:x1] + 1) / (wall[y0:y1, x0:x1] + 1), 0.05, 1.2)
    bx0, by0, bx1, by1 = BOX
    alpha = np.zeros(cp.shape[:2], np.float32)
    cv2.rectangle(alpha, (bx0 + 1, by0 + 1), (bx1 - 1, by1 - 1), 1.0, -1)
    alpha = cv2.GaussianBlur(alpha, (0, 0), 0.8)
    dx, dy = MOVE
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    H, W = cp.shape[:2]
    ratio_m = cv2.warpAffine(ratio, M, (W, H), borderValue=(1, 1, 1))
    box_m = cv2.warpAffine(cpf, M, (W, H))
    alpha_m = cv2.warpAffine(alpha, M, (W, H))[..., None]
    out = wall * ratio_m                                    # shadow + box darkening carried over
    out = out * (1 - alpha_m) + box_m * alpha_m             # the box itself, pixel for pixel
    reg = (x0 - 6, y0 - 6, PILLAR_EDGE + 2, y1 + dy + 8)
    _static["img"], _static["reg"] = out, reg
    _static["led"] = (bx0 + dx + (bx1 - bx0) // 2, by0 + dy + int((by1 - by0) * 0.62))
    return out, reg


def apply(i, frame=None):
    """Return fixed RGB frame i (1-based) of clip B."""
    f = (_rd(i) if frame is None else frame).astype(np.float32)
    if i > 63:
        return f.astype(np.uint8)
    pil, (x0, y0, x1, y1) = _pillar()
    cp = _rd(CLEAN).astype(np.float32)
    # per-frame exposure flicker of the plate
    off = f[y0:y1, x0:x1].mean((0, 1)) - cp[y0:y1, x0:x1].mean((0, 1))
    region = pil[y0:y1, x0:x1] + off
    fm = np.zeros(f.shape[:2], np.float32)
    cv2.rectangle(fm, (x0, y0), (x1 - 1, y1 - 1), 1.0, -1)
    fm = cv2.GaussianBlur(fm, (0, 0), 1.5)[y0:y1, x0:x1, None]
    # never paint over the arm (it stays in front of the pillar)
    f[y0:y1, x0:x1] = f[y0:y1, x0:x1] * (1 - fm) + region * fm
    pressed = 0.0
    if i <= len(TIP):
        tip = TIP[i - 1]
        s = SHIFT * float(np.clip((29 - i) / 6.0, 0, 1))      # ease out while the arm retracts
        if s > 0.3:
            raw = _rd(i).astype(np.float32)
            band = (slice(780, 1000), slice(200, ARM_END + 40))
            d = np.abs(raw - cp).sum(2)
            arm = np.zeros(f.shape[:2], np.uint8)
            arm[band] = (d[band] > 55).astype(np.uint8)
            arm[:, ARM_END:] = 0
            arm = cv2.morphologyEx(arm, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
            arm = cv2.morphologyEx(arm, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
            n, lab, st, _ = cv2.connectedComponentsWithStats(arm)
            if n > 1:
                k = 1 + int(np.argmax(st[1:, 4]))
                arm = (lab == k).astype(np.uint8)
            H, W = f.shape[:2]
            gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
            span = max(120.0, ARM_END - tip)
            w = np.clip(1 - (gx - tip) / span, 0, 1)
            w[:, :int(tip - s - 40)] = 1.0
            mapx = gx + s * w
            warped = cv2.remap(raw, mapx, gy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            wm = cv2.remap(arm.astype(np.float32), mapx, gy, cv2.INTER_LINEAR)
            # remove the original arm (clean plate), then lay the stretched arm back on top
            om = cv2.GaussianBlur(cv2.dilate(arm, np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 1.0)[..., None]
            bg = cp + off
            bg[y0:y1, x0:x1] = bg[y0:y1, x0:x1] * (1 - fm) + region * fm
            f = f * (1 - om) + bg * om
            wm = cv2.GaussianBlur(wm, (0, 0), 0.7)[..., None]
            f = f * (1 - wm) + warped * wm
            if tip - s <= 222 + 3:
                pressed = float(np.clip((225 - (tip - s)) / 4.0, 0, 1))
    if pressed > 0:                                         # the button's LED wakes up
        lx, ly = _static["led"]
        yy, xx = np.mgrid[ly - 14:ly + 15, lx - 14:lx + 15]
        g = np.exp(-((xx - lx) ** 2 + (yy - ly) ** 2) / (2 * 2.2 ** 2))
        f[ly - 14:ly + 15, lx - 14:lx + 15] += (g * 120 * pressed)[..., None] * np.array([1.0, 0.75, 0.35], np.float32)
    return np.clip(f, 0, 255).astype(np.uint8)
