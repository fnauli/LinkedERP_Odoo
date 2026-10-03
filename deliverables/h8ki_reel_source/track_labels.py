"""Planar tracking of the white bag label in each Kling clip.

v1 re-detected the label outline every frame; lighting and fold shadows made that outline (and so the
logo) breathe by up to 30 %. v2 seeds the quad once from a clean detection and then moves it with the
bag itself: KLT feature tracks on the bag panel -> RANSAC homography per frame -> quad. Detection is only
used as a very weak drift correction, and the result is smoothed forwards and backwards in time.
"""
import json
import numpy as np
import cv2

R = "../real/c{}/{:03d}.jpg"
N = 121
CFG = {  # clip: search box (x0, y0, x1, y1), V min, S max, seed frame (0-based, label clean + fully visible)
    1: ((360, 980, 720, 1380), 150, 45, 0),
    2: ((280, 800, 680, 1220), 150, 45, 0),
    3: ((140, 840, 470, 1180), 95, 50, 50),
    4: ((0, 820, 330, 1250), 150, 45, 0),
}


def gray(n, i):
    return cv2.cvtColor(cv2.imread(R.format(n, i + 1)), cv2.COLOR_BGR2GRAY)


def order(pts):
    pts = np.array(pts, np.float32)
    s, d = pts.sum(1), np.diff(pts, axis=1)[:, 0]
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]], np.float32)


def detect(n, i):
    (x0, y0, x1, y1), vmin, smax, _ = CFG[n]
    im = cv2.imread(R.format(n, i + 1))
    hsv = cv2.cvtColor(im[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 2] > vmin) & (hsv[..., 1] < smax)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    k, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if k < 2:
        return None, None
    j = np.argmax(st[1:, 4]) + 1
    if st[j, 4] < 1500:
        return None, None
    cnts, _ = cv2.findContours((lab == j).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    hull = cv2.convexHull(max(cnts, key=cv2.contourArea))
    approx = cv2.approxPolyDP(hull, 0.04 * cv2.arcLength(hull, True), True).reshape(-1, 2)
    if len(approx) != 4:
        approx = cv2.boxPoints(cv2.minAreaRect(hull))
    q = order(approx) + np.array([x0, y0], np.float32)
    col = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)[y0:y1, x0:x1][lab == j].mean(0)
    return q, col


def panel_mask(shape, q, grow=1.9):
    c = q.mean(0)
    poly = (c + (q - c) * grow).astype(np.int32)
    m = np.zeros(shape, np.uint8)
    cv2.fillConvexPoly(m, poly, 255)
    return m


def step(g0, g1, q):
    """Homography that moves the bag panel from frame g0 to g1."""
    pts = cv2.goodFeaturesToTrack(g0, 300, 0.01, 5, mask=panel_mask(g0.shape, q))
    if pts is None or len(pts) < 8:
        return np.eye(3)
    nxt, ok, _ = cv2.calcOpticalFlowPyrLK(g0, g1, pts, None, winSize=(25, 25), maxLevel=3)
    back, ok2, _ = cv2.calcOpticalFlowPyrLK(g1, g0, nxt, None, winSize=(25, 25), maxLevel=3)
    good = (ok[:, 0] == 1) & (ok2[:, 0] == 1) & (np.linalg.norm(back - pts, axis=2)[:, 0] < 1.0)
    a, b = pts[good], nxt[good]
    if len(a) >= 12:
        Hm, inl = cv2.findHomography(a, b, cv2.RANSAC, 2.0)
        if Hm is not None:
            return Hm
    if len(a) >= 4:
        A, _ = cv2.estimateAffinePartial2D(a, b, method=cv2.RANSAC, ransacReprojThreshold=2.0)
        if A is not None:
            return np.vstack([A, [0, 0, 1]])
    return np.eye(3)


def move(q, Hm):
    return cv2.perspectiveTransform(q.reshape(-1, 1, 2), Hm).reshape(4, 2)


def smooth(arr, sigma=2.0):
    """Zero-phase Gaussian smoothing along time."""
    r = int(3 * sigma)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    flat = arr.reshape(len(arr), -1)
    pad = np.pad(flat, ((r, r), (0, 0)), mode="edge")
    out = np.stack([np.convolve(pad[:, j], k, mode="valid") for j in range(flat.shape[1])], 1)
    return out.reshape(arr.shape)


out = {}
for n, (_, _, _, seed) in CFG.items():
    grays = [gray(n, i) for i in range(N)]
    q_seed, _ = detect(n, seed)
    Q = np.zeros((N, 4, 2), np.float32)
    Q[seed] = q_seed
    for direction in (1, -1):                      # track forwards and backwards from the seed frame
        i = seed
        while 0 <= i + direction < N:
            j = i + direction
            q = move(Q[i], step(grays[i], grays[j], Q[i]))
            dq, _ = detect(n, j)
            if dq is not None:                     # very weak drift correction, only if detection agrees
                if np.abs(dq - q).max() < 12:
                    q = 0.95 * q + 0.05 * dq
            Q[j] = q
            i = j
    # follow the bag's motion, but keep the patch's shape steady (Kling's label itself wobbles)
    ctr = smooth(Q.mean(1, keepdims=True), 1.5)
    shape = smooth(Q - Q.mean(1, keepdims=True), 6.0)
    Q = ctr + shape
    cols = []
    for i in range(N):
        _, c = detect(n, i)
        cols.append(c if c is not None else np.full(3, np.nan))
    C = np.array(cols)
    for j in range(3):
        v = C[:, j]
        ok = ~np.isnan(v)
        C[:, j] = np.interp(np.arange(N), np.where(ok)[0], v[ok])
    C = smooth(C, 6.0)
    w = np.linalg.norm(Q[:, 1] - Q[:, 0], axis=1)
    h = np.linalg.norm(Q[:, 3] - Q[:, 0], axis=1)
    acc = np.abs(np.diff(Q, 2, axis=0)).mean()
    print(f"clip {n}: jitter {acc:.2f} px/f^2, width {w.min():.0f}-{w.max():.0f}, height {h.min():.0f}-{h.max():.0f}")
    out[n] = {"quads": Q.round(2).tolist(), "colors": C.round(1).tolist()}
json.dump(out, open("labels.json", "w"))
