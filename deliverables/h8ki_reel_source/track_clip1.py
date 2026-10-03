"""Clip 1: anchor the logo to the label itself (its filled outline), not to bag texture.

The fog leaves little texture on the bag, so feature tracking let the logo slide ~3.5 px against the
label. The label is a bright white rectangle, so its filled-outline centroid and rotated-rectangle fit
are measured every frame (sub-pixel), lightly smoothed for position and strongly for size and angle.
"""
import json, numpy as np, cv2

N = 121
BOX = (360, 980, 720, 1380)


def label_mask(im):
    x0, y0, x1, y1 = BOX
    hsv = cv2.cvtColor(im[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 2] > 150) & (hsv[..., 1] < 45)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    k, lab, st, _ = cv2.connectedComponentsWithStats(m)
    j = np.argmax(st[1:, 4]) + 1
    cnts, _ = cv2.findContours((lab == j).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    filled = np.zeros_like(m)
    cv2.drawContours(filled, [max(cnts, key=cv2.contourArea)], -1, 1, -1)   # fill the fake-letter holes
    full = np.zeros(im.shape[:2], np.uint8)
    full[y0:y1, x0:x1] = filled
    return full


def smooth(x, s):
    if s <= 0:
        return x
    r = int(3 * s) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2)
    k /= k.sum()
    return np.convolve(np.pad(x, r, mode="edge"), k, "valid")


if __name__ == "__main__":
    cx, cy, ww, hh, aa = [], [], [], [], []
    for i in range(N):
        m = label_mask(cv2.imread(f"../real/c1/{i + 1:03d}.jpg"))
        M = cv2.moments(m, binaryImage=True)
        cx.append(M["m10"] / M["m00"]); cy.append(M["m01"] / M["m00"])
        pts = np.column_stack(np.nonzero(m))[:, ::-1].astype(np.float32)
        (rx, ry), (rw, rh), ang = cv2.minAreaRect(pts)
        if rw < rh:                                   # normalise to (width < height, angle near 0)
            rw, rh, ang = rh, rw, ang - 90
        ang = (ang + 45) % 90 - 45
        ww.append(min(rw, rh)); hh.append(max(rw, rh)); aa.append(ang)
    cx, cy = smooth(np.array(cx), 0.8), smooth(np.array(cy), 0.8)
    ww, hh, aa = smooth(np.array(ww), 5), smooth(np.array(hh), 5), smooth(np.array(aa), 5)
    quads = []
    for i in range(N):
        box = cv2.boxPoints(((cx[i], cy[i]), (ww[i], hh[i]), aa[i]))
        s, d = box.sum(1), np.diff(box, axis=1)[:, 0]
        q = np.array([box[np.argmin(s)], box[np.argmin(d)], box[np.argmax(s)], box[np.argmax(d)]])
        quads.append(q.round(2).tolist())
    L = json.load(open("labels.json"))
    L["1"]["quads"] = quads
    json.dump(L, open("labels.json", "w"))
    print("clip 1 width %.0f-%.0f height %.0f-%.0f angle %.1f..%.1f" % (ww.min(), ww.max(), hh.min(), hh.max(), aa.min(), aa.max()))
