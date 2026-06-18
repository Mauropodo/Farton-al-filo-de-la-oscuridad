"""Verify specific fields in generated PDF (no crash on encoding)."""
import sys
sys.path.insert(0, r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad\tools')
from pathlib import Path
from pypdf import PdfReader

JUGADORES = Path(r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad\Jugadores')
pdf_files = list(JUGADORES.glob("*.pdf"))

target_fields = [
    'Text-K5jiPv1zZt', 'Text-LH5D1gjQPU', 'Text-BPxh-vdM00',
    'Text-bVxZH_JLtD', 'Text-U0YbAjmSCO', 'Text-INUKHIjqxl',
    'Text-rYQnONzxJ4', 'Text-hmAw6o_vhL', 'Text-ycOaSOyi-6',
    'Text-EpsZXj58Ak', 'Text-Xwsg_wKnGm', 'Text-Z3OjMzBeLG',
    'Text-wzoAoPnjkr', 'Text-WnmAq9il-i', 'Text-Z5Fxtg33Xe',
    'Text-oOUHa8l3b-', 'Text-CX-KMKKD5u', 'Text-ZTxs8ke7sl',
    'Text-cYHeyUGAjX',
]

for pdf_path in pdf_files:
    print(f"Checking: {pdf_path.name}")
    reader = PdfReader(str(pdf_path))
    
    for pg_idx in range(2):
        page = reader.pages[pg_idx]
        if '/Annots' not in page:
            continue
        
        for annot in page['/Annots']:
            obj = annot.get_object()
            if '/T' not in obj:
                continue
            name = str(obj['/T'])
            if name not in target_fields:
                continue
            val = str(obj.get('/V', ''))
            x0, y0, x1, y1 = [float(v) for v in obj['/Rect']]
            cx, cy = (x0+x1)/2, (y0+y1)/2
            # ascii-safe display
            safe_val = val.encode('ascii', errors='replace').decode('ascii')
            print(f"  P{pg_idx+1} {name:<30} cx={cx:.0f} cy={cy:.0f} => '{safe_val}'")
    
    print()
