"""Anchor the logo to each label's own outline (all clips).

Feature tracking on the bag let the logo slide against the label wherever the bag had little texture.
The label is a bright white panel, so its filled outline is measured every frame: the centre follows it
almost exactly (light smoothing), the corner shape is smoothed strongly so the print does not breathe.
"""
import json, numpy as np, cv2

N = 121
CFG = {  # clip: search box (x0, y0, x1, y1), V min, S max
    1: ((360, 980, 720, 1380), 150, 45),
    2: ((200, 760, 780, 1280), 150, 45),
    3: ((140, 840, 470, 1180), 95, 50),
    4: ((0, 820, 330, 1250), 150, 45),
}


def label_mask(im, clip):
    """Filled outline of the white label (BGR frame) as a full-size 0/1 mask, or None."""
    (x0, y0, x1, y1), vmin, smax = CFG[clip]
    hsv = cv2.cvtColor(im[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 2] > vmin) & (hsv[..., 1] < smax)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    k, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if k < 2:
        return None
    j = np.argmax(st[1:, 4]) + 1
    if st[j, 4] < 1500:
        return None
    cnts, _ = cv2.findContours((lab == j).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    filled = np.zeros_like(m)
    cv2.drawContours(filled, [cv2.convexHull(max(cnts, key=cv2.contourArea))], -1, 1, -1)
    if filled[0].any() or filled[-1].any() or filled[:, 0].any() or filled[:, -1].any():
        return None                                   # label clipped by the search box / frame edge
    full = np.zeros(im.shape[:2], np.uint8)
    full[y0:y1, x0:x1] = filled
    return full


def order(pts):
    pts = np.array(pts, np.float32)
    s, d = pts.sum(1), np.diff(pts, axis=1)[:, 0]
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]], np.float32)


def quad(m):
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cnts, key=cv2.contourArea)
    a = cv2.approxPolyDP(c, 0.04 * cv2.arcLength(c, True), True).reshape(-1, 2)
    if len(a) != 4:
        a = cv2.boxPoints(cv2.minAreaRect(c))
    return order(a)


def smooth(arr, s):
    r = int(3 * s) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2)
    k /= k.sum()
    flat = arr.reshape(len(arr), -1)
    pad = np.pad(flat, ((r, r), (0, 0)), mode="edge")
    return np.stack([np.convolve(pad[:, j], k, "valid") for j in range(flat.shape[1])], 1).reshape(arr.shape)


if __name__ == "__main__":
    L = json.load(open("labels_v2.json"))                # v2 = bag-texture (KLT) tracks, used as fallback
    for n in CFG:
        Qk = np.array(L[str(n)]["quads"], np.float32)
        Q = np.full((N, 4, 2), np.nan)
        for i in range(N):
            m = label_mask(cv2.imread(f"../real/c{n}/{i + 1:03d}.jpg"), n)
            if m is not None:
                q = quad(m)
                M = cv2.moments(m, binaryImage=True)
                Q[i] = q - q.mean(0) + (M["m10"] / M["m00"], M["m01"] / M["m00"])
        area = np.array([cv2.contourArea(q.astype(np.float32)) if not np.isnan(q).any() else np.nan for q in Q])
        # sudden jumps = a highlight merged with the label or a brief occlusion
        loc = np.array([np.nanmedian(area[max(0, i - 3):i + 4]) for i in range(N)])
        ok = ~np.isnan(area) & (np.abs(area / loc - 1) < 0.08)
        # outline where it is measured; elsewhere the bag tracker carrying the nearest outline offset
        D = (Q - Qk).reshape(N, -1)
        for j in range(D.shape[1]):
            D[:, j] = np.interp(np.arange(N), np.where(ok)[0], D[ok, j])
        Q = Qk + D.reshape(N, 4, 2)
        ctr = Q.mean(1, keepdims=True)
        Qs = smooth(ctr, 0.8) + smooth(Q - ctr, 5.0)
        L[str(n)]["quads"] = Qs.round(2).tolist()
        w = np.linalg.norm(Qs[:, 1] - Qs[:, 0], axis=1)
        print(f"clip {n}: outline in {ok.sum()}/{N} frames, width {w.min():.0f}-{w.max():.0f}")
    json.dump(L, open("labels.json", "w"))
