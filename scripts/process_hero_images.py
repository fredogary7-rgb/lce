"""Process hero engine images: blue tint, blur, smart crop, WebP export."""
import os
from PIL import Image, ImageFilter, ImageEnhance

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE, 'static', 'images')
HERO_DIR = os.path.join(IMG_DIR, 'hero')

os.makedirs(HERO_DIR, exist_ok=True)

# Config: (filename, crop_box (left, top, right, bottom), target_width)
# Crop boxes designed to show only a portion of each engine
CONFIGS = [
    {
        'src': 'cha.JPG',
        'dst': 'cha.webp',
        # Show front-right portion of the forklift (top-left area)
        'crop': (60, 20, 380, 340),
        'width': 550,
    },
    {
        'src': 'gru.JPG',
        'dst': 'gru.webp',
        # Show cabin/upper part of the crane (right side)
        'crop': (180, 10, 520, 380),
        'width': 520,
    },
    {
        'src': 'pelle.JPG',
        'dst': 'pelle.webp',
        # Show arm/bucket of the excavator (bottom-left area)
        'crop': (30, 60, 360, 420),
        'width': 500,
    },
]

for cfg in CONFIGS:
    src_path = os.path.join(IMG_DIR, cfg['src'])
    dst_path = os.path.join(HERO_DIR, cfg['dst'])

    if not os.path.exists(src_path):
        print(f'  SKIP: {cfg["src"]} not found')
        continue

    img = Image.open(src_path).convert('RGB')

    # Smart crop
    left, top, right, bottom = cfg['crop']
    # Clamp crop to image bounds
    left = max(0, left)
    top = max(0, top)
    right = min(img.width, right)
    bottom = min(img.height, bottom)
    img = img.crop((left, top, right, bottom))

    # Resize to target width, keep aspect ratio
    ratio = cfg['width'] / img.width
    new_h = int(img.height * ratio)
    img = img.resize((cfg['width'], new_h), Image.LANCZOS)

    # Subtle blue tint via RGB channel manipulation
    r, g, b = img.split()
    # Boost blue channel, reduce red/yellow
    r = r.point(lambda x: int(x * 0.55))
    g = g.point(lambda x: int(x * 0.70))
    b = b.point(lambda x: min(255, int(x * 1.25)))
    img = Image.merge('RGB', (r, g, b))

    # Slight desaturation for monochrome feeling
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(0.30)  # 30% of original saturation

    # Soft blur for atmospheric depth
    img = img.filter(ImageFilter.GaussianBlur(radius=2.5))

    # Slight brightness reduction
    enhancer_b = ImageEnhance.Brightness(img)
    img = enhancer_b.enhance(0.85)

    # Contrast boost to keep details visible
    enhancer_c = ImageEnhance.Contrast(img)
    img = enhancer_c.enhance(1.08)

    # Save as optimized WebP
    img.save(dst_path, 'WEBP', quality=60, method=6)
    size_kb = os.path.getsize(dst_path) / 1024
    print(f'  ✓ {cfg["src"]} -> hero/{cfg["dst"]} ({img.width}x{img.height}, {size_kb:.1f} KB)')

print('\nAll hero images processed!')