"""H8KI Instagram Story Highlights: 4 covers + story slides (1080x1920), in the brand colours.

Slides are driven by the CONTENT dict below. Anything Hoki still has to confirm is written as [ISI: ...]
and drawn inside a yellow dashed box, so a draft can never be mistaken for a final slide.
  python3 highlights.py OUTDIR
"""
import sys, os, re, math
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from gfx import font

RED = (227, 24, 30); GREEN = (4, 152, 68); INDIGO = (41, 27, 115); INK = (24, 28, 40)
GREY = (96, 104, 116); BG = (246, 247, 250); WHITE = (255, 255, 255); YEL = (255, 196, 0)
W, H = 1080, 1920
OUT = sys.argv[1] if len(sys.argv) > 1 else "highlights"
os.makedirs(OUT, exist_ok=True)


def logo(width):
    im = np.asarray(Image.open(os.path.join(os.path.dirname(__file__), "logo.jpg")).convert("RGB"), np.float32)
    dist = np.max(np.abs(im - 247.0), axis=2)
    a = np.clip((dist - 6) / 40, 0, 1)
    col = np.clip((im - 247 * (1 - a[..., None])) / np.maximum(a[..., None], 1e-3), 0, 255)
    lg = Image.fromarray(np.dstack([col, a * 255]).astype(np.uint8), "RGBA")
    lg = lg.crop(lg.getbbox())
    return lg.resize((width, int(lg.height * width / lg.width)), Image.LANCZOS)


# ------------------------------------------------------------------ icons (drawn at 4x, white on colour)
def icon_box(d, cx, cy, s, c):
    w = s
    top = [(cx, cy - 0.55 * w), (cx + 0.62 * w, cy - 0.25 * w), (cx, cy + 0.05 * w), (cx - 0.62 * w, cy - 0.25 * w)]
    left = [(cx - 0.62 * w, cy - 0.25 * w), (cx, cy + 0.05 * w), (cx, cy + 0.72 * w), (cx - 0.62 * w, cy + 0.42 * w)]
    right = [(cx + 0.62 * w, cy - 0.25 * w), (cx, cy + 0.05 * w), (cx, cy + 0.72 * w), (cx + 0.62 * w, cy + 0.42 * w)]
    lw = int(0.07 * w)
    for poly in (top, left, right):
        d.line(poly + [poly[0]], fill=c, width=lw, joint="curve")
    d.line([(cx - 0.31 * w, cy - 0.40 * w), (cx + 0.31 * w, cy - 0.10 * w)], fill=c, width=lw)   # tape


def icon_pin(d, cx, cy, s, c):
    r = 0.5 * s
    d.ellipse((cx - r, cy - 0.75 * s - r, cx + r, cy - 0.75 * s + r), fill=c)
    d.polygon([(cx - 0.43 * s, cy - 0.5 * s), (cx + 0.43 * s, cy - 0.5 * s), (cx, cy + 0.6 * s)], fill=c)
    hr = 0.2 * s
    return (cx - hr, cy - 0.75 * s - hr, cx + hr, cy - 0.75 * s + hr)


def icon_chat(d, cx, cy, s, c, bg):
    d.rounded_rectangle((cx - 0.75 * s, cy - 0.6 * s, cx + 0.75 * s, cy + 0.4 * s), radius=int(0.3 * s), fill=c)
    d.polygon([(cx - 0.45 * s, cy + 0.3 * s), (cx - 0.2 * s, cy + 0.3 * s), (cx - 0.55 * s, cy + 0.72 * s)], fill=c)
    for k in (-1, 0, 1):
        r = 0.1 * s
        d.ellipse((cx + k * 0.38 * s - r, cy - 0.1 * s - r, cx + k * 0.38 * s + r, cy - 0.1 * s + r), fill=bg)


def icon_star(d, cx, cy, s, c):
    pts = []
    for k in range(10):
        r = s * (0.8 if k % 2 == 0 else 0.34)
        a = -math.pi / 2 + k * math.pi / 5
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=c)


