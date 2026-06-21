#!/usr/bin/env python3
"""Slice icons.png (3x3 sprite sheet) into 9 centered, uniform, transparent PNGs."""
from PIL import Image
from collections import deque
import os

SRC = "icons.png"
OUT = "icons"
os.makedirs(OUT, exist_ok=True)

# Row-major mapping to LOCS keys
NAMES = [
    ["gym", "library", "park"],
    ["cafe", "museum", "airport"],
    ["restaurant", "temple", "university"],
]

img = Image.open(SRC).convert("RGBA")
W, H = img.size
cw, ch = W / 3.0, H / 3.0

INSET = 26       # drop dashed grid border lines
FUZZ = 52        # bg color tolerance for flood fill
PAD = 14         # padding around trimmed sticker

def color_dist(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1]) + abs(a[2]-b[2])

def flood_transparent(im, fuzz):
    """Flood-fill from all border pixels, making bg-colored pixels transparent.
    Stops at the bright sticker outline, so dark interior stays opaque."""
    px = im.load()
    w, h = im.size
    # bg reference = average of the 4 corners
    corners = [px[0,0], px[w-1,0], px[0,h-1], px[w-1,h-1]]
    bg = tuple(sum(c[i] for c in corners)//4 for i in range(3))
    seen = [[False]*w for _ in range(h)]
    q = deque()
    for x in range(w):
        q.append((x,0)); q.append((x,h-1))
    for y in range(h):
        q.append((0,y)); q.append((w-1,y))
    while q:
        x, y = q.popleft()
        if x<0 or y<0 or x>=w or y>=h or seen[y][x]:
            continue
        seen[y][x] = True
        r,g,b,a = px[x,y]
        if color_dist((r,g,b), bg) <= fuzz:
            px[x,y] = (r,g,b,0)
            q.append((x+1,y)); q.append((x-1,y))
            q.append((x,y+1)); q.append((x,y-1))
    return im

def bbox_opaque(im):
    px = im.load()
    w, h = im.size
    minx, miny, maxx, maxy = w, h, 0, 0
    found = False
    for y in range(h):
        for x in range(w):
            if px[x,y][3] > 24:
                found = True
                if x<minx: minx=x
                if y<miny: miny=y
                if x>maxx: maxx=x
                if y>maxy: maxy=y
    if not found:
        return None
    return (minx, miny, maxx+1, maxy+1)

cells = []
for r in range(3):
    for c in range(3):
        left = int(round(c*cw)) + INSET
        top = int(round(r*ch)) + INSET
        right = int(round((c+1)*cw)) - INSET
        bottom = int(round((r+1)*ch)) - INSET
        cell = img.crop((left, top, right, bottom))
        cell = flood_transparent(cell, FUZZ)
        bb = bbox_opaque(cell)
        if bb:
            sticker = cell.crop(bb)
        else:
            sticker = cell
        cells.append((NAMES[r][c], sticker))

# Uniform square canvas = largest sticker dimension + padding
maxdim = max(max(s.size) for _, s in cells)
canvas_sz = maxdim + PAD*2

for name, sticker in cells:
    canvas = Image.new("RGBA", (canvas_sz, canvas_sz), (0,0,0,0))
    sw, sh = sticker.size
    ox = (canvas_sz - sw)//2
    oy = (canvas_sz - sh)//2
    canvas.paste(sticker, (ox, oy), sticker)
    # downscale to a sensible delivery size
    final = canvas.resize((256, 256), Image.LANCZOS)
    final.save(os.path.join(OUT, f"{name}.png"))
    print(f"  {name}.png  (sticker {sw}x{sh} -> 256x256 canvas)")

print(f"Canvas size {canvas_sz}px, 9 icons written to {OUT}/")
