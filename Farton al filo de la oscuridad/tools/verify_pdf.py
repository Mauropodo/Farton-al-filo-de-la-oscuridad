"""Verify which fields were set in the generated PDF."""
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
    print(f"\n{'='*60}")
    print(f"VERIFICANDO: {pdf_path.name}")
    print(f"{'='*60}")
    reader = PdfReader(str(pdf_path))
    
    for pg_idx in range(min(2, len(reader.pages))):
        print(f"\n--- Page {pg_idx+1} ---")
        page = reader.pages[pg_idx]
        if '/Annots' not in page:
            print("  No annotations")
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
                print(f"  {name:<30} = {val:<30}  (cx={cx:.0f} cy={cy:.0f} type={ft})")
