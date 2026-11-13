"""Prepare a phone clip: stabilise (smooth the hand shake, keep the pans), blur the address labels,
upscale 720x1280 -> 1080x1920 with a light sharpen, and grade the flat overcast footage.
  python3 prep.py IN.mov OUTDIR [Y_MIN|none]"""
import sys, os
import numpy as np, cv2
from labels import label_mask, person_mask

src, out = sys.argv[1], sys.argv[2]
YMIN = sys.argv[3] if len(sys.argv) > 3 else "0.05"
os.makedirs(out, exist_ok=True)
cap = cv2.VideoCapture(src)
frames = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    frames.append(f)
n = len(frames)
# --- stabilisation: per-frame similarity transform, smoothed trajectory
traj = [np.zeros(3)]
prev = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
for i in range(1, n):
    cur = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
    p0 = cv2.goodFeaturesToTrack(prev, 300, 0.01, 20)
    dx = dy = da = 0.0
    if p0 is not None:
        p1, stt, _ = cv2.calcOpticalFlowPyrLK(prev, cur, p0, None)
        g = stt.ravel() == 1
        if g.sum() > 10:
            M, _ = cv2.estimateAffinePartial2D(p0[g], p1[g])
            if M is not None:
                dx, dy, da = M[0, 2], M[1, 2], np.arctan2(M[1, 0], M[0, 0])
    traj.append(traj[-1] + [dx, dy, da])
    prev = cur
traj = np.array(traj)
k = 21
pad = np.pad(traj, ((k // 2, k // 2), (0, 0)), mode="edge")
smooth = np.stack([np.convolve(pad[:, j], np.ones(k) / k, mode="valid") for j in range(3)], 1)
corr = smooth - traj
H, W = frames[0].shape[:2]
ZOOM = 1.08
stab = []
for i, f in enumerate(frames):
    dx, dy, da = corr[i]
    M = cv2.getRotationMatrix2D((W / 2, H / 2), np.degrees(da), ZOOM)
    M[:, 2] += [dx * ZOOM, dy * ZOOM]
    stab.append(cv2.cvtColor(cv2.warpAffine(f, M, (W, H), borderMode=cv2.BORDER_REFLECT), cv2.COLOR_BGR2RGB))
# --- address labels: detect per frame, then take the union over +-4 frames so a label missed in one frame stays hidden
if YMIN != "none":
    masks = [label_mask(r, float(YMIN)) for r in stab]
    people = [person_mask(r) for r in stab]
    R = 4
else:
    masks = None
for i, rgb in enumerate(stab):
    if masks is not None:
        m = np.max(np.stack(masks[max(0, i - R):i + R + 1]), 0) * (1 - people[i])   # never blur a face or a hand
        if m.any():
            small = cv2.resize(rgb, (W // 12, H // 12), interpolation=cv2.INTER_AREA)
            bl = cv2.GaussianBlur(cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR), (0, 0), 4)
            mf = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 3)[..., None]
            rgb = (rgb * (1 - mf) + bl * mf).astype(np.uint8)
    up = cv2.resize(rgb, (1080, 1920), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    bl = cv2.GaussianBlur(up, (0, 0), 2.0)
    up = up + 0.6 * (up - bl)                                   # light sharpen after the upscale
    x = np.clip(up / 255, 0, 1)
    x = x * np.array([1.04, 1.0, 0.94], np.float32)               # a little warmth
    x = np.clip(x, 0, 1)
    x = x + 0.10 * (x - 0.5) * (1 - np.abs(2 * x - 1))            # contrast S-curve
    lum = x.mean(2, keepdims=True)
    x = lum + (x - lum) * 1.15                                    # a touch more colour
    cv2.imwrite(os.path.join(out, f"f{i + 1:04d}.jpg"), cv2.cvtColor((np.clip(x, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 95])
print(src, n, "frames")
