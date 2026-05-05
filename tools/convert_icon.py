"""Convert the 512x512 PNG into a multi-size .ico for Windows apps.

Usage: python tools/convert_icon.py
"""
from PIL import Image
import os

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, '..'))
ASSETS = os.path.join(ROOT, 'hqspg', 'assets')

SRC = os.path.join(ASSETS, '512x512HQ.png')
OUT = os.path.join(ASSETS, 'hqspg_icon.ico')

def main():
    if not os.path.isfile(SRC):
        print('Source image not found:', SRC)
        return 1
    img = Image.open(SRC).convert('RGBA')
    # ICO can contain multiple sizes; Pillow will resize when saving with sizes
    sizes = [(16,16),(32,32),(48,48),(256,256),(512,512)]
    # Pillow expects the largest image; provide it and sizes parameter
    img.save(OUT, format='ICO', sizes=sizes)
    print('Wrote', OUT)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
