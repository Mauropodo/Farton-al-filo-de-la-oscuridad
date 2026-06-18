"""Debug PDF generation step by step."""
import sys
sys.path.insert(0, r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad\tools')
from pathlib import Path
from pypdf import PdfReader

BASE = Path(r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad')
JUGADORES = BASE / 'Jugadores'
TEMPLATE = BASE / 'tools' / 'plantilla_dnd_2024.pdf'

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
            return name
    return None

reader = PdfReader(str(TEMPLATE))
fields = get_page_fields(reader, 0)

# Test all the score fields
print("Testing ability score matching in main script:")

# STR score: cx=140-160, cy=620-640, h_min=15, h_max=25
result = find_field(fields, 140, 160, 620, 640, h_min=15, h_max=25)
print(f"  STR score: {result}")

# DEX score: cx=35-55, cy=545-560, h_min=15, h_max=25
result = find_field(fields, 35, 55, 545, 560, h_min=15, h_max=25)
print(f"  DEX score: {result}")

# INT score: cx=35-55, cy=425-445, h_min=15, h_max=25
result = find_field(fields, 35, 55, 425, 445, h_min=15, h_max=25)
print(f"  INT score: {result}")

# STR mod: cx=170-190, cy=618-630, h_min=12, h_max=22
result = find_field(fields, 170, 190, 618, 630, h_min=12, h_max=22)
print(f"  STR mod: {result}")

# DEX mod: cx=65-85, cy=542-552, h_min=12, h_max=22
result = find_field(fields, 65, 85, 542, 552, h_min=12, h_max=22)
print(f"  DEX mod: {result}")

# Prof bonus: cx=45-70, cy=618-630, w_min=15, w_max=30
result = find_field(fields, 45, 70, 618, 630, w_min=15, w_max=30)
print(f"  Prof bonus: {result}")

# AC: cx=530-560, cy=628-640, w_min=35, w_max=55
result = find_field(fields, 530, 560, 628, 640, w_min=35, w_max=55)
print(f"  AC: {result}")

# Also list all Text fields with their cy for verification
print(f"\nAll Text fields (sorted by cy descending):")
for name, f in sorted(fields.items(), key=lambda x: -x[1]['cy']):
    if f['type'] == '/Tx':
        print(f"  {name:<30} cx={f['cx']:.1f} cy={f['cy']:.1f} w={f['w']:.1f} h={f['h']:.1f}")
