import os
import re
import sys
import yaml
import unicodedata
from pathlib import Path
from pypdf import PdfReader, PdfWriter

BASE = Path(__file__).resolve().parent.parent
JUGADORES = BASE / "Jugadores"
TEMPLATE = BASE / "tools" / "plantilla_dnd_2024.pdf"

SKILL_ORDER_ES = [
    "acrobacias", "trato con animales", "arcano", "atletismo",
    "engañar", "historia", "perspicacia", "intimidar",
    "investigación", "medicina", "naturaleza", "percepción",
    "actuación", "persuasión", "religión", "juego de manos",
    "sigilo", "supervivencia"
]


def clean_md(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'^###\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^##\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_frontmatter(text):
    m = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
    return yaml.safe_load(m.group(1)) if m else {}


def parse_table(body):
    rows = []
    for line in body.split('\n'):
        line = line.strip()
        if line.startswith('|') and line.endswith('|'):
            cols = [c.strip() for c in line.split('|')[1:-1]]
            if len(cols) >= 2 and not all(c == '---' or set(c) <= set('-: ') for c in cols):
                rows.append(cols)
    return rows


def calc_mod(score):
    return (score - 10) // 2


def parse_character(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    fm = parse_frontmatter(text)

    name_m = re.search(r'^# (.+)$', text, re.MULTILINE)
    name = clean_md(name_m.group(1).strip()) if name_m else fm.get('nombre', '')

    # Split the name: "Mago - Lyra Brisaveloz" → class name + character name
    # The name already contains both; we need to extract the character name
    if ' - ' in name:
        parts = name.split(' - ', 1)
        char_name = parts[1]
    else:
        char_name = name

    data = {
        'name': char_name,
        'class': fm.get('clase', ''),
        'level': str(fm.get('nivel', 1)),
        'race': fm.get('raza', ''),
        'alignment': fm.get('alineamiento', ''),
        'hp_max': str(fm.get('hp_max', '')),
        'hp_current': str(fm.get('hp_actual', '')),
        'ac': str(fm.get('ca', '')),
        'speed': str(fm.get('velocidad', '')),
        'initiative': str(fm.get('iniciativa', '')),
        'prof_bonus': f"+{fm.get('bonificador_de_competencia', 2)}",
        'str': fm.get('fuerza', 10),
        'dex': fm.get('destreza', 10),
        'con': fm.get('constitucion', 10),
        'int': fm.get('inteligencia', 10),
        'wis': fm.get('sabiduria', 10),
        'cha': fm.get('carisma', 10),
    }

    sections = re.split(r'^## ', text, flags=re.MULTILINE)
    for sec in sections:
        header = sec.split('\n')[0].strip()
        body = '\n'.join(sec.split('\n')[1:])

        if 'Estad' in header:
            table = parse_table(body)
            for cols in table:
                key = cols[0].strip().lower()
                val = cols[1].strip()
                if 'cordura' in key:
                    parts = val.split('/')
                    data['sanity_max'] = parts[0].strip()
                    data['sanity_current'] = parts[1].strip() if len(parts) > 1 else parts[0].strip()
                elif 'pg m' in key:
                    data['hp_max'] = val
                elif 'pg a' in key:
                    data['hp_current'] = val
                elif key == '**ca**' or key == 'ca':
                    data['ac'] = val.split()[0]
                elif 'velocidad' in key:
                    data['speed'] = val.split()[0]
                elif 'iniciativa' in key:
                    data['initiative'] = val
                elif 'competencia' in key:
                    data['prof_bonus'] = val
                elif 'dados de golpe' in key or 'dados' in key:
                    data['hit_dice'] = val

        elif header == 'Características':
            data['save_profs'] = {}
            table = parse_table(body)
            for cols in table:
                stat = cols[0].strip().lower()
                val = cols[1].strip()
                if 'fuerza' in stat:
                    data['str'] = int(val)
                elif 'destreza' in stat:
                    data['dex'] = int(val)
                elif 'constitución' in stat or 'constitucion' in stat:
                    data['con'] = int(val)
                elif 'inteligencia' in stat:
                    data['int'] = int(val)
                elif 'sabiduría' in stat or 'sabiduria' in stat:
                    data['wis'] = int(val)
                elif 'carisma' in stat:
                    data['cha'] = int(val)
                # Detect save proficiency from 4th column (Save column)
                if len(cols) >= 4:
                    save_col = cols[3].strip()
                    if 'V' in save_col or '✓' in save_col or 'v' in save_col:
                        stat_key = ''
                        if 'fuerza' in stat: stat_key = 'str'
                        elif 'destreza' in stat: stat_key = 'dex'
                        elif 'constitución' in stat or 'constitucion' in stat: stat_key = 'con'
                        elif 'inteligencia' in stat: stat_key = 'int'
                        elif 'sabiduría' in stat or 'sabiduria' in stat: stat_key = 'wis'
                        elif 'carisma' in stat: stat_key = 'cha'
                        if stat_key:
                            data['save_profs'][stat_key] = True

        elif header == 'Habilidades':
            data['skills'] = []
            table = parse_table(body)
            for cols in table:
                if cols[0].strip().lower().startswith('habilidad'):
                    continue
                skill = clean_md(cols[0].strip())
                mod_val = cols[1].strip()
                # Check mark (✓) or V indicates proficiency
                prof = len(cols) > 2 and (chr(10003) in cols[2] or 'V' in cols[2])
                data['skills'].append({
                    'name': skill,
                    'mod': mod_val.replace(chr(8722), '-'),  # Unicode minus → hyphen
                    'proficient': prof
                })

        elif header == 'Ataques':
            data['attacks'] = []
            table = parse_table(body)
            for cols in table:
                if cols[0].strip().lower() == 'ataque':
                    continue
                bonus = cols[1].strip()
                data['attacks'].append({
                    'name': cols[0].strip(),
                    'bonus': bonus,
                    'damage': cols[2].strip(),
                    'type': cols[3].strip() if len(cols) > 3 else ''
                })

        elif header == 'Equipo':
            data['equipment'] = []
            table = parse_table(body)
            for cols in table:
                item = cols[0].strip()
                qty = cols[1].strip() if len(cols) > 1 else '1'
                data['equipment'].append(f"{item} x{qty}")

        elif header == 'Competencias e idiomas':
            data['proficiencies'] = clean_md(body.strip())

        elif header == 'Cordura':
            data['sanity_section'] = body.strip()
            s_max = re.search(r'\*\*Cordura máxima\*\*\s*\|\s*(\d+)', body)
            s_cur = re.search(r'\*\*Cordura actual\*\*\s*\|\s*(\d+)', body)
            s_trauma = re.search(r'\*\*Traumas activos\*\*\s*\|\s*(.*)', body)
            if s_max: data['sanity_max'] = s_max.group(1)
            if s_cur: data['sanity_current'] = s_cur.group(1)
            if s_trauma: data['sanity_traumas'] = s_trauma.group(1).strip()

        elif header.startswith('Trasfondo'):
            data['background'] = re.sub(r'\[\[.*?\]\]', '', clean_md(body)).strip()

        elif 'Trucos' in header:
            data['cantrips'] = clean_md(body.strip())

        elif header.startswith('Hechizos preparados'):
            data['spells'] = clean_md(body.strip())

        elif header == 'Rasgos y aptitudes':
            data['features'] = clean_md(body.strip())

    for k in ['skills', 'attacks', 'equipment']:
        data.setdefault(k, [])
    for k in ['proficiencies', 'background', 'sanity_max', 'sanity_current', 'sanity_traumas', 'cantrips', 'spells', 'features']:
        data.setdefault(k, '')
    data.setdefault('sanity_traumas', chr(8212))
    data.setdefault('hit_dice', '1d6')

    return data


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


def build_page1_values(data, fields):
    vals = {}

    # Coords: y=0 bottom, y=774 top. Higher cy = higher on page.
    # All field coordinates verified from dump.

    # ===================== HEADER =====================
    # Name: cx≈140 cy≈753 w≈222 - LEFT EMPTY per requirement

    # Class: cx≈85 cy≈730 w≈119 (Text-VHOEWtcX0f)
    cl = find_field(fields, 70, 100, 724, 736, w_min=100)
    if cl: vals[cl] = data['class']

    # Level (circle): cx≈339 cy≈729 w≈33 (Text-0Ka9rOFA0F)
    lvl = find_field(fields, 325, 355, 724, 735, w_min=25, w_max=40)
    if lvl: vals[lvl] = data['level']

    # XP: cx≈404 cy≈726 w≈50 h≈46 (Text-WnmAq9il-i)
    xp = find_field(fields, 385, 420, 720, 735, w_min=40, w_max=60)
    if xp: vals[xp] = ''

    # Race: cx≈85 cy≈708 w≈119 (Text-6gGZ9W4hzu)
    race = find_field(fields, 70, 100, 703, 714, w_min=100)
    if race: vals[race] = data['race']

    # Subclass: cx≈197 cy≈708 w≈98 (Text-Z5Fxtg33Xe)
    sub = find_field(fields, 180, 215, 703, 714, w_min=80)
    if sub: vals[sub] = ''

    # Background: cx≈277 cy≈714 w≈43 (Text-CX-KMKKD5u)
    bg = find_field(fields, 260, 290, 708, 720, w_min=35, w_max=55)
    if bg and data.get('background'):
        vals[bg] = data['background'][:40]

    # Alignment: try other header fields
    # Text-4e56MHQxyH: cx=276.6 cy=737.9 w=27.3
    al = find_field(fields, 260, 290, 733, 743, w_min=20, w_max=35)
    if al and data.get('alignment'):
        vals[al] = data['alignment']

    # ===================== PROFICIENCY BONUS =====================
    # Text-wzoAoPnjkr: cx=57.9 cy=623.2 w=22.0 h=40.3 (tall field)
    prof = find_field(fields, 45, 70, 618, 630, w_min=15, w_max=30)
    if prof: vals[prof] = data['prof_bonus']

    # ===================== ABILITY SCORES =====================
    # Right column (cx≈150): STR(cy=630), CON(cy=456), WIS(cy=282)
    # Left column (cx≈44): DEX(cy=553), INT(cy=435), CHA(cy=288)
    score_map = {
        'str': (140, 160, 620, 640),
        'dex': (35, 55, 545, 560),
        'con': (140, 160, 448, 465),
        'int': (35, 55, 425, 445),
        'wis': (140, 160, 275, 290),
        'cha': (35, 55, 280, 295),
    }
    for stat, (cx1, cx2, cy1, cy2) in score_map.items():
        f = find_field(fields, cx1, cx2, cy1, cy2, h_min=15, h_max=25, w_min=20)
        if f: vals[f] = str(data.get(stat, 10))

    # Modifiers (circles next to scores, w≈23)
    mod_map = {
        'str': (170, 190, 618, 630),
        'dex': (65, 85, 542, 552),
        'con': (170, 190, 445, 455),
        'int': (65, 85, 424, 435),
        'wis': (170, 190, 270, 282),
        'cha': (65, 85, 278, 290),
    }
    for stat, (cx1, cx2, cy1, cy2) in mod_map.items():
        f = find_field(fields, cx1, cx2, cy1, cy2, h_min=12, h_max=22, w_min=20)
        if f:
            mod = calc_mod(data.get(stat, 10))
            vals[f] = f"{mod:+d}"

    # ===================== COMBAT STATS =====================
    # HP Current: cx≈168 cy≈682 w≈101 (Text-tdhhLWTT-s)
    hp_cur = find_field(fields, 130, 210, 676, 688, w_min=80)
    if hp_cur: vals[hp_cur] = data['hp_current']

    # HP Max: cx≈435 cy≈681 w≈101 (Text-_6AiBiNnQ1)
    hp_max = find_field(fields, 400, 470, 676, 688, w_min=80)
    if hp_max: vals[hp_max] = data['hp_max']

    # HP Temp: cx≈340 cy≈698 w≈88 (Text-2GuMnSt7AS)
    hp_tmp = find_field(fields, 320, 360, 693, 703, w_min=75)
    if hp_tmp: vals[hp_tmp] = ''

    # AC: cx≈547 cy≈634 w≈44 (Text-FtVU38fLiT)
    ac = find_field(fields, 530, 560, 628, 640, w_min=35, w_max=55)
    if ac: vals[ac] = data['ac']

    # Speed: cx≈263 cy≈634 w≈37 (Text-iXzJ8sS_B6)
    spd = find_field(fields, 248, 278, 628, 640, w_min=28, w_max=45)
    if spd: vals[spd] = data['speed']

    # Initiative: cx≈357 cy≈634 w≈42 (Text-nl0Bfvd1qZ)
    ini = find_field(fields, 340, 375, 628, 640, w_min=32, w_max=50)
    if ini: vals[ini] = data['initiative']

    # Hit Dice: cx≈451 cy≈634 w≈37 (Text-XXlJcosGl7)
    hd = find_field(fields, 438, 465, 628, 640, w_min=28, w_max=45)
    if hd and data.get('hit_dice'):
        vals[hd] = data['hit_dice']

    # ===================== SKILLS =====================
    # Modifier fields at cx≈142, w≈18 (NOT ability score fields which have w≈23)
    skill_mods = sorted(
        [(n, f) for n, f in fields.items()
         if f['type'] == '/Tx' and 130 <= f['cx'] <= 155
         and 170 <= f['cy'] <= 595 and f['w'] <= 20],
        key=lambda x: -x[1]['cy']
    )
    # Checkboxes at cx≈128
    skill_cbs = sorted(
        [(n, f) for n, f in fields.items()
         if f['type'] == '/Btn' and 120 <= f['cx'] <= 135
         and 170 <= f['cy'] <= 595],
        key=lambda x: -x[1]['cy']
    )
    # Name fields at cx≈36, w≈18 (NOT ability score fields which have w≈23)
    skill_names = sorted(
        [(n, f) for n, f in fields.items()
         if f['type'] == '/Tx' and 25 <= f['cx'] <= 45
         and 170 <= f['cy'] <= 595 and f['w'] <= 20],
        key=lambda x: -x[1]['cy']
    )

    s_skills = sorted(data['skills'], key=lambda s: _skill_index(s['name']))

    for i, sk in enumerate(s_skills):
        # Modifier
        if i < len(skill_mods):
            vals[skill_mods[i][0]] = sk['mod']
        # Proficiency checkbox
        if sk['proficient'] and i < len(skill_cbs):
            vals[skill_cbs[i][0]] = '/Yes'
        # Skill name (only first N chars fit in narrow fields)
        if i < len(skill_names):
            name_short = sk['name'].split('(')[0].strip()[:12]
            vals[skill_names[i][0]] = name_short

    # ===================== SAVING THROWS =====================
    # D&D 2024: ability mod fields ARE the save mod fields (same cx≈74/180)
    # No separate save mod fields exist. Proficient saves get the prof bonus
    # added to the ability mod — but the template uses the same field.
    # We already wrote ability mods above. For proficient saves, override
    # with the save-specific value.
    save_profs = data.get('save_profs', {})
    prof_val = int(data['prof_bonus'].replace('+', ''))

    # Right column: STR(cx≈180 cy≈624), CON(cx≈180 cy≈450), WIS(cx≈180 cy≈276)
    save_mod_right_pos = [('str', 170, 190, 618, 630),
                          ('con', 170, 190, 445, 455),
                          ('wis', 170, 190, 268, 282)]
    for stat, cx1, cx2, cy1, cy2 in save_mod_right_pos:
        if save_profs.get(stat):
            f = find_field(fields, cx1, cx2, cy1, cy2, h_min=12, h_max=22, w_min=20)
            if f:
                mod = calc_mod(data.get(stat, 10)) + prof_val
                vals[f] = f"{mod:+d}"

    # Left column: DEX(cx≈74 cy≈546), INT(cx≈74 cy≈429), CHA(cx≈74 cy≈283)
    save_mod_left_pos = [('dex', 65, 85, 542, 552),
                         ('int', 65, 85, 424, 435),
                         ('cha', 65, 85, 278, 290)]
    for stat, cx1, cx2, cy1, cy2 in save_mod_left_pos:
        if save_profs.get(stat):
            f = find_field(fields, cx1, cx2, cy1, cy2, h_min=12, h_max=22, w_min=20)
            if f:
                mod = calc_mod(data.get(stat, 10)) + prof_val
                vals[f] = f"{mod:+d}"

    # Note: D&D 2024 template has no separate save proficiency checkboxes.
    # Save proficiency is reflected in the modifier value directly.

    # ===================== WEAPON TABLE =====================
    # 6 rows × 4 columns. Cy: 569, 550, 530, 511, 492, 472
    # Name: cx≈280, Bonus: cx≈359, Damage: cx≈421, Notes: cx≈524
    weapon_cols = {
        'name': (265, 310),
        'bonus': (345, 375),
        'damage': (410, 440),
        'notes': (510, 540),
    }
    attacks = data.get('attacks', [])

    # For each column, get fields sorted by cy desc
    # Actual widths: name w≈104, bonus w≈43, damage w≈74, notes w≈124
    wep_name = sorted(
        [(n, f) for n, f in fields.items()
         if f['type'] == '/Tx' and 265 <= f['cx'] <= 310
         and 465 <= f['cy'] <= 575 and f['w'] > 80 and f['w'] < 130],
        key=lambda x: -x[1]['cy']
    )
    wep_bonus = sorted(
        [(n, f) for n, f in fields.items()
         if f['type'] == '/Tx' and 345 <= f['cx'] <= 375
         and 465 <= f['cy'] <= 575 and f['w'] > 25 and f['w'] < 60],
        key=lambda x: -x[1]['cy']
    )
    wep_damage = sorted(
        [(n, f) for n, f in fields.items()
         if f['type'] == '/Tx' and 410 <= f['cx'] <= 440
         and 465 <= f['cy'] <= 575 and f['w'] > 50 and f['w'] < 100],
        key=lambda x: -x[1]['cy']
    )

    for i, atk in enumerate(attacks):
        if i < len(wep_name):
            vals[wep_name[i][0]] = atk['name']
        if i < len(wep_bonus):
            b = atk['bonus']
            if b.lower() not in ['automático', 'automatico', 'auto']:
                if not b.startswith('+') and not b.startswith('-'):
                    b = '+' + b
            vals[wep_bonus[i][0]] = b
        if i < len(wep_damage):
            dmg = atk['damage']
            if atk.get('type'):
                dmg += f" {atk['type']}"
            vals[wep_damage[i][0]] = dmg

    # ===================== FEATURES (big paragraph, right side) =====================
    # Paragraph-SIZoKloBpN: cx≈316 cy≈324 w≈176 h≈204 (large area)
    feat_paras = sorted(
        [(n, f) for n, f in fields.items()
         if f['type'] == '/Tx' and 280 <= f['cx'] <= 360
         and 200 <= f['cy'] <= 400 and f['w'] > 150],
        key=lambda x: -x[1]['cy']
    )
    if feat_paras:
        feat_text = ''
        if data.get('features'):
            feat_text += data['features'][:300]
        if data.get('cantrips'):
            feat_text += f"\n\nTrucos ({data['cantrips']})"
        if feat_text:
            vals[feat_paras[0][0]] = feat_text

    # Second features paragraph (right side, below)
    feat_para2 = sorted(
        [(n, f) for n, f in fields.items()
         if f['type'] == '/Tx' and 470 <= f['cx'] <= 530
         and 200 <= f['cy'] <= 400 and f['w'] > 100],
        key=lambda x: -x[1]['cy']
    )
    if feat_para2:
        text = ''
        if data.get('proficiencies'):
            text += f"Competencias: {data['proficiencies']}"
        if text:
            vals[feat_para2[0][0]] = text

    # ===================== EQUIPMENT (bottom) =====================
    # Paragraph-LL7oZqO3Uq: cx≈112 cy≈83 w≈195 h≈50
    # Paragraph-IKYhFIWoCf: cx≈498 cy≈324 w≈176 h≈204
    equip_bottom = sorted(
        [(n, f) for n, f in fields.items()
         if f['type'] == '/Tx' and 50 <= f['cx'] <= 200
         and 50 <= f['cy'] <= 120 and f['w'] > 150],
        key=lambda x: -x[1]['cy']
    )
    if equip_bottom and data.get('equipment'):
        vals[equip_bottom[0][0]] = '\n'.join(data['equipment'][:12])

    equip_right = sorted(
        [(n, f) for n, f in fields.items()
         if f['type'] == '/Tx' and 470 <= f['cx'] <= 530
         and 100 <= f['cy'] <= 200 and f['w'] > 100],
        key=lambda x: -x[1]['cy']
    )
    if equip_right and data.get('equipment') and len(data['equipment']) > 12:
        vals[equip_right[0][0]] = '\n'.join(data['equipment'][12:])

    return vals


def build_page2_values(data, fields):
    vals = {}

    # ===================== SPELLCASTING HEADER =====================
    if data.get('class', '').lower() in ['mago', 'hechicero', 'clérigo', 'druida', 'bardo', 'paladín', 'brujo']:
        # Spellcasting ability: cx≈82 cy≈751 w≈105 (Text-UPSPRKLy8W)
        sa = find_field(fields, 55, 110, 745, 758, w_min=80)
        if sa: vals[sa] = 'Inteligencia'

        # Spell mod: cx≈34 cy≈716 w≈27 (Text-OTOlimUkBI)
        sm = find_field(fields, 20, 50, 710, 722, w_min=20, w_max=35)
        if sm:
            int_mod = calc_mod(data.get('int', 10))
            vals[sm] = f"{int_mod:+d}"

        # Save DC: cx≈30 cy≈688 w≈33 (Text-toCN624mE4)
        dc = find_field(fields, 20, 45, 682, 695, w_min=25, w_max=40)
        if dc:
            dc_val = 8 + calc_mod(data.get('int', 10)) + 2
            vals[dc] = str(dc_val)

        # Spell attack: cx≈30 cy≈660 w≈33 (Text-HcDxGuRb5n)
        atk = find_field(fields, 20, 45, 654, 668, w_min=25, w_max=40)
        if atk:
            atk_val = calc_mod(data.get('int', 10)) + 2
            vals[atk] = f"{atk_val:+d}"

    # ===================== BACKGROUND / ASPECT =====================
    # cx≈500 cy≈708 (right side top)
    aspecto = find_field(fields, 430, 560, 690, 730, w_min=100, h_min=40)
    if aspecto and data.get('background'):
        vals[aspecto] = data['background'][:300]

    # ===================== HISTORY / PERSONALITY =====================
    # cx≈500 cy≈417 (right side, large area)
    hist = find_field(fields, 430, 560, 350, 500, w_min=100, h_min=50)
    if hist:
        parts = []
        parts.append(f"Cordura: {data.get('sanity_current', '?')}/{data.get('sanity_max', '?')}")
        if data.get('sanity_traumas') and data['sanity_traumas'] not in ('', chr(8212)):
            parts.append(f"Traumas: {data['sanity_traumas']}")
        vals[hist] = '\n'.join(parts)

    # ===================== LANGUAGES & PROFICIENCIES =====================
    # cx≈500 cy≈276
    lang = find_field(fields, 430, 560, 240, 300, w_min=100, h_min=30)
    if lang and data.get('proficiencies'):
        vals[lang] = data['proficiencies'][:200]

    # ===================== EQUIPMENT PAGE 2 =====================
    # cx≈500 cy≈170
    equip = find_field(fields, 430, 560, 130, 210, w_min=100, h_min=40)
    if equip and data.get('equipment'):
        vals[equip] = '\n'.join(data['equipment'][:10])

    # ===================== SPELL SLOTS =====================
    # Level 1 max & used: common fields on spellcasting page
    # Look for fields in expected slot area
    s1_max = find_field(fields, 340, 380, 573, 590, w_min=20)
    if s1_max: vals[s1_max] = '4'
    s1_used = find_field(fields, 280, 310, 573, 590, w_min=20)
    if s1_used: vals[s1_used] = '0'

    # ===================== CANTRIPS & SPELLS =====================
    # Spell list rows: left(cx≈97 w≈108), right(cx≈172 w≈33)
    # Row 1 (cy≈589): Cantrips, Row 2 (cy≈570) onwards: spells
    spell_names = sorted(
        [(n, f) for n, f in fields.items()
         if f['type'] == '/Tx' and 85 <= f['cx'] <= 115
         and 170 <= f['cy'] <= 595 and 95 <= f['w'] <= 130],
        key=lambda x: -x[1]['cy']
    )
    spell_notes = sorted(
        [(n, f) for n, f in fields.items()
         if f['type'] == '/Tx' and 160 <= f['cx'] <= 185
         and 170 <= f['cy'] <= 595 and 25 <= f['w'] <= 40],
        key=lambda x: -x[1]['cy']
    )

    # Row 0 (cy≈589): Cantrips
    if spell_names and data.get('cantrips'):
        vals[spell_names[0][0]] = data['cantrips']

    # Row 1+ (cy≈570 to cy≈170): Prepared spells
    if data.get('spells'):
        spells_list = [s.strip() for s in data['spells'].split(',')]
        for i, sp in enumerate(spells_list):
            ri = i + 1  # skip cantrip row
            if ri < len(spell_names):
                vals[spell_names[ri][0]] = sp[:25]
            if ri < len(spell_notes):
                vals[spell_notes[ri][0]] = 'Preparado'

    return vals


def _skill_index(name):
    norm = name.split('(')[0].strip().lower()
    for i, s in enumerate(SKILL_ORDER_ES):
        if norm == s or s.startswith(norm) or norm.startswith(s):
            return i
    return 999


def generate_pdf(data):
    reader = PdfReader(str(TEMPLATE))
    writer = PdfWriter()

    p1_fields = get_page_fields(reader, 0)
    p2_fields = get_page_fields(reader, 1)

    p1_vals = build_page1_values(data, p1_fields)
    p2_vals = build_page2_values(data, p2_fields)

    # Normalize accented chars for PDF font compatibility
    def asciify(v):
        if isinstance(v, str):
            if any(ord(c) > 127 for c in v) and not v.startswith('/'):
                nfkd = unicodedata.normalize('NFKD', v)
                return nfkd.encode('ASCII', 'ignore').decode('ASCII')
        return v
    p1_vals = {k: asciify(v) for k, v in p1_vals.items()}
    p2_vals = {k: asciify(v) for k, v in p2_vals.items()}

    writer.append(reader)
    writer.set_need_appearances_writer()

    writer.update_page_form_field_values(writer.pages[0], p1_vals)
    writer.update_page_form_field_values(writer.pages[1], p2_vals)

    # Manually set checkbox values: pypdf doesn't set checkboxes reliably
    from pypdf.generic import NameObject
    all_vals = {**p1_vals, **p2_vals}
    for pg in [writer.pages[0], writer.pages[1]]:
        for annot_ref in pg.get('/Annots', []):
            obj = annot_ref.get_object()
            name = str(obj.get('/T', ''))
            ft = str(obj.get('/FT', ''))
            # Try direct set for all checkboxes that should be marked
            if ft == '/Btn' and name in all_vals:
                desired = str(all_vals[name])
                if desired == '/Yes':
                    obj[NameObject('/V')] = NameObject('/Yes')
                    obj[NameObject('/AS')] = NameObject('/Yes')

    name_part = data.get('name', 'personaje').replace(' ', '_').replace(chr(8212), '-')
    output = JUGADORES / f"{name_part}.pdf"

    with open(output, 'wb') as f:
        writer.write(f)
    return output


def main():
    if not TEMPLATE.exists():
        print(f"ERROR: No se encuentra la plantilla en:\n{TEMPLATE}")
        sys.exit(1)

    # Only process the Mago character
    md_files = sorted(JUGADORES.glob("*.md"))
    if not md_files:
        print(f"No se encontraron .md en {JUGADORES}")
        return

    # Find Mago file
    mago_file = None
    for f in md_files:
        if 'mago' in f.name.lower():
            mago_file = f
            break

    if not mago_file:
        print("No se encontró el archivo del Mago")
        # Fallback: first file
        mago_file = md_files[0]

    print(f"Leyendo: {mago_file.name}")
    data = parse_character(mago_file)
    output = generate_pdf(data)
    print(f"  -> Generado: {output.name}")
    print("  -> Campo de nombre dejado VACÍO (jugadores lo rellenan)")


if __name__ == '__main__':
    main()
