"""Verify PDF fields written - cleaner output."""
import sys
sys.path.insert(0, r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad\tools')
from pathlib import Path
from pypdf import PdfReader

JUGADORES = Path(r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad\Jugadores')

pdf_files = list(JUGADORES.glob("*.pdf"))
if not pdf_files:
    print("No PDF files found")
    sys.exit(1)

for pdf_path in pdf_files:
    print(f"VERIFICANDO: {pdf_path.name}")
    reader = PdfReader(str(pdf_path))
    
    for pg_idx in range(min(2, len(reader.pages))):
        count = 0
        page = reader.pages[pg_idx]
        if '/Annots' not in page:
            continue
        
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
                count += 1
                safe_val = val[:40].replace('\n', ' ').replace('\r', ' ')
                print(f"  P{pg_idx+1} {name:<30} = {safe_val:<40}  (cx={cx:.0f} cy={cy:.0f})")
        
        if count == 0:
            print(f"  Page {pg_idx+1}: no fields set")
        else:
            print(f"  Page {pg_idx+1}: {count} fields set total")
