"""Verify ALL written fields in PDF (encoding-safe)."""
import sys
sys.path.insert(0, r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad\tools')
from pathlib import Path
from pypdf import PdfReader

JUGADORES = Path(r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad\Jugadores')

for pdf_path in JUGADORES.glob("*.pdf"):
    print(f"=== {pdf_path.name} ===")
    reader = PdfReader(str(pdf_path))

    for pg_idx in range(2):
        page = reader.pages[pg_idx]
        if '/Annots' not in page:
            continue

        written = []
        for annot in page['/Annots']:
            obj = annot.get_object()
            if '/T' not in obj:
                continue
            name = str(obj['/T'])
            val = str(obj.get('/V', ''))
            ft = str(obj.get('/FT', ''))
            x0, y0, x1, y1 = [float(v) for v in obj['/Rect']]
            cx, cy = (x0+x1)/2, (y0+y1)/2

            if val and val != '':
                safe = val[:50].encode('ascii', errors='replace').decode('ascii')
                written.append((cy, name, safe, ft, cx))

        # Sort by cy desc (top to bottom)
        written.sort(key=lambda x: -x[0])
        print(f"  Page {pg_idx+1}: {len(written)} fields written")
        for cy, name, val, ft, cx in written:
            print(f"    {name:<30} cy={cy:.0f} cx={cx:.0f} = {val}")
