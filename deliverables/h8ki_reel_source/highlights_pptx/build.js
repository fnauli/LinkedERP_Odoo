// H8KI Instagram Highlights as an editable PowerPoint for Hoki's team.
// Slide size 11.25" x 20" = exactly 1080 x 1920 px when PowerPoint exports at its default 96 dpi.
// Everything below is laid out in pixels (px / 96 = inches) so it matches highlights.py one to one.
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.SKILL + "/scripts/apply_theme.js");

const OUT = process.argv[2] || "H8KI_Instagram_Highlights_EDITABLE.pptx";
const THEME = {
  name: "H8KI Highlights",
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  colors: {
    dk1: "181C28", lt1: "FFFFFF", dk2: "606874", lt2: "F6F7FA",
    accent1: "E3181E", accent2: "049844", accent3: "291B73", accent4: "FFB400",
    accent5: "966E00", accent6: "FFF3B0", hlink: "291B73", folHlink: "606874",
  },
};
const P = (px) => px / 96;            // px -> inches
const PT = (px) => px * 0.75;         // px font size -> pt

const pres = new pptxgen();
pres.defineLayout({ name: "STORY_9x16", width: 11.25, height: 20 });
pres.layout = "STORY_9x16";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "H8KI Instagram Highlights";
pres.author = "H8KI";
const C = pres.SchemeColor;
const RED = C.accent1, GREEN = C.accent2, INDIGO = C.accent3;

pres.defineSlideMaster({ title: "Cover", background: { color: C.accent1 }, objects: [] });
pres.defineSlideMaster({ title: "Story", background: { color: C.background2 }, objects: [] });

const WA = "[ISI: 08xx-xxxx-xxxx]";
let n = 0;
const name = (s) => `${s}_${++n}`;

// A yellow sticky note to the right of the slide: visible while editing, never in the exported PNG.
function sticky(slide, lines) {
  slide.addText(lines.map((t, i) => ({ text: t.replace(/^\u2022 /, ""),
    options: { breakLine: i < lines.length - 1, bold: i === 0, bullet: t.startsWith("\u2022 ") } })), {
    x: 11.6, y: 0.3, w: 4.4, h: 6, fill: { color: "FFF3B0" }, line: { color: "FFC400", width: 1.5 },
    fontSize: 16, color: "181C28", valign: "top", margin: 0.2, paraSpaceAfter: 6, isTextBox: true,
    objectName: "Catatan (di luar slide, tidak ikut ter-export)",
  });
}

const ICONS = {
  Layanan: { file: "assets/icon_box.png", x: 343, y: 786, w: 393, h: 400, bg: RED },
  Area: { file: "assets/icon_pin.png", x: 390, y: 585, w: 300, h: 555, bg: INDIGO },
  "Cara Order": { file: "assets/icon_chat.png", x: 315, y: 780, w: 450, h: 396, bg: GREEN },
  Testimoni: { file: "assets/icon_star.png", x: 311, y: 720, w: 457, h: 434, bg: RED },
};

function cover(sec) {
  const ic = ICONS[sec];
  const s = pres.addSlide({ masterName: "Cover", sectionTitle: sec });
  s.background = { color: ic.bg };
  s.addImage({ path: ic.file, x: P(ic.x), y: P(ic.y), w: P(ic.w), h: P(ic.h), objectName: name("Ikon"),
    altText: `Ikon highlight ${sec}` });
  sticky(s, [`SAMPUL HIGHLIGHT: ${sec}`, "Siap pakai, tidak perlu diubah.",
    "Export slide ini sebagai PNG, upload sebagai Story, lalu pilih sebagai sampul highlight “" + sec + "”.",
    "Instagram memotong lingkaran dari tengah, jadi ikon sengaja di tengah."]);
  s.addNotes(`Sampul highlight "${sec}". Warna latar bisa diganti lewat Format Background; ikon bisa diganti gambar lain (taruh di tengah slide).`);
}

