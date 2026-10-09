#!/usr/bin/env python3
"""
Extract sprites/assets from the Breakout-style game screenshot.
Requires: Pillow, numpy, scipy
"""

from PIL import Image
import numpy as np
from scipy import ndimage
import os
from collections import defaultdict

# ========== CONFIG ==========
INPUT_IMAGE = "image.png"   # change if needed
OUTPUT_DIR  = "extracted_assets"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Background colors to ignore (from the image)
BG_COLORS = [
    (69, 40, 60),    # dark maroon
    (63, 63, 116),   # purple-blue
    (34, 32, 52),    # darker purple
]

# ========== 1. Load image ==========
im = Image.open(INPUT_IMAGE).convert("RGB")
arr = np.array(im)
h, w = arr.shape[:2]
print(f"Loaded image: {w}×{h}")

# ========== 2. Create foreground mask ==========
mask = np.ones((h, w), dtype=bool)
for bg in BG_COLORS:
    dist = np.linalg.norm(arr.astype(float) - np.array(bg), axis=2)
    mask &= (dist > 28)

# ========== 3. Connected components ==========
structure = np.ones((3, 3), dtype=int)          # 8-connectivity
labeled, num_features = ndimage.label(mask, structure=structure)
print(f"Found {num_features} connected components")

# ========== 4. Extract sprites ==========
sprites = []
for i in range(1, num_features + 1):
    comp = (labeled == i)
    size = int(comp.sum())
    if size < 30 or size > 3500:          # ignore noise & huge blobs
        continue

    ys, xs = np.where(comp)
    y1, y2 = int(ys.min()), int(ys.max())
    x1, x2 = int(xs.min()), int(xs.max())

    crop = arr[y1:y2+1, x1:x2+1]
    crop_mask = comp[y1:y2+1, x1:x2+1]

    # RGBA with transparency
    rgba = np.zeros((crop.shape[0], crop.shape[1], 4), dtype=np.uint8)
    rgba[..., :3] = crop
    rgba[..., 3] = np.where(crop_mask, 255, 0)

    sprites.append({
        "id": i,
        "bbox": (x1, y1, x2, y2),
        "size": size,
        "w": x2 - x1 + 1,
        "h": y2 - y1 + 1,
        "img": Image.fromarray(rgba, "RGBA"),
    })

# Sort by size (biggest first)
sprites.sort(key=lambda s: -s["size"])
print(f"Kept {len(sprites)} useful sprites\n")

# ========== 5. Save everything + classify ==========
paddle_saved = False
ball_saved = False
brick_count = defaultdict(int)

for s in sprites:
    x1, y1, x2, y2 = s["bbox"]
    name = f"sprite_{s['id']:03d}_{s['w']}x{s['h']}"

    # --- Classify by size / position ---
    if s["w"] > 100 and s["h"] < 40 and y1 > 500:          # paddle
        name = "paddle"
        paddle_saved = True
    elif 8 <= s["w"] <= 16 and 8 <= s["h"] <= 16 and y1 > 400:  # ball
        name = "ball"
        ball_saved = True
    elif 45 <= s["w"] <= 60 and 18 <= s["h"] <= 32:          # normal bricks
        # Sample center color to name the brick
        cx, cy = s["w"] // 2, s["h"] // 2
        r, g, b = s["img"].getpixel((cx, cy))[:3]
        if b > 180 and r < 130:          color = "blue"
        elif g > 140 and r < 130:        color = "green"
        elif r > 200 and g > 200:        color = "yellow"
        elif r > 200 and g > 90:         color = "orange"
        elif r > 150 and g < 80:         color = "red"
        else:                            color = "other"
        brick_count[color] += 1
        name = f"brick_{color}_{brick_count[color]:02d}"
    elif y1 < 50 and s["w"] < 20:                            # lives / hearts
        name = f"life_{s['id']}"

    out_path = os.path.join(OUTPUT_DIR, f"{name}.png")
    s["img"].save(out_path)
    print(f"  saved {name:25s}  {s['w']:3d}×{s['h']:<3d}  @ ({x1:3d},{y1:3d})")

# ========== 6. Extra: clean manual crops of the nicest bricks ==========
# (these give perfect single-brick assets without any edge artifacts)

manual_crops = {
    # name: (left, top, right, bottom)
    "brick_blue_clean":   (188,  88, 239, 109),
    "brick_red_clean":    (254, 122, 305, 143),
    "brick_green_clean":  (386, 122, 437, 143),
    "brick_orange_clean": (518, 122, 569, 143),
    "brick_yellow_clean": (320, 156, 371, 181),   # approx special
    "paddle_clean":       (402, 544, 517, 569),
    "ball_clean":         (378, 420, 386, 430),
}

print("\n--- Clean manual crops ---")
for name, (l, t, r, b) in manual_crops.items():
    crop = im.crop((l, t, r, b))
    # Make background transparent
    crop = crop.convert("RGBA")
    data = np.array(crop)
    # simple chroma-key against the three bg colors
    for bg in BG_COLORS:
        dist = np.linalg.norm(data[..., :3].astype(float) - bg, axis=2)
        data[dist < 30, 3] = 0
    Image.fromarray(data).save(os.path.join(OUTPUT_DIR, f"{name}.png"))
    print(f"  saved {name}")

print(f"\nDone! All assets are in: ./{OUTPUT_DIR}/")
print("You now have individual bricks, paddle, ball, lives, etc.")
