"""Debug checkbox export values."""
import sys
sys.path.insert(0, r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad\tools')
from pathlib import Path
from pypdf import PdfReader

JUGADORES = Path(r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad\Jugadores')
TEMPLATE = Path(r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad\tools\plantilla_dnd_2024.pdf')

# Check template
print("=== TEMPLATE CHECKBOXES ===")
reader = PdfReader(str(TEMPLATE))
page = reader.pages[0]
count = 0
for annot in page.get('/Annots', []):
    obj = annot.get_object()
    if '/T' not in obj:
        continue
    name = str(obj['/T'])
    ft = str(obj.get('/FT', ''))
    if ft == '/Btn':
        ap_n = obj.get('/AP', {}).get('/N', {})
        keys = list(ap_n.keys()) if hasattr(ap_n, 'keys') else []
        vals = {'V': str(obj.get('/V', '')), 'DV': str(obj.get('/DV', ''))}
        count += 1
        if count <= 3:
            print(f"  {name:<30} AP keys: {keys}  V={vals['V']} DV={vals['DV']}")

# Check generated PDF
print("\n=== GENERATED PDF CHECKBOXES (proficient skills) ===")
pdf_files = list(JUGADORES.glob("*.pdf"))
for pdf_path in pdf_files:
    reader = PdfReader(str(pdf_path))
    page = reader.pages[0]
    
    # Find the expected profficient checkboxes
    # Arcano is index 1 in skill_cbs, which should be cy≈566
    cb_list = []
    for annot in page.get('/Annots', []):
        obj = annot.get_object()
        if str(obj.get('/T', '')).startswith('CheckBox'):
            x0, y0, x1, y1 = [float(v) for v in obj['/Rect']]
            cx, cy = (x0+x1)/2, (y0+y1)/2
            if 120 <= cx <= 135:
                cb_list.append((cy, str(obj['/T']), str(obj.get('/V', ''))))
    
    cb_list.sort(key=lambda x: -x[0])
    for i, (cy, name, val) in enumerate(cb_list[:10]):
        print(f"  idx={i} cy={cy:.0f} {name:<30} V={val}")