function header(s, title, kicker, accent) {
  s.addShape(pres.ShapeType.rect, { x: 0, y: 0, w: 11.25, h: P(640), fill: { color: accent }, line: { type: "none" },
    objectName: name("Latar judul") });
  const lw = 300, lh = 300 * 265 / 600, pw = lw + 48, ph = lh + 36;
  s.addShape(pres.ShapeType.roundRect, { x: P(72), y: P(250), w: P(pw), h: P(ph), rectRadius: P(28),
    fill: { color: C.background1 }, line: { type: "none" }, objectName: name("Plat logo") });
  s.addImage({ path: "assets/logo.png", x: P(96), y: P(268), w: P(lw), h: P(lh), objectName: name("Logo H8KI"),
    altText: "Logo H8KI" });
  s.addText(kicker, { x: P(72), y: P(250 + ph + 24), w: P(940), h: P(52), margin: 0, fontSize: PT(34), bold: true,
    color: C.background1, valign: "top", isTextBox: true, objectName: name("Subjudul") });
  s.addText(title, { x: P(72), y: P(250 + ph + 74), w: P(940), h: P(100), margin: 0, fontSize: PT(76), bold: true,
    color: C.background1, valign: "top", isTextBox: true, objectName: name("Judul") });
}

function footer(s) {
  s.addText([{ text: "Order via WhatsApp  " }, { text: WA }], {
    shape: pres.ShapeType.roundRect, x: P(110), y: P(1560), w: P(860), h: P(90), rectRadius: P(45),
    fill: { color: GREEN }, line: { type: "none" }, color: C.background1, fontSize: PT(36), bold: true,
    align: "center", valign: "middle", margin: 0, objectName: name("Tombol WhatsApp"),
  });
}

function card(s, x, y, w, h) {
  s.addShape(pres.ShapeType.roundRect, { x: P(x), y: P(y), w: P(w), h: P(h), rectRadius: P(36),
    fill: { color: C.background1 }, line: { type: "none" },
    shadow: { type: "outer", color: "000000", blur: 14, offset: 6, angle: 90, opacity: 0.18 },
    objectName: name("Kartu") });
}

const CONTENT = {
  Layanan: {
    kicker: "Kurir yang nggak nyerah", accent: RED,
    items: [
      ["[ISI: layanan 1, mis. Reguler]", "[ISI: keterangan & estimasi waktu]"],
      ["[ISI: layanan 2, mis. Same Day]", "[ISI: keterangan & estimasi waktu]"],
      ["[ISI: layanan 3, mis. Kargo]", "[ISI: keterangan singkat]"],
    ],
    note: "Alamat cuma pakai patokan? Kurir kami cari sampai ketemu.",
    todo: ["nama 3 layanan", "keterangan + estimasi waktu tiap layanan", "nomor WhatsApp (tombol hijau)"],
  },
  Area: {
    kicker: "Di mana kami melayani", accent: INDIGO,
    items: [
      ["[ISI: Cabang / kota 1]", "[ISI: alamat cabang atau area layanan]"],
      ["[ISI: Cabang / kota 2]", "[ISI: alamat cabang atau area layanan]"],
      ["[ISI: Cabang / kota 3]", "[ISI: alamat cabang atau area layanan]"],
    ],
    note: "Area Anda belum ada di daftar? Tanya dulu via WhatsApp.",
    todo: ["nama cabang / kota", "alamat atau area layanan tiap cabang", "nomor WhatsApp (tombol hijau)"],
  },
  "Cara Order": {
    kicker: "Mudah, cukup 4 langkah", accent: GREEN,
    items: [
      ["1. Chat WhatsApp kami", "Klik link di bio atau simpan nomor di bawah."],
      ["2. Kirim detail paket", "Alamat pengirim & penerima, isi paket, dan perkiraan berat/ukuran."],
      ["3. [ISI: dijemput / antar ke cabang]", "[ISI: jam jemput / jam buka]"],
      ["4. Bayar & terima nomor resi", "[ISI: cara bayar, mis. transfer / tunai]"],
    ],
    todo: ["langkah 3: dijemput kurir atau antar ke cabang", "jam jemput / jam buka", "cara bayar",
      "nomor WhatsApp (tombol hijau)"],
  },
};

