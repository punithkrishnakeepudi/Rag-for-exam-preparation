from PIL import Image, ImageDraw, ImageFont

S = 2  # supersample
W, H = 1560*S, 900*S
BG = "white"; INK = "#1f2937"; ACC = "#4f46e5"; MUT = "#6b7280"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
f_title = ImageFont.truetype(FB, 21*S)
f_part  = ImageFont.truetype(FB, 15*S)
f_msg   = ImageFont.truetype(FR, 14*S)
f_note  = ImageFont.truetype(FR, 12*S)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

parts = [
    ("Student\n(Browser UI)", "#e0e7ff"),
    ("FastAPI\nBackend", "#ccfbf1"),
    ("ChromaDB\nVector Store", "#fef3c7"),
    ("LLM Provider\n(chat + embed)", "#fde68a"),
    ("SQLite\nDatabase", "#fef3c7"),
]
n = len(parts)
left, right = 125*S, (W - 125*S)
step = (right - left) // (n - 1)
xs = [left + i*step for i in range(n)]

box_top, box_h, box_w = 70*S, 58*S, 190*S
for x, (label, fill) in zip(xs, parts):
    d.rounded_rectangle([x-box_w//2, box_top, x+box_w//2, box_top+box_h], radius=8*S,
                        fill=fill, outline=INK, width=2*S)
    lines = label.split("\n")
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=f_part)
        d.text((x-tw/2, box_top+11*S + i*19*S), ln, font=f_part, fill=INK)

life_top = box_top + box_h
life_bot = H - 40*S
for x in xs:
    y = life_top
    while y < life_bot:
        d.line([x, y, x, min(y+8*S, life_bot)], fill=MUT, width=2*S)
        y += 14*S

def arrow(y, a, b, text, dashed=False, back=False):
    x1, x2 = xs[a], xs[b]
    col = MUT if back else ACC
    if dashed:
        step_ = 10*S; x = min(x1, x2)
        while x < max(x1, x2):
            d.line([x, y, min(x+6*S, max(x1,x2)), y], fill=col, width=2*S); x += step_
    else:
        d.line([x1, y, x2, y], fill=col, width=3*S)
    hs = 9*S
    if x2 > x1:
        d.polygon([(x2, y), (x2-hs, y-hs//2), (x2-hs, y+hs//2)], fill=col)
    else:
        d.polygon([(x2, y), (x2+hs, y-hs//2), (x2+hs, y+hs//2)], fill=col)
    tw = d.textlength(text, font=f_msg)
    cx = (x1+x2)/2
    d.rectangle([cx-tw/2-4*S, y-22*S, cx+tw/2+4*S, y-4*S], fill=BG)
    d.text((cx-tw/2, y-20*S), text, font=f_msg, fill=INK)

def selfloop(y, a, text):
    x = xs[a]; w = 52*S
    d.line([x, y, x+w, y], fill=ACC, width=3*S)
    d.line([x+w, y, x+w, y+26*S], fill=ACC, width=3*S)
    d.line([x+w, y+26*S, x, y+26*S], fill=ACC, width=3*S)
    hs = 9*S
    d.polygon([(x, y+26*S), (x+hs, y+26*S-hs//2), (x+hs, y+26*S+hs//2)], fill=ACC)
    d.text((x+w+10*S, y+6*S), text, font=f_msg, fill=INK)

title = "Sequence of a Retrieval-Augmented Chat Request"
tw = d.textlength(title, font=f_title)
d.text(((W-tw)/2, 22*S), title, font=f_title, fill=INK)

y = life_top + 46*S; dy = 52*S
arrow(y, 0, 1, "1.  POST /api/notebooks/{id}/chat  {question, history}"); y += dy
arrow(y, 1, 3, "2.  embed(question)"); y += dy
arrow(y, 3, 1, "3.  query vector (1536-dim)", back=True, dashed=True); y += dy
arrow(y, 1, 2, "4.  similarity query, n_results = 3"); y += dy
arrow(y, 2, 1, "5.  top-3 chunks + metadata", back=True, dashed=True); y += dy
arrow(y, 1, 0, "6.  SSE event  { type: 'sources' }", back=True); y += dy
selfloop(y, 1, "7.  build prompt: system + context + last 4 turns + question"); y += 66*S
arrow(y, 1, 3, "8.  chat completion request  (stream = true)"); y += dy
arrow(y, 3, 1, "9.  token deltas  (repeated)", back=True, dashed=True); y += dy
arrow(y, 1, 0, "10.  SSE events  { type: 'token' }  x N", back=True); y += dy
arrow(y, 1, 0, "11.  SSE event  { type: 'done' }", back=True); y += dy
arrow(y, 0, 1, "12.  POST /messages  (user turn, then assistant turn)"); y += dy
arrow(y, 1, 4, "13.  INSERT message rows"); y += dy

img = img.resize((W//S, H//S), Image.LANCZOS)
img.save("fig_sequence.png", dpi=(170,170))
print("saved", img.size)
