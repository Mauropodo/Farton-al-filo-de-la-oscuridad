"""Debug PDF field matching."""
import sys
sys.path.insert(0, r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad\tools')
from pathlib import Path
from pypdf import PdfReader

BASE = Path(r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad')
reader = PdfReader(str(BASE / 'tools' / 'plantilla_dnd_2024.pdf'))

def get_page_fields(reader, page_num):
    fields = {}
    page = reader.pages[page_num]
    for annot in page.get('/Annots', []):
        obj = annot.get_object()
        name = str(obj['/T'])
        x0, y0, x1, y1 = [float(v) for v in obj['/Rect']]
        fields[name] = {
            'rect': [x0, y0, x1, y1], 'cx': (x0 + x1) / 2, 'cy': (y0 + y1) / 2,
            'w': x1 - x0, 'h': y1 - y0, 'type': str(obj.get('/FT', ''))
        }
    return fields

def find_field(fields, cx_min, cx_max, cy_min, cy_max, w_min=0, w_max=999, h_min=0, h_max=999):
    for name, f in fields.items():
        if (cx_min <= f['cx'] <= cx_max and cy_min <= f['cy'] <= cy_max
                and w_min <= f['w'] <= w_max and h_min <= f['h'] <= h_max):
            return name, f
    return None, None

f = get_page_fields(reader, 0)

print("Testing ability score field matching:\n")

checks = [
    ('STR score', 140, 160, 620, 640),
    ('DEX score', 35, 55, 545, 560),
    ('CON score', 140, 160, 448, 465),
    ('INT score', 35, 55, 425, 445),
    ('WIS score', 140, 160, 275, 290),
    ('CHA score', 35, 55, 280, 295),
]
for label, cx1, cx2, cy1, cy2 in checks:
    name, ff = find_field(f, cx1, cx2, cy1, cy2, h_min=15, h_max=25)
    if name:
        print(f"  {label:15}: {name:<30} cx={ff['cx']:.1f} cy={ff['cy']:.1f} h={ff['h']:.1f}")
    else:
        print(f"  {label:15}: NOT FOUND")

print("\nCheck what fields exist near cy=620-640, cx=140-160:")
for name, ff in sorted(f.items(), key=lambda x: -x[1]['cy']):
    if 610 <= ff['cy'] <= 650 and 130 <= ff['cx'] <= 170:
        print(f"  {name:<30} cx={ff['cx']:.1f} cy={ff['cy']:.1f} w={ff['w']:.1f} h={ff['h']:.1f} type={ff['type']}")

print("\nCheck what fields exist near cy=540-560, cx=30-55:")
for name, ff in sorted(f.items(), key=lambda x: -x[1]['cy']):
    if 540 <= ff['cy'] <= 560 and 30 <= ff['cx'] <= 55:
        print(f"  {name:<30} cx={ff['cx']:.1f} cy={ff['cy']:.1f} w={ff['w']:.1f} h={ff['h']:.1f} type={ff['type']}")
