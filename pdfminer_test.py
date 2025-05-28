#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrae la tabla de destinos de un PDF (BOE) usando pdfminer.six y vuelca un CSV
formato:
MINISTERIO;CDIR;CDES;PROVINCIA;LOCALIDAD;PUESTO;CPUESTO;ESPECIFICO
"""

import re, csv, sys, pathlib
from pdfminer.high_level import extract_text

PDF   = sys.argv[1] if len(sys.argv) > 1 else "listado.pdf"
OUT   = pathlib.Path(PDF).with_suffix(".csv")

# --------------------------------------------------------------------------
HEADER_WORDS = {
    'PUESTO', 'NÚMERO', 'CENTRO', 'DIRECTIVO/00.A.A', 'CENTRO DIRECTIVO/00.A.A',
    'CENTRO DE DESTINO', 'PROVINCIA', 'LOCALIDAD', 'PUESTO DE TRABAJO',
    'NIVEL', 'C.D.', 'C.', 'ESPECÍFICO', 'C. ESPECÍFICO', 'NIVEL C.D.'
}
MINISTRY_RE  = re.compile(r'^(MINISTERIO|AGENCIA|ORGANISMO|JEFATURA|INSTITUTO|CONSORCIO)', re.I)
CP_RE        = re.compile(r'^\d{7}$')
EURO_RE      = re.compile(r'^(\d+\.)*\d+,\d{2}$')     # 3.656,24  ó 589,76
DIGIT_RE     = re.compile(r'^\d+$')

def is_header(tok:str)->bool:
    return tok in HEADER_WORDS or DIGIT_RE.fullmatch(tok)

def find_especifico(tokens, idx, max_look=8):
    """devuelve el C. específico (float en str) buscando hacia delante"""
    for j in range(idx+1, min(idx+1+max_look, len(tokens))):
        if EURO_RE.fullmatch(tokens[j]):
            return tokens[j].replace('.', '').replace(',', '.')
    return ''

def build_row(ministry:str, cell_tokens:list, cp:str, espec:str):
    """
    cell_tokens ya sin cabeceras ni duplicados.
    último  = puesto
    penúlt. con ',' -> localidad, su anterior -> provincia
    lo que quede delante: cdir (1ª) + cdes (resto)
    """
    if len(cell_tokens) < 4:
        return None

    puesto = cell_tokens[-1]
    loc    = prov = ''
    # provincia / localidad
    for t in reversed(cell_tokens[:-1]):
        if not loc and ',' in t:
            loc = t
            continue
        if not prov:
            prov = t
            break
    if not prov:            # fila sin localidad explícita
        prov = loc or cell_tokens[-2]
    if not loc:
        loc = prov

    # CDIR & CDES
    cdir = cell_tokens[0]
    cdes = " ".join(cell_tokens[1:-2]) if len(cell_tokens) > 4 else ''

    return [ministry, cdir, cdes, prov, loc, puesto, cp, espec]

# --------------------------------------------------------------------------
text   = extract_text(PDF)
tokens = [t.strip() for t in text.splitlines() if t.strip()]

rows, buf, last_full = [], [], []
ministry = ''

i = 0
while i < len(tokens):
    tok = tokens[i]

    # 1. Cabecera de ministerio
    if MINISTRY_RE.match(tok):
        ministry = tok
        buf.clear()
        i += 1
        continue

    # 2. Código de puesto (7 dígitos)  → flush de fila
    if CP_RE.fullmatch(tok):
        cp     = tok
        espec  = find_especifico(tokens, i)
        # limpieza de buf
        clean  = [t for t in buf if not is_header(t)]
        # si la fila “hermana” solo trae el puesto reaprovechamos la info completa anterior
        if len(clean) < 4 and last_full:
            clean = last_full + clean
            # quitar duplicados conservando orden
            seen, tmp = set(), []
            for t in clean:
                if t not in seen:
                    tmp.append(t); seen.add(t)
            clean = tmp
        row = build_row(ministry, clean, cp, espec)
        if row:
            rows.append(row)
            last_full = clean[:]            # cache para la posible “hermana”
        buf.clear()
        i += 1
        continue

    # 3. Otros tokens: acumular
    if not is_header(tok):
        buf.append(tok)
    i += 1

# --------------------------------------------------------------------------
with OUT.open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    w.writerow(["MINISTERIO","CDIR","CDES","PROVINCIA","LOCALIDAD",
                "PUESTO","CPUESTO","ESPECIFICO"])
    w.writerows(rows)

print(f"OK – {len(rows)} filas escritas en {OUT}")
