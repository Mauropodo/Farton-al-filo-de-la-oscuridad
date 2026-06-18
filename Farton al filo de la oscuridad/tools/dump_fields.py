from pypdf import PdfReader

reader = PdfReader(r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad\tools\plantilla_dnd_2024.pdf')

for page_num in range(2):
    page = reader.pages[page_num]
    print(f'=== PAGE {page_num+1} ===')
    annots = page.get('/Annots', [])
    fields = []
    for annot in annots:
        obj = annot.get_object()
        name = obj.get('/T', 'NO_NAME')
        ft = str(obj.get('/FT', ''))
        rect = [float(v) for v in obj.get('/Rect', [0,0,0,0])]
        cx = (rect[0] + rect[2]) / 2
        cy = (rect[1] + rect[3]) / 2
        w = rect[2] - rect[0]
        h = rect[3] - rect[1]
        fields.append({
            'name': name, 'type': ft,
            'cx': round(cx, 1), 'cy': round(cy, 1),
            'w': round(w, 1), 'h': round(h, 1),
            'rect': [round(r, 1) for r in rect]
        })
    
    fields.sort(key=lambda f: (-f['cy'], f['cx']))
    for f in fields:
        line = "  cx={cx:6.1f} cy={cy:6.1f} w={w:5.1f} h={h:4.1f} type={t:5s} name={n}".format(
            cx=f['cx'], cy=f['cy'], w=f['w'], h=f['h'], t=f['type'], n=f['name']
        )
        print(line)
    print()
