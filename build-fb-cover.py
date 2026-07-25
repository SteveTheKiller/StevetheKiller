import re, base64, math, os
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

HERE = r"C:\Users\steve\Steve-the-Killer"
SVG  = os.path.join(HERE, "header.svg")
TTF  = os.path.join(HERE, "_killerscan.ttf")
OUT  = os.path.join(HERE, "fb-cover.png")

svg = open(SVG, "r", encoding="utf-8", errors="ignore").read()
m = re.search(r"data:font/truetype;base64,([A-Za-z0-9+/=]+)", svg)
open(TTF, "wb").write(base64.b64decode(m.group(1)))

SS = 2
W, H = 1702 * SS, 630 * SS
BG=(13,13,13); DARKRED=(139,0,0); WAVE2=(90,0,0); LITRED=(255,57,57)
ACCENT=(204,0,0); SHADOW=(58,0,0); WHITE=(255,255,255); GRAY=(183,183,183)

def font(px): return ImageFont.truetype(TTF, int(px))

def seg_w(text, f, ls):
    if not text: return 0
    w = sum(f.getlength(c) + ls for c in text)
    return w - ls

def draw_seg(dr, x, baseline, text, f, ls, fill):
    asc, desc = f.getmetrics()
    for c in text:
        dr.text((x, baseline - asc), c, font=f, fill=fill)
        x += f.getlength(c) + ls
    return x

def centered(dr, cx, baseline, text, f, ls, fill):
    x = cx - seg_w(text, f, ls) / 2
    draw_seg(dr, x, baseline, text, f, ls, fill)

# --- base canvas ---
base = Image.new("RGBA", (W, H), BG + (255,))

# --- red waves along the bottom ---
def wave(color, base_y, amp, wl, phase, alpha):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    pts = []
    step = 6
    for x in range(0, W + step, step):
        y = base_y + amp * math.sin(2 * math.pi * (x / wl) + phase)
        pts.append((x, y))
    pts += [(W, H), (0, H)]
    d.polygon(pts, fill=color + (int(alpha * 255),))
    base.alpha_composite(lay)

wave(WAVE2,   int(H * 0.90), 20 * SS, W * 0.62, 1.1, 0.90)
wave(DARKRED, int(H * 0.93), 26 * SS, W * 0.85, 0.0, 0.95)

# --- vignette (radial darken at edges) ---
vw, vh = 440, 163
vmask = Image.new("L", (vw, vh), 0)
px = vmask.load()
cx, cy = vw * 0.5, vh * 0.42
maxd = math.hypot(max(cx, vw - cx), max(cy, vh - cy))
for y in range(vh):
    for x in range(vw):
        d = math.hypot(x - cx, y - cy) / maxd
        t = max(0.0, (d - 0.52) / 0.48)
        px[x, y] = int(min(1.0, t) * 120)
vmask = vmask.resize((W, H))
vig = Image.new("RGBA", (W, H), (0, 0, 0, 255))
vig.putalpha(vmask)
base.alpha_composite(vig)

# --- wordmark: "Steve" (dark red + lit edge) + " the Killer" (white) ---
steve_fs = int(0.235 * H)
killer_fs = int(steve_fs * 0.773)
fS = font(steve_fs); fK = font(killer_fs)
lsS = 0.038 * steve_fs; lsK = 0.038 * killer_fs
S_TXT = "Steve"; K_TXT = " the Killer"

total = seg_w(S_TXT, fS, lsS) + seg_w(K_TXT, fK, lsK)
maxw = 0.86 * W
if total > maxw:
    fac = maxw / total
    steve_fs = int(steve_fs * fac); killer_fs = int(killer_fs * fac)
    fS = font(steve_fs); fK = font(killer_fs)
    lsS = 0.038 * steve_fs; lsK = 0.038 * killer_fs
    total = seg_w(S_TXT, fS, lsS) + seg_w(K_TXT, fK, lsK)

x0 = (W - total) / 2
ybase = int(H * 0.455)
ascS = fS.getmetrics()[0]

# main wordmark on its own layer (for shadow derivation)
wm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dwm = ImageDraw.Draw(wm)
xend = draw_seg(dwm, x0, ybase, S_TXT, fS, lsS, DARKRED)
draw_seg(dwm, xend, ybase, K_TXT, fK, lsK, WHITE)

# drop shadow from the wordmark alpha
alpha = wm.split()[3]
shadow = Image.new("RGBA", (W, H), SHADOW + (0,))
shadow.putalpha(alpha.point(lambda a: int(a * 0.8)))
shadow = shadow.filter(ImageFilter.GaussianBlur(3 * SS))
base.alpha_composite(shadow, (2 * SS, 5 * SS))

# lit edge: "Steve" in bright red, offset up-left, behind main
lit = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw_seg(ImageDraw.Draw(lit), x0 - 3 * SS, ybase - 4 * SS, S_TXT, fS, lsS, LITRED)
base.alpha_composite(lit)

# main wordmark on top
base.alpha_composite(wm)