const TODO_HEAD = (sec) => [`YANG PERLU DIISI: ${sec}`, "Ganti semua teks [ISI: ...]:"];
const TODO_TAIL = ["Kalau teks terlalu panjang, persingkat; jangan kecilkan huruf terlalu jauh.",
  "Slide ini tidak boleh di-upload selama masih ada “[ISI”."];

function story(sec, spec) {
  const s = pres.addSlide({ masterName: "Story", sectionTitle: sec });
  header(s, sec, spec.kicker, spec.accent);
  const k = spec.items.length, ch = k <= 3 ? 230 : 190, gap = k <= 3 ? 30 : 22;
  let y = 700;
  spec.items.forEach(([t, b], i) => {
    card(s, 60, y, 960, ch);
    s.addShape(pres.ShapeType.roundRect, { x: P(60), y: P(y), w: P(16), h: P(ch), rectRadius: P(8),
      fill: { color: spec.accent }, line: { type: "none" }, objectName: name("Penanda kartu") });
    s.addText([
      { text: t, options: { bold: true, fontSize: PT(k <= 3 ? 38 : 34), color: C.text1, breakLine: true } },
      { text: b, options: { fontSize: PT(k <= 3 ? 30 : 27), color: C.text2, paraSpaceBefore: 6 } },
    ], { x: P(120), y: P(y + 24), w: P(860), h: P(ch - 48), margin: 0, valign: "middle", fit: "shrink",
      isTextBox: true, objectName: name(`Isi kartu ${i + 1}`) });
    y += ch + gap;
  });
  if (spec.note) {
    s.addText(spec.note, { x: P(60), y: P(y + 4), w: P(960), h: P(56), margin: 0, align: "center", valign: "middle",
      fontSize: PT(30), color: C.text2, isTextBox: true, objectName: name("Catatan bawah") });
  }
  footer(s);
  sticky(s, [...TODO_HEAD(sec), ...spec.todo.map((t) => "• " + t), ...TODO_TAIL]);
  s.addNotes(`Story highlight "${sec}". Isi semua teks [ISI: ...] dengan info resmi Hoki, lalu export sebagai PNG (1080 x 1920).`);
}

function testimoni() {
  const sec = "Testimoni";
  const s = pres.addSlide({ masterName: "Story", sectionTitle: sec });
  header(s, sec, "Kata pelanggan kami", RED);
  card(s, 60, 720, 960, 700);
  s.addText("“", { x: P(110), y: P(690), w: P(200), h: P(300), margin: 0, fontSize: PT(220), bold: true,
    color: RED, valign: "top", isTextBox: true, objectName: name("Tanda kutip") });
  s.addText("[ISI: kutipan pelanggan, 1-3 kalimat, dengan izin pelanggan]", { x: P(120), y: P(930), w: P(840),
    h: P(260), margin: 0, fontSize: PT(40), color: C.text1, valign: "top", fit: "shrink", isTextBox: true,
    objectName: name("Kutipan") });
  s.addText("[ISI: nama & kota pelanggan]", { x: P(120), y: P(1215), w: P(840), h: P(56), margin: 0,
    fontSize: PT(34), bold: true, color: C.text1, valign: "top", isTextBox: true, objectName: name("Nama pelanggan") });
  for (let k = 0; k < 5; k++) {
    s.addShape(pres.ShapeType.star5, { x: P(140 + k * 70 - 22), y: P(1360 - 22), w: P(44), h: P(44),
      fill: { color: C.accent4 }, line: { type: "none" }, objectName: name(`Bintang ${k + 1}`) });
  }
  footer(s);
  sticky(s, ["YANG PERLU DIISI: Testimoni", "Ini template: duplikat slide ini untuk tiap testimoni.",
    "• kutipan asli pelanggan (1-3 kalimat)", "• nama + kota (minta izin dulu)",
    "• jumlah bintang (hapus bintang kalau tidak relevan)", "• nomor WhatsApp (tombol hijau)",
    "Hanya pakai testimoni nyata dan sudah diizinkan pelanggan."]);
  s.addNotes("Template testimoni. Klik kanan slide > Duplicate Slide untuk testimoni berikutnya.");
}

