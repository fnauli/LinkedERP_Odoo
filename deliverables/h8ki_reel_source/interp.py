"""Motion-compensated in-between frames (bidirectional DIS optical flow), for gentle slow motion."""
import numpy as np, cv2

_dis = None


def _flow(a, b):
    global _dis
    if _dis is None:
        _dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    return _dis.calc(cv2.cvtColor(a, cv2.COLOR_RGB2GRAY), cv2.cvtColor(b, cv2.COLOR_RGB2GRAY), None)


def between(a, b, s):
    """Frame at fraction s (0..1) between RGB frames a and b."""
    if s < 0.02:
        return a
    if s > 0.98:
        return b
    h, w = a.shape[:2]
    fab, fba = _flow(a, b), _flow(b, a)
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    wa = cv2.remap(a, gx - s * fab[..., 0], gy - s * fab[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    wb = cv2.remap(b, gx - (1 - s) * fba[..., 0], gy - (1 - s) * fba[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return (wa.astype(np.float32) * (1 - s) + wb.astype(np.float32) * s).astype(np.uint8)
