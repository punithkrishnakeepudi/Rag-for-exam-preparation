"""Read the rendered PDF and rewrite the page numbers in the front-matter lists.

Front matter is numbered in lowercase roman starting at iii, because the
acknowledgement (i) and declaration (ii) are added in front of this file
by the student. The body restarts at arabic 1 with Chapter 1.
"""

import re
import pathlib

import fitz

PDF = "AI_Study_Assistant_Using_RAG_Report.pdf"
SRC = pathlib.Path("build_report.py")

d = fitz.open(PDF)
pages = [p.get_text() for p in d]
lines = [[l.strip() for l in t.split("\n")] for t in pages]


def page_of_line(text, start=0):
    for i in range(start, len(lines)):
        if text in lines[i]:
            return i + 1
    return None


def roman(n):
    vals = [(1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"),
            (50, "l"), (40, "xl"), (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
    out = ""
    for v, sym in vals:
        while n >= v:
            out += sym
            n -= v
    return out


# The cover document sits in front of the abstract and carries no page numbers.
# The abstract is the first numbered page and prints iii.
abstract_page = page_of_line("ABSTRACT")
ROMAN_OFFSET = 3 - abstract_page

ch1 = page_of_line("1.  INTRODUCTION")
off = ch1 - 1

CH = [(1, "INTRODUCTION"), (2, "LITERATURE REVIEW"), (3, "METHODOLOGY"),
      (4, "IMPLEMENTATION"), (5, "TESTING & DEPLOYMENT"),
      (6, "RESULTS AND DISCUSSION"), (7, "CONCLUSION AND FUTURE SCOPE")]
starts = {n: page_of_line(f"{n}.  {name}") - off for n, name in CH}
starts["REF"] = page_of_line("REFERENCES", ch1 - 1) - off
order = [1, 2, 3, 4, 5, 6, 7, "REF"]
ends = {a: starts[b] - 1 for a, b in zip(order, order[1:])}
ends["REF"] = len(pages) - off

idx_page = page_of_line("INDEX")
front = {
    "ABSTRACT": page_of_line("ABSTRACT"),
    "LIST OF FIGURES": page_of_line("LIST OF FIGURES", idx_page),
    "LIST OF TABLES": page_of_line("LIST OF TABLES", idx_page),
    "LIST OF ABBREVIATIONS": page_of_line("LIST OF ABBREVIATIONS", idx_page),
}

figs, tabs = {}, {}
for i, t in enumerate(pages):
    for m in re.finditer(r"Figure (\d+\.\d+):", t):
        figs.setdefault(m.group(1), str(i + 1 - off))
    for m in re.finditer(r"Table (\d+\.\d+):", t):
        tabs.setdefault(m.group(1), str(i + 1 - off))

s = SRC.read_text()

names = {1: "INTRODUCTION", 2: "LITERATURE REVIEW", 3: "METHODOLOGY", 4: "IMPLEMENTATION",
         5: "TESTING & DEPLOYMENT", 6: "RESULTS AND DISCUSSION",
         7: "CONCLUSION AND FUTURE SCOPE"}

rows = ['    ["", "ACKNOWLEDGEMENT", "i"],',
        '    ["", "DECLARATION", "ii"],']
for k in ("ABSTRACT", "LIST OF FIGURES", "LIST OF TABLES", "LIST OF ABBREVIATIONS"):
    rows.append(f'    ["", "{k}", "{roman(front[k] + ROMAN_OFFSET)}"],')
for n in range(1, 8):
    span = f"{starts[n]} – {ends[n]}" if ends[n] > starts[n] else f"{starts[n]}"
    rows.append(f'    ["{n}", "{names[n]}", "{span}"],')
ref_span = (f'{starts["REF"]} – {ends["REF"]}' if ends["REF"] > starts["REF"]
            else f'{starts["REF"]}')
rows.append(f'    ["", "REFERENCES", "{ref_span}"],')
s = re.sub(r"INDEX_ROWS = \[.*?\n\]", "INDEX_ROWS = [\n" + "\n".join(rows) + "\n]",
           s, flags=re.S)


def retitle(block, mapping):
    global s
    m = re.search(rf"{block} = \[(.*?)\n\]", s, flags=re.S)
    body = m.group(1)

    def repl(mo):
        label, title = mo.group(1), mo.group(2)
        return f'("{label}", "{title}", "{mapping[label.split()[1]]}")'

    body2 = re.sub(r'\("((?:Figure|Table) [\d.]+)", "([^"]+)", "([^"]*)"\)', repl, body)
    s = s[:m.start(1)] + body2 + s[m.end(1):]


retitle("FIGURES", figs)
retitle("TABLES", tabs)
SRC.write_text(s)
print(f"synced: total={len(pages)} offset={off}")
print("  front:", {k: roman(v + ROMAN_OFFSET) for k, v in front.items()})
print("  chapters:", starts)
print("  ends:", ends)
