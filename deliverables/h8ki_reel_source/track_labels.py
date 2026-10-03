"""Track the plain white bag label in each Kling clip -> per-frame quadrilateral (for the H8KI logo)."""
import numpy as np, cv2, json

R = "../real/c{}/{:03d}.jpg"
CFG = {  # clip: (x0, y0, x1, y1 search box, V min, S max)
    1: (360, 980, 720, 1380, 150, 45),
    2: (280, 800, 680, 1220, 150, 45),
    3: (140, 840, 470, 1180, 95, 50),
    4: (0, 820, 330, 1250, 150, 45),
}


def order(pts):
    pts = np.array(pts, np.float32)
    s, d = pts.sum(1), np.diff(pts, axis=1)[:, 0]
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]], np.float32)


def detect(n, fr):
    x0, y0, x1, y1, vmin, smax = CFG[n]
    im = cv2.imread(R.format(n, fr))
    hsv = cv2.cvtColor(im[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 2] > vmin) & (hsv[..., 1] < smax)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    k, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if k < 2:
        return None, None
    i = np.argmax(st[1:, 4]) + 1
    if st[i, 4] < 1500:
        return None, None
    cnts, _ = cv2.findContours((lab == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    hull = cv2.convexHull(max(cnts, key=cv2.contourArea))
    peri = cv2.arcLength(hull, True)
    approx = cv2.approxPolyDP(hull, 0.04 * peri, True).reshape(-1, 2)
    if len(approx) != 4:
        approx = cv2.boxPoints(cv2.minAreaRect(hull))
    q = order(approx) + np.array([x0, y0], np.float32)
    col = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)[y0:y1, x0:x1][lab == i].mean(0)
    return q, col


out = {}
for n in CFG:
    qs, cols = [], []
    for fr in range(1, 122):
        q, c = detect(n, fr)
        qs.append(q)
        cols.append(c)
    # fill gaps by nearest valid, reject jumps, smooth
    Q = np.array([q if q is not None else np.full((4, 2), np.nan) for q in qs])
    C = np.array([c if c is not None else np.full(3, np.nan) for c in cols])
    area = np.array([cv2.contourArea(q) if q is not None else np.nan for q in qs])
    med = np.nanmedian(area)
    bad = (area < 0.55 * med) | (area > 1.6 * med)
    Q[bad] = np.nan
    C[bad] = np.nan
    for arr in (Q, C):
        flat = arr.reshape(len(arr), -1)
        for j in range(flat.shape[1]):
            v = flat[:, j]
            ok = ~np.isnan(v)
            flat[:, j] = np.interp(np.arange(len(v)), np.where(ok)[0], v[ok])
    k = 7
    pad = np.pad(Q, ((k // 2, k // 2), (0, 0), (0, 0)), mode="edge")
    Qs = np.array([pad[i:i + k].mean(0) for i in range(len(Q))])
    padc = np.pad(C, ((k, k), (0, 0)), mode="edge")
    Cs = np.array([padc[i:i + 2 * k + 1].mean(0) for i in range(len(C))])
    out[n] = {"quads": Qs.round(1).tolist(), "colors": Cs.round(1).tolist(), "bad": int(bad.sum())}
    print("clip", n, "rejected", int(bad.sum()), "median area", int(med))
json.dump(out, open("labels.json", "w"))
