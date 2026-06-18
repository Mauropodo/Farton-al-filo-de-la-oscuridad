"""Dump all PDF form fields with coordinates for verification."""
import sys
sys.path.insert(0, r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad\tools')
from pathlib import Path
from pypdf import PdfReader

BASE = Path(r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad')
TEMPLATE = BASE / 'tools' / 'plantilla_dnd_2024.pdf'

def get_page_fields(reader, page_num):
    fields = {}
    page = reader.pages[page_num]
    for annot in page.get('/Annots', []):
        obj = annot.get_object()
        name = str(obj['/T'])
        x0, y0, x1, y1 = [float(v) for v in obj['/Rect']]
        fields[name] = {
            'rect': [x0, y0, x1, y1],
            'cx': (x0 + x1) / 2,
            'cy': (y0 + y1) / 2,
            'w': x1 - x0,
            'h': y1 - y0,
            'type': str(obj.get('/FT', ''))
        }
    return fields

reader = PdfReader(str(TEMPLATE))
for pg in [0, 1]:
    print(f"\n{'='*60}")
    print(f"PAGE {pg+1} FIELDS (y=0 bottom, y=774 top)")
    print(f"{'='*60}")
    fields = get_page_fields(reader, pg)
    for name, f in sorted(fields.items(), key=lambda x: -x[1]['cy']):
        print(f"{name:<30} cx={f['cx']:>6.1f} cy={f['cy']:>6.1f}  w={f['w']:>5.1f} h={f['h']:>5.1f}  {f['type']}")
    print(f"\nTotal fields: {len(fields)}")
