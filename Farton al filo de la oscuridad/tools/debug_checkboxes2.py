"""Debug: Try checking checkboxes manually."""
import sys
sys.path.insert(0, r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad\tools')
from pathlib import Path
from pypdf import PdfReader, PdfWriter, generic

BASE = Path(r'I:\Mi unidad\Juegos Compartidos\ROL\Personalizadas\farton al filo de la oscuridad\Farton al filo de la oscuridad')
TEMPLATE = BASE / 'tools' / 'plantilla_dnd_2024.pdf'
JUGADORES = BASE / 'Jugadores'

# Read template
reader = PdfReader(str(TEMPLATE))
writer = PdfWriter()
writer.append(reader)

# Set a single checkbox via update_page_form_field_values first
writer.update_page_form_field_values(writer.pages[0], {
    'CheckBox-DdsX2-jkWn': '/Yes',
})

# Also try setting directly via annotation
for annot_ref in writer.pages[0].get('/Annots', []):
    annot = annot_ref.get_object()
    name = str(annot.get('/T', ''))
    if name == 'CheckBox-DdsX2-jkWn':
        annot[generic.NameObject('/AS')] = generic.NameObject('/Yes')
        annot[generic.NameObject('/V')] = generic.NameObject('/Yes')
        
# Save
output = JUGADORES / "test_checkbox.pdf"
with open(output, 'wb') as f:
    writer.write(f)

# Verify
reader2 = PdfReader(str(output))
for annot_ref in reader2.pages[0].get('/Annots', []):
    annot = annot_ref.get_object()
    if 'DdsX2' in str(annot.get('/T', '')):
        print(f"V={annot.get('/V')} AS={annot.get('/AS')}")
