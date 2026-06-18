"""Debug: check what checkbox values are being set."""
import sys
sys.path.insert(0, r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad\tools')
from pathlib import Path
from pypdf import PdfReader, PdfWriter, generic

BASE = Path(r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad')
TEMPLATE = BASE / 'tools' / 'plantilla_dnd_2024.pdf'
JUGADORES = BASE / 'Jugadores'

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

reader = PdfReader(str(TEMPLATE))
fields = get_page_fields(reader, 0)

# Build skill_cbs same as in the main script
skill_cbs = sorted(
    [(n, f) for n, f in fields.items()
     if f['type'] == '/Btn' and 120 <= f['cx'] <= 135
     and 170 <= f['cy'] <= 595],
    key=lambda x: -x[1]['cy']
)

print("First 10 skill_cbs:")
for i, (n, f) in enumerate(skill_cbs[:10]):
    print(f"  {i}: {n:<30} cy={f['cy']:.0f} cx={f['cx']:.0f} type={f['type']}")

simulate_vals = {}
for i in range(5):
    simulate_vals[skill_cbs[i][0]] = '/Yes'

print("\nSimulated vals (first 5 checkboxes set to /Yes):")
for k, v in simulate_vals.items():
    print(f"  {k:<30} = {v}")

# Now test writing to a PDF
writer = PdfWriter()
writer.append(reader)
writer.update_page_form_field_values(writer.pages[0], {'CheckBox-DdsX2-jkWn': '/Yes'})

# Direct set
for annot_ref in writer.pages[0].get('/Annots', []):
    obj = annot_ref.get_object()
    name = str(obj.get('/T', ''))
    if name == 'CheckBox-DdsX2-jkWn':
        obj[generic.NameObject('/V')] = generic.NameObject('/Yes')
        obj[generic.NameObject('/AS')] = generic.NameObject('/Yes')
        print(f"\nDirect set done for {name}")

test_out = JUGADORES / 'test_cb.pdf'
with open(test_out, 'wb') as f:
    writer.write(f)

# Verify
r2 = PdfReader(str(test_out))
for annot_ref in r2.pages[0].get('/Annots', []):
    obj = annot_ref.get_object()
    if 'DdsX2' in str(obj.get('/T', '')):
        v = obj.get('/V')
        as_val = obj.get('/AS')
        print(f"Verified: V={v} AS={as_val}")
