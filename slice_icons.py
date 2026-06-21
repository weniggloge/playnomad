#!/usr/bin/env python3
"""Slice sprite sheets into clean, centered, transparent PNGs.

Strategy (robust against the dashed grid lines):
  1. cut the sheet into grid cells
  2. flood-fill the navy background to transparent from the cell borders
  3. keep only the LARGEST connected opaque blob (= the sticker);
     this discards the leftover dashed-line fragments entirely
  4. tight-crop to that blob, then center on a uniform square canvas
"""
from PIL import Image
from collections import deque
import os, sys

def flood_bg_transparent(im, fuzz=60):
    px = im.load(); w, h = im.size
    corners = [px[0,0], px[w-1,0], px[0,h-1], px[w-1,h-1]]
    bg = tuple(sum(c[i] for c in corners)//4 for i in range(3))
    seen = bytearray(w*h)
    q = deque()
    for x in range(w): q.append((x,0)); q.append((x,h-1))
    for y in range(h): q.append((0,y)); q.append((w-1,y))
    def dist(c): return abs(c[0]-bg[0])+abs(c[1]-bg[1])+abs(c[2]-bg[2])
    while q:
        x,y = q.popleft()
        if x<0 or y<0 or x>=w or y>=h or seen[y*w+x]: continue
        seen[y*w+x]=1
        r,g,b,a = px[x,y]
        if dist((r,g,b))<=fuzz:
            px[x,y]=(r,g,b,0)
            q.append((x+1,y)); q.append((x-1,y)); q.append((x,y+1)); q.append((x,y-1))
    return im

def largest_blob_only(im, alpha_min=40):
    """Keep only the largest connected component of opaque pixels."""
    px = im.load(); w, h = im.size
    label = [0]*(w*h)
    best_id, best_size, best_px = 0, 0, None
    cur = 0
    for sy in range(h):
        for sx in range(w):
            idx = sy*w+sx
            if label[idx] or px[sx,sy][3] < alpha_min: continue
            cur += 1
            size = 0; comp = []
            q = deque([(sx,sy)]); label[idx]=cur
            while q:
                x,y = q.popleft(); size += 1; comp.append((x,y))
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx,ny = x+dx,y+dy
                    if 0<=nx<w and 0<=ny<h:
                        ni = ny*w+nx
                        if not label[ni] and px[nx,ny][3]>=alpha_min:
                            label[ni]=cur; q.append((nx,ny))
            if size > best_size:
                best_size, best_id, best_px = size, cur, comp
    if best_px is None:
        return im, 0
    # erase everything not in the largest blob
    keep = set(best_px)
    for y in range(h):
        for x in range(w):
            if px[x,y][3] and (x,y) not in keep:
                r,g,b,_ = px[x,y]; px[x,y]=(r,g,b,0)
    return im, best_size

def bbox_opaque(im, alpha_min=40):
    px=im.load(); w,h=im.size
    minx,miny,maxx,maxy = w,h,0,0; found=False
    for y in range(h):
        for x in range(w):
            if px[x,y][3]>=alpha_min:
                found=True
                minx=min(minx,x); miny=min(miny,y); maxx=max(maxx,x); maxy=max(maxy,y)
    return (minx,miny,maxx+1,maxy+1) if found else None

def slice_sheet(src, cols, rows, names, outdir, out_size=256, pad_frac=0.08, min_area=2000):
    img = Image.open(src).convert("RGBA")
    W,H = img.size; cw, ch = W/cols, H/rows
    os.makedirs(outdir, exist_ok=True)
    stickers=[]
    for r in range(rows):
        for c in range(cols):
            i = r*cols+c
            if i>=len(names) or names[i] is None: continue
            cell = img.crop((int(round(c*cw)),int(round(r*ch)),int(round((c+1)*cw)),int(round((r+1)*ch))))
            cell = flood_bg_transparent(cell)
            cell, area = largest_blob_only(cell)
            if area < min_area:
                print(f"  (skip empty cell {r},{c})"); continue
            bb = bbox_opaque(cell)
            stickers.append((names[i], cell.crop(bb)))
    maxdim = max(max(s.size) for _,s in stickers)
    pad = int(maxdim*pad_frac)
    canvas_sz = maxdim + pad*2
    for name, st in stickers:
        canvas = Image.new("RGBA",(canvas_sz,canvas_sz),(0,0,0,0))
        sw,sh = st.size
        canvas.paste(st, ((canvas_sz-sw)//2,(canvas_sz-sh)//2), st)
        canvas.resize((out_size,out_size), Image.LANCZOS).save(os.path.join(outdir,f"{name}.png"))
        print(f"  {outdir}/{name}.png  (blob {sw}x{sh})")
    print(f"  -> uniform canvas {canvas_sz}px\n")

# Location icons: 3x3  (minimal padding so the art fills the square)
slice_sheet("icons.png", 3, 3,
    ["gym","library","park","cafe","museum","airport","restaurant","temple","university"],
    "icons", pad_frac=0.02)

# Avatar icons: 3 cols x 2 rows, last cell empty
slice_sheet("avataricons.png", 3, 2,
    ["nomad","mage","witch","rogue","executive",None],
    "icons/avatars", pad_frac=0.02)
