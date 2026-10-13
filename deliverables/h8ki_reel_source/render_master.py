"""Render the final cut once into a near-lossless master (x264 CRF 14, AAC 320k)."""
import os, sys, subprocess
os.environ["REAL"] = "1"; os.environ["V2"] = "1"
from multiprocessing import Pool
import imageio_ffmpeg
import render_v2 as R
from common import W, H, FPS, DUR, HOOK
out = sys.argv[1]
n = int((DUR + HOOK) * FPS)
cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
       "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "audio_v2.wav",
       "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-tune", "film", "-pix_fmt", "yuv420p",
       "-profile:v", "high", "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart", "-shortest", out]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
with Pool(4) as pool:
    for k, b in enumerate(pool.imap(R.frame, range(n), chunksize=4)):
        p.stdin.write(b)
p.stdin.close(); p.wait(); print("master done", out)
