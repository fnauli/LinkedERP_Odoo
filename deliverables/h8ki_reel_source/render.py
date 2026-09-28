"""Render all frames and mux with the soundtrack."""
import subprocess, sys, math
import numpy as np
from multiprocessing import Pool
from PIL import Image
import imageio_ffmpeg
from common import *
from gfx import to_img, to_arr, draw_text, font
import scene_digital as SD
import scene_night as SN
import scene_house as SH


def zoom(img, z, fy=0.5):
    """Camera push: crop around centre and scale back up."""
    if z <= 1.001:
        return img
    cw, ch = W / z, H / z
    x0, y0 = (W - cw) / 2, (H - ch) * fy
    return img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BICUBIC)


def frame(i):
    hf = int(HOOK * FPS)
    if i < hf:
        th = i / FPS
        return np.asarray(zoom(to_img(SD.hook(th)), 1.06 - 0.06 * ease_out(th / HOOK)), np.uint8).tobytes()
    t = (i - hf) / FPS
    if t < S1_END:
        return np.asarray(zoom(to_img(SD.scene1(t)), 1 + 0.035 * ease_io(t / S1_END)), np.uint8).tobytes()
    elif t < NIGHT_START:
        arr = SD.scene2(t)
    elif t < S3_END:
        arr = SN.scene3(t)
        if t < NIGHT_START + 0.7:
            # the black screen gains depth: stars bloom in, "GPS menyerah." fades away
            p = ease_io(lin(t, NIGHT_START, NIGHT_START + 0.7))
            arr = arr * p
            if p < 1:
                img = to_img(arr)
                txt = SD.scene2(NIGHT_START - 0.01)
                arr = np.maximum(to_arr(img), txt * (1 - p))
        img = to_img(arr)
        return np.asarray(img, np.uint8).tobytes()
    elif t < S4_END:
        return np.asarray(SH.scene4(t), np.uint8).tobytes()
    else:
        return np.asarray(SH.scene5(t), np.uint8).tobytes()
    return np.asarray(to_img(arr), np.uint8).tobytes()


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "reel.mp4"
    n = int((DUR + HOOK) * FPS)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", "audio.wav", "-c:v", "libx264", "-preset", "slow", "-b:v", "6.5M", "-maxrate", "8M", "-bufsize", "14M", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for k, b in enumerate(pool.imap(frame, range(n), chunksize=4)):
            p.stdin.write(b)
            if k % 60 == 0:
                print(f"{k}/{n}", flush=True)
    p.stdin.close()
    p.wait()
    print("done", out)
