"""Small markdown -> styled docx converter for the H8KI guides.
Supports: '# Title' + subtitle line, '## Heading', tables, ``` code blocks, '- [ ]' checklists, '- ' bullets,
'1. ' numbered items, and **bold**, *italic*, `code` inside text.
  python3 md2docx.py IN.md OUT.docx"""
import re, sys
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

RED = RGBColor(0xD6, 0x1E, 0x2C); NAVY = RGBColor(0x1F, 0x2A, 0x44); GREY = RGBColor(0x5A, 0x63, 0x70)
src, out = sys.argv[1], sys.argv[2]
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.0)
sec.top_margin = sec.bottom_margin = Cm(1.8)
st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
st.paragraph_format.space_after = Pt(4); st.paragraph_format.line_spacing = 1.15
for name, size, color in (("Title", 22, NAVY), ("Heading 1", 15, NAVY)):
    s = doc.styles[name]; s.font.name = "Calibri"; s.font.size = Pt(size); s.font.bold = True; s.font.color.rgb = color


def shade(el, hexcolor):
    pr = el.get_or_add_tcPr() if hasattr(el, "get_or_add_tcPr") else el.get_or_add_pPr()
    sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hexcolor)
    pr.append(sh)


TOK = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)")


def runs(p, text, size=None, color=None, bold=False):
    for part in TOK.split(text):
        if not part:
            continue
        if part.startswith("**"):
            r = p.add_run(part[2:-2]); r.bold = True
        elif part.startswith("`"):
            r = p.add_run(part[1:-1]); r.font.name = "Consolas"
            r._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "Consolas")
            r.font.color.rgb = RGBColor(0x8A, 0x1C, 0x24)
        elif part.startswith("*") and len(part) > 2:
            r = p.add_run(part[1:-1]); r.italic = True
        else:
            r = p.add_run(part)
        if bold:
            r.bold = True
        if size:
            r.font.size = Pt(size)
        if color is not None and not part.startswith("`"):
            r.font.color.rgb = color


lines = open(src, encoding="utf-8").read().split("\n")
i = 0
while i < len(lines):
    ln = lines[i]
    if ln.startswith("# "):
        p = doc.add_paragraph(style="Title"); runs(p, ln[2:]); i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i < len(lines):
            p = doc.add_paragraph(); runs(p, lines[i], size=9.5, color=GREY); i += 1
        continue
    if ln.startswith("## "):
        p = doc.add_paragraph(style="Heading 1"); runs(p, ln[3:]); p.paragraph_format.space_before = Pt(14); i += 1
        continue
    if ln.startswith("```"):
        i += 1; block = []
        while not lines[i].startswith("```"):
            block.append(lines[i]); i += 1
        i += 1
        p = doc.add_paragraph(); shade(p._p, "F3F4F6")
        p.paragraph_format.left_indent = Cm(0.3)
        for k, b in enumerate(block):
            r = p.add_run(b); r.font.size = Pt(10)
            if k < len(block) - 1:
                r.add_break()
        continue
    if ln.startswith("| "):
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                rows.append(cells)
            i += 1
        t = doc.add_table(rows=len(rows), cols=len(rows[0])); t.style = "Table Grid"
        for r_, row in enumerate(rows):
            for c_, cell in enumerate(row):
                cl = t.cell(r_, c_); cl.text = ""
                runs(cl.paragraphs[0], cell, size=10, bold=(r_ == 0))
                if r_ == 0:
                    shade(cl._tc, "1F2A44")
                    for r in cl.paragraphs[0].runs:
                        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        doc.add_paragraph()
        continue
    m = re.match(r"^- \[ \] (.*)", ln)
    if m:
        p = doc.add_paragraph(); runs(p, "☐  " + m.group(1)); p.paragraph_format.left_indent = Cm(0.4); i += 1
        continue
    m = re.match(r"^- (.*)", ln)
    if m:
        p = doc.add_paragraph(style="List Bullet"); runs(p, m.group(1)); i += 1
        continue
    m = re.match(r"^(\d+)\. (.*)", ln)
    if m:
        p = doc.add_paragraph(); runs(p, f"{m.group(1)}.  " + m.group(2)); p.paragraph_format.left_indent = Cm(0.4)
        i += 1
        continue
    if ln.strip():
        p = doc.add_paragraph(); runs(p, ln)
    i += 1
doc.save(out)
print("saved", out)
