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


def frame(i):
    t = i / FPS
    if t < S1_END:
        arr = SD.scene1(t)
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
    n = int(DUR * FPS)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", "audio.wav", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for k, b in enumerate(pool.imap(frame, range(n), chunksize=4)):
            p.stdin.write(b)
            if k % 60 == 0:
                print(f"{k}/{n}", flush=True)
    p.stdin.close()
    p.wait()
    print("done", out)
