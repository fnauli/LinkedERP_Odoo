"""Find the white address labels on the cartons and blur them (Hoki: addresses must not be readable)."""
import numpy as np, cv2
_SEG = None


def person_mask(rgb):
    """People in the frame (mediapipe selfie segmentation): a scarf or a cap is never a label."""
    global _SEG
    if _SEG is None:
        import mediapipe as mp
        _SEG = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=0)
    m = (_SEG.process(rgb).segmentation_mask > 0.4).astype(np.uint8)
    return cv2.dilate(m, np.ones((9, 9), np.uint8))


def label_mask(rgb, y_min=0.05):
    pm = person_mask(rgb)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    v, s = hsv[..., 2], hsv[..., 1]
    white = ((v > 125) & (s < 50)).astype(np.uint8)
    # labels sit on brown cardboard: keep white blobs with cardboard around them
    card = ((hsv[..., 0] > 8) & (hsv[..., 0] < 28) & (s > 70) & (v > 70)).astype(np.uint8)
    near_card = cv2.dilate(card, np.ones((25, 25), np.uint8))
    white = cv2.morphologyEx(white, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(white)
    h, w = white.shape
    out = np.zeros_like(white)
    for k in range(1, n):
        x, y, bw, bh, area = st[k]
        if area < 0.00015 * h * w or area > 0.035 * h * w or not (0.4 < bw / max(bh, 1) < 3.2):
            continue
        if bw > 0.45 * w or bh > 0.3 * h:
            continue
        comp = lab[y:y + bh, x:x + bw] == k
        ring = near_card[max(0, y - 6):y + bh + 6, max(0, x - 6):x + bw + 6]
        fill = area / (bw * bh)
        if y < y_min * h or ring.mean() < 0.3 or fill < 0.27:
            continue
        if pm[y:y + bh, x:x + bw][comp].mean() > 0.1:
            continue
        box = v[y:y + bh, x:x + bw]
        dark = (box < 130).mean()                 # labels carry printed text and lines; a scarf or a wall does not
        if dark < 0.015 or dark > 0.4 or box.std() < 22:
            continue
        out[y:y + bh, x:x + bw][comp] = 1
        cv2.rectangle(out, (x, y), (x + bw, y + bh), 1, -1)
    return cv2.dilate(out, np.ones((11, 11), np.uint8))


def blur_labels(rgb, y_min=0.05):
    m = label_mask(rgb, y_min)
    if m.sum() == 0:
        return rgb
    small = cv2.resize(rgb, (rgb.shape[1] // 12, rgb.shape[0] // 12), interpolation=cv2.INTER_AREA)
    bl = cv2.GaussianBlur(cv2.resize(small, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_LINEAR), (0, 0), 4)
    mf = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 3)[..., None]
    return (rgb * (1 - mf) + bl * mf).astype(np.uint8)
