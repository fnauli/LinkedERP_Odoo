"""'Kiriman untuk Nenek' v4 = v2 cut (no flash-forward) with the bag as Kling filmed it in shot 3:
the printed-in logo patch (label3) is left out, because it read as pasted on.
  python3 render_nenek_v4.py OUT.mp4"""
import sys, subprocess
from multiprocessing import Pool
import imageio_ffmpeg
import render_nenek as R

R.label3.apply = lambda a, p: a          # shot 3: keep the original bag label

if __name__ == "__main__":
    out = sys.argv[1]
    n = int(R.DUR * R.FPS)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    master = out + ".master.mp4"
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{R.W}x{R.H}",
           "-r", str(R.FPS), "-i", "-", "-i", "audio_nenek.wav", "-c:v", "libx264", "-preset", "slow", "-crf", "14",
           "-tune", "film", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", "-shortest", master]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for b in pool.imap(R.frame_bytes, range(n), chunksize=6):
            p.stdin.write(b)
    p.stdin.close(); p.wait()
    for ps in (1, 2):
        c = [ff, "-v", "error", "-y", "-i", master, "-c:v", "libx264", "-preset", "veryslow", "-b:v", "7000k",
             "-maxrate", "9000k", "-bufsize", "14000k", "-pix_fmt", "yuv420p", "-pass", str(ps), "-passlogfile", out + ".p2"]
        c += (["-an", "-f", "mp4", "/dev/null"] if ps == 1 else
              ["-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out])
        subprocess.run(c, check=True)
    print("done", out)