function guide() {
  const s = pres.addSlide({ masterName: "Story", sectionTitle: "Petunjuk" });
  s.background = { color: C.background1 };
  s.addText("PETUNJUK (jangan di-upload)", { x: P(72), y: P(120), w: P(936), h: P(50), margin: 0, fontSize: PT(32),
    bold: true, color: RED, isTextBox: true, objectName: name("Label") });
  s.addText("Cara pakai file ini", { x: P(72), y: P(180), w: P(936), h: P(110), margin: 0, fontSize: PT(76),
    bold: true, color: C.text1, isTextBox: true, objectName: name("Judul") });
  const steps = [
    ["Isi teks [ISI: ...]", "Klik teks di slide lalu ketik info resmi Hoki. Catatan kuning di kanan slide menyebut apa saja yang perlu diisi."],
    ["Nomor WhatsApp sekaligus", "Tekan Ctrl+H (Mac: Cmd+Shift+H), cari [ISI: 08xx-xxxx-xxxx], ganti dengan nomor Hoki, lalu Replace All."],
    ["Cek sebelum export", "Ctrl+F cari “[ISI”. Harus tidak ada lagi yang ditemukan."],
    ["Export jadi gambar", "File > Export > PNG > All Slides. Ukuran slide sudah 1080 x 1920 px. Di Mac, isi Width 1080 dan Height 1920."],
    ["Upload ke Highlight", "Upload sampul + slide sebagai Story, tambahkan ke Highlight, lalu Edit Highlight > Edit Cover pilih gambar sampulnya."],
  ];
  let y = 360;
  steps.forEach(([t, b], i) => {
    s.addShape(pres.ShapeType.ellipse, { x: P(72), y: P(y), w: P(96), h: P(96), fill: { color: [RED, INDIGO, GREEN, RED, INDIGO][i] },
      line: { type: "none" }, objectName: name(`Nomor ${i + 1}`) });
    s.addText(String(i + 1), { x: P(72), y: P(y), w: P(96), h: P(96), margin: 0, align: "center", valign: "middle",
      fontSize: PT(48), bold: true, color: C.background1, isTextBox: true, objectName: name(`Angka ${i + 1}`) });
    s.addText([
      { text: t, options: { bold: true, fontSize: PT(38), color: C.text1, breakLine: true } },
      { text: b, options: { fontSize: PT(29), color: C.text2, paraSpaceBefore: 6 } },
    ], { x: P(200), y: P(y - 8), w: P(808), h: P(220), margin: 0, valign: "top", isTextBox: true,
      objectName: name(`Langkah ${i + 1}`) });
    y += 270;
  });
  s.addText("Urutan upload yang disarankan: Layanan, Area, Cara Order, Testimoni.", { x: P(72), y: P(1720), w: P(936),
    h: P(80), margin: 0, fontSize: PT(28), italic: true, color: C.text2, isTextBox: true, objectName: name("Catatan") });
  s.addNotes("Slide petunjuk untuk tim Hoki. Jangan di-export / di-upload.");
}

pres.addSection({ title: "Petunjuk" });
guide();
for (const sec of ["Layanan", "Area", "Cara Order"]) {
  pres.addSection({ title: sec });
  cover(sec);
  story(sec, CONTENT[sec]);
}
pres.addSection({ title: "Testimoni" });
cover("Testimoni");
testimoni();

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
