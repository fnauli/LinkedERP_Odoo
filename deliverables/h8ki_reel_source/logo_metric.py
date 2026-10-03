import sys, numpy as np, cv2
from label_logo import apply
from track_outline import label_mask
rng = {1: (14, 99), 2: (19, 96), 3: (7, 115), 4: (5, 90)}
for n in map(int, sys.argv[1:]):
    a, b = rng[n]; R = []
    for i in range(a, b):
        bgr = cv2.imread(f"../real/c{n}/{i+1:03d}.jpg")
        m = label_mask(bgr, n)
        if m is None: continue
        o = apply(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), n, i).astype(int)
        ink = (m > 0) & ((np.abs(o[..., 0] - o[..., 1]) > 60))
        ys, xs = np.nonzero(ink); ly, lx = np.nonzero(m)
        lh, lw = ly.max() - ly.min(), lx.max() - lx.min()
        R.append([np.ptp(ys) / lh, np.ptp(xs) / lw, (ys.mean() - ly.min()) / lh, (xs.mean() - lx.min()) / lw])
    R = np.array(R)
    hp = R - cv2.GaussianBlur(R, (1, 0), 0, sigmaY=4) if False else R - np.array([np.convolve(np.pad(R[:, j], 6, mode='edge'), np.ones(13) / 13, 'valid') for j in range(4)]).T
    print(f"clip {n}: logo/label height {R[:,0].min():.3f}-{R[:,0].max():.3f}  width {R[:,1].min():.3f}-{R[:,1].max():.3f}  "
          f"pos y {R[:,2].std()*100:.2f}%  x {R[:,3].std()*100:.2f}%  frame-jitter {np.abs(hp).mean(0).round(4)}")