def cover(name, draw_icon, bg):
    """1080x1920 story image; Instagram's highlight circle crops the centre, so the icon sits there."""
    S = 4
    big = Image.new("RGB", (W * S // 2, H * S // 2), bg)
    d = ImageDraw.Draw(big)
    cx, cy, s = big.width / 2, big.height / 2, 300 * S / 2
    hole = draw_icon(d, cx, cy, s)
    if hole:
        d.ellipse(hole, fill=bg)
    im = big.resize((W, H), Image.LANCZOS)
    im.save(os.path.join(OUT, f"COVER_{name}.png"))
    sq = im.crop((0, (H - W) // 2, W, (H + W) // 2))            # square version, same centre
    sq.save(os.path.join(OUT, f"COVER_{name}_square.png"))
    return sq


# ------------------------------------------------------------------ slide helpers
def wrap(text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if f.getlength(t) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def text_block(d, x, y, text, f, fill, maxw, lh, placeholder_ok=True):
    """Draw wrapped text; [ISI: ...] parts are drawn in a yellow dashed box. Returns the new y."""
    if "[ISI" in text and placeholder_ok:
        lines = wrap(text, f, maxw - 24)
        hgt = lh * len(lines) + 20
        dash_box(d, (x - 12, y - 8, x + maxw + 12, y + hgt))
        for ln in lines:
            d.text((x, y), ln, font=f, fill=(150, 110, 0)); y += lh
        return y + 26
    for ln in wrap(text, f, maxw):
        d.text((x, y), ln, font=f, fill=fill); y += lh
    return y


def dash_box(d, box):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(255, 248, 214))
    for x in range(int(x0), int(x1), 22):
        d.line([(x, y0), (min(x + 12, x1), y0)], fill=YEL, width=4); d.line([(x, y1), (min(x + 12, x1), y1)], fill=YEL, width=4)
    for y in range(int(y0), int(y1), 22):
        d.line([(x0, y), (x0, min(y + 12, y1))], fill=YEL, width=4); d.line([(x1, y), (x1, min(y + 12, y1))], fill=YEL, width=4)


def card(img, box, r=36):
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).rounded_rectangle((box[0], box[1] + 10, box[2], box[3] + 10), r, fill=60)
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    img.paste((0, 0, 0), (0, 0), sh)
    ImageDraw.Draw(img).rounded_rectangle(box, r, fill=WHITE)


def base(title, kicker, accent):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 640), fill=accent)                      # colour header band
    lg = logo(300)
    plate = Image.new("RGBA", (lg.width + 48, lg.height + 36), (255, 255, 255, 255))
    pm = Image.new("L", plate.size, 0); ImageDraw.Draw(pm).rounded_rectangle((0, 0, *plate.size), 28, fill=255)
    img.paste(plate, (72, 250), pm)
    img.paste(lg, (96, 268), lg)
    d.text((72, 250 + plate.height + 34), kicker, font=font("sb", 34), fill=(255, 255, 255))
    d.text((72, 250 + plate.height + 80), title, font=font("xb", 76), fill=WHITE)
    return img, d


def footer(d, wa):
    f = font("sb", 36)
    txt = f"Order via WhatsApp  {wa}"
    tw = f.getlength(txt)
    x0 = (W - tw) / 2 - 40
    d.rounded_rectangle((x0, 1560, x0 + tw + 80, 1650), 45, fill=GREEN)
    d.text((W / 2, 1605), txt, font=f, fill=WHITE, anchor="mm")


# ------------------------------------------------------------------ content (Hoki to confirm every [ISI: ...])
WA = "[ISI: 08xx-xxxx-xxxx]"
CONTENT = {
    "Layanan": {
        "kicker": "Kurir yang nggak nyerah", "accent": RED,
        "items": [
            ("[ISI: layanan 1, mis. Reguler]", "[ISI: keterangan & estimasi waktu]"),
            ("[ISI: layanan 2, mis. Same Day]", "[ISI: keterangan & estimasi waktu]"),
            ("[ISI: layanan 3, mis. Kargo]", "[ISI: keterangan singkat]"),
        ],
        "note": "Alamat cuma pakai patokan? Kurir kami cari sampai ketemu.",
    },
    "Area": {
        "kicker": "Di mana kami melayani", "accent": INDIGO,
        "items": [
            ("[ISI: Cabang / kota 1]", "[ISI: alamat cabang atau area layanan]"),
            ("[ISI: Cabang / kota 2]", "[ISI: alamat cabang atau area layanan]"),
            ("[ISI: Cabang / kota 3]", "[ISI: alamat cabang atau area layanan]"),
        ],
        "note": "Area Anda belum ada di daftar? Tanya dulu via WhatsApp.",
    },
    "Cara Order": {
        "kicker": "Mudah, cukup 4 langkah", "accent": GREEN,
        "items": [
            ("1. Chat WhatsApp kami", "Klik link di bio atau simpan nomor di bawah."),
            ("2. Kirim detail paket", "Alamat pengirim & penerima, isi paket, dan perkiraan berat/ukuran."),
            ("3. [ISI: dijemput / antar ke cabang]", "[ISI: jam jemput / jam buka]"),
            ("4. Bayar & terima nomor resi", "[ISI: cara bayar, mis. transfer / tunai]"),
        ],
    },
}


def slide(name, spec):
    img, d = base(name, spec["kicker"], spec["accent"])
    y = 700
    n = len(spec["items"])
    big = n <= 3
    ft, fb = font("b", 38 if big else 34), font("m", 30 if big else 27)
    lt, lb = (52, 42) if big else (46, 37)
    for title, body in spec["items"]:
        tl = wrap(title, ft, 800); bl = wrap(body, fb, 800)
        hgt = lt * len(tl) + lb * len(bl) + 60 + (34 if "[ISI" in title else 0) + (34 if "[ISI" in body else 0)
        card(img, (60, y, W - 60, y + hgt))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((60, y, 76, y + hgt), 8, fill=spec["accent"])
        yy = text_block(d, 120, y + 28, title, ft, INK, 840, lt)
        text_block(d, 120, yy + 4, body, fb, GREY, 840, lb)
        y += hgt + 24
    if spec.get("note"):
        d.text((W / 2, y + 30), spec["note"], font=font("m", 30), fill=GREY, anchor="mm")
    footer(d, WA)
    assert y < 1540, f"{name}: content runs into the footer ({y})"
    img.save(os.path.join(OUT, f"SLIDE_{name.replace(' ', '_')}.png"))
    return img


def testimoni_template():
    img, d = base("Testimoni", "Kata pelanggan kami", RED)
    card(img, (60, 720, W - 60, 1420))
    d = ImageDraw.Draw(img)
    d.text((110, 700), "“", font=font("xb", 200), fill=RED)
    text_block(d, 120, 960, "[ISI: kutipan pelanggan, 1-3 kalimat, dengan izin pelanggan]", font("m", 40), INK, 840, 56)
    text_block(d, 120, 1220, "[ISI: nama & kota pelanggan]", font("b", 34), INK, 840, 46)
    for k in range(5):
        icon_star(d, 140 + k * 70, 1360, 26, (255, 180, 0))
    footer(d, WA)
    img.save(os.path.join(OUT, "SLIDE_Testimoni_template.png"))
    return img


if __name__ == "__main__":
    covers = [cover("Layanan", lambda d, x, y, s: icon_box(d, x, y, s, WHITE), RED),
              cover("Area", lambda d, x, y, s: icon_pin(d, x, y, s, WHITE), INDIGO),
              cover("Cara_Order", lambda d, x, y, s: icon_chat(d, x, y, s, WHITE, GREEN), GREEN),
              cover("Testimoni", lambda d, x, y, s: icon_star(d, x, y, s, WHITE), RED)]
    slides = [slide(n, s) for n, s in CONTENT.items()] + [testimoni_template()]
    # preview: how the circles look on a profile, and the slides side by side
    pv = Image.new("RGB", (4 * 260 + 40, 300), WHITE); pd = ImageDraw.Draw(pv)
    for k, (c, lab) in enumerate(zip(covers, ["Layanan", "Area", "Cara Order", "Testimoni"])):
        m = Image.new("L", (200, 200), 0); ImageDraw.Draw(m).ellipse((0, 0, 199, 199), fill=255)
        x = 40 + k * 260
        pd.ellipse((x - 6, 14, x + 206, 226), outline=(200, 200, 205), width=3)
        pv.paste(c.resize((200, 200), Image.LANCZOS), (x, 20), m)
        pd.text((x + 100, 260), lab, font=font("m", 26), fill=INK, anchor="mm")
    pv.save(os.path.join(OUT, "preview_profile_circles.png"))
    sp = Image.new("RGB", (4 * 360, 640), WHITE)
    for k, s in enumerate(slides):
        sp.paste(s.resize((360, 640), Image.LANCZOS), (k * 360, 0))
    sp.save(os.path.join(OUT, "preview_slides.png"))
    print("ok")
