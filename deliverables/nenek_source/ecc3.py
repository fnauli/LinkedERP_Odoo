"""Lock shot 3's label: frame-to-frame ECC homography on a cropped ROI (label + bag ring), chained."""
import json, numpy as np, cv2
Q = np.array(json.load(open("../k1/shot3_quads.json")), np.float32)
def gray(i):
    return cv2.GaussianBlur(cv2.cvtColor(cv2.imread(f"../k1/f{i:04d}.png"), cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.0)
q0 = Q[0]
Hc = np.eye(3, dtype=np.float32)
Hs, cc = [Hc.copy()], [1.0]
crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-5)
prev = gray(144)
for i in range(145, 216):
    cur = gray(i)
    qp = cv2.perspectiveTransform(q0[None], Hc)[0]
    c = qp.mean(0)
    ring = c + (qp - c) * 1.4
    x, y, w, h = cv2.boundingRect(ring.astype(np.int32))
    pad = 60
    X0, Y0 = max(0, x - pad), max(0, y - pad)
    X1, Y1 = min(1080, x + w + pad), min(1916, y + h + pad)
    a = prev[Y0:Y1, X0:X1]; b = cur[Y0:Y1, X0:X1]
    m = np.zeros(a.shape, np.uint8)
    cv2.fillConvexPoly(m, (ring - [X0, Y0]).astype(np.int32), 255)
    dH = np.eye(3, dtype=np.float32)
    try:
        r, dH = cv2.findTransformECC(a, b, dH, cv2.MOTION_HOMOGRAPHY, crit, m, 5)
    except cv2.error:
        r = -1
        dH = np.eye(3, dtype=np.float32)
    T = np.array([[1, 0, X0], [0, 1, Y0], [0, 0, 1]], np.float32)
    dHf = T @ dH @ np.linalg.inv(T)                 # ROI coords -> full-frame coords
    Hc = (dHf @ Hc); Hc /= Hc[2, 2]
    Hs.append(Hc.astype(np.float32).copy()); cc.append(float(r)); prev = cur
quads = [cv2.perspectiveTransform(q0[None], H)[0].tolist() for H in Hs]
json.dump({"H": [H.tolist() for H in Hs], "quads": quads, "cc": cc}, open("shot3_ecc.json", "w"))
print("min cc", round(min(cc), 3), [round(v, 2) for v in cc])
