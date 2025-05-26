import tabula
import pdfplumber
import pandas as pd
import re

PDF_PATH = 'listado.pdf'
CSV_OUT = 'vacantes.csv'

PREFIXES = (
    'MINISTERIO', 'AGENCIA', 'JEFATURA', 'ORGANISMO', 'CONFEDERACION',
    'INSTITUTO', 'FONDO', 'MUTUALIDAD', 'TESORERIA', 'CONSEJO',
    'BIBLIOTECA', 'CENTRO', 'ENTIDAD', 'GERENCIA', 'MUSEO',
    'OFICINA', 'S.GRAL', 'COMISION', 'MANCOMUNIDAD'
)
PUESTO_PREFIXES = ('AUXILIAR', 'GESTOR', 'SECRETARIO', 'JEFE', 'TECNICO')


def extract_ministerios(pdf_path):
    """
    Extrae la línea de ministerio/organismo antes de cada tabla.
    Devuelve una lista de cadenas, una por cada tabla en el PDF.
    """
    ministerios = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            lines = [l.strip() for l in (page.extract_text() or '').split('\n') if l.strip()]
            for idx, line in enumerate(lines):
                if any(line.startswith(pref + ' ') or line == pref for pref in PREFIXES):
                    if idx + 1 < len(lines) and lines[idx + 1].startswith('PUESTO'):
                        ministerios.append(line)
    return ministerios


def leer_tablas(pdf_path, num_pages):
    """
    Lee tablas por página, intentando primero lattice y luego stream.
    Devuelve una lista de listas de DataFrames, uno por página.
    """
    tables_by_page = []
    for p in range(1, num_pages + 1):
        try:
            dfs = tabula.read_pdf(pdf_path, pages=p, multiple_tables=True, lattice=True)
        except:
            dfs = []
        if not dfs:
            dfs = tabula.read_pdf(pdf_path, pages=p, multiple_tables=True, stream=True)
        tables_by_page.append(dfs)
    return tables_by_page


def normalize_lines(raw):
    """
    Divide el texto raw en líneas y separa fusiones de puesto pegadas.
    """
    parts = [l.strip() for l in re.split(r'[\r\n]+', raw) if l.strip()]
    # Tras dividir en líneas y hacer strip():
    clean = [l for l in parts if not re.fullmatch(r'\d{1,2}', l)]
    output = []
    for l in parts:
        split_done = False
        for pref in PUESTO_PREFIXES:
            idx = l.find(pref)
            if idx > 0 and not l.startswith(pref):
                output.append(l[:idx].strip())
                output.append(l[idx:].strip())
                split_done = True
                break
        if not split_done:
            output.append(l)
    return output


def parse_table(df, ministerio):
    """
    Procesa un DataFrame de una página combinada y extrae registros.
    """
    records = []
    for _, row in df.iterrows():
        raw = "\n".join(str(row[c]) for c in df.columns if pd.notnull(row[c]))
        # Saltar encabezado
        if 'PUESTO' in raw and 'NÚMERO' in raw:
            continue
        # Salario
        m_sal = re.search(r"\d{1,3}(?:\.\d{3})*,\d{2}", raw)
        sal = m_sal.group(0) if m_sal else ''
        # Normalizar
        lines = normalize_lines(raw)
        # Limpiar
        clean = [l for l in lines if not l.isdigit() and l != sal]
        # Campos fijos
        cdir = clean[0] if len(clean) > 0 else ''
        cdes = clean[1] if len(clean) > 1 else ''
        provincia = clean[2] if len(clean) > 2 else ''
        localidad = ''
        cp = ''
        # Detectar localidad+cp fusionados
        for l in clean[3:]:
            m = re.match(r"^(.+?)(\d{6,})$", l)
            if m:
                localidad = m.group(1).strip()
                cp = m.group(2)
                break
        # Fallback cp: primer número puro >=6 dígitos
        if not cp:
            for l in lines:
                cp = next((l for l in clean if re.fullmatch(r'\d{6,}', l)), '')
        # Fallback localidad: primera clean con coma
        if not localidad:
            for l in clean[3:]:
                if ',' in l:
                    localidad = re.sub(r"\d+$", "", l).strip()
                    break
        # Fallback localidad alt: elemento 3 de clean
        if not localidad and len(clean) > 3:
            localidad = clean[3]
        # Puesto
        puesto = ''
        for l in clean[2:]:
            if any(l.startswith(pref) for pref in PUESTO_PREFIXES):
                puesto = l
                break
        records.append({
            'MINISTERIO': ministerio,
            'CDIR':       cdir,
            'CDES':       cdes,
            'PROVINCIA':  provincia,
            'LOCALIDAD':  localidad,
            'PUESTO':     puesto,
            'CPUESTO':    cp,
            'ESPECIFICO': sal
        })
    return records


if __name__ == '__main__':
    ministerios = extract_ministerios(PDF_PATH)
    with pdfplumber.open(PDF_PATH) as pdf:
        num_pages = len(pdf.pages)
    tables_by_page = leer_tablas(PDF_PATH, num_pages)
    all_records = []
    for idx, ministerio in enumerate(ministerios):
        if idx < len(tables_by_page):
            dfs = tables_by_page[idx]
            if not dfs:
                continue
            # Concatenar todas las tablas de la página
            df_all = pd.concat(dfs, ignore_index=True)
            recs = parse_table(df_all, ministerio)
            all_records.extend(recs)
    df_out = pd.DataFrame(
        all_records,
        columns=['MINISTERIO', 'CDIR', 'CDES', 'PROVINCIA', 'LOCALIDAD', 'PUESTO', 'CPUESTO', 'ESPECIFICO']
    )
    df_out.to_csv(CSV_OUT, sep=';', index=False, encoding='utf-8-sig')
    print(f"Se ha generado '{CSV_OUT}' con {len(df_out)} registros.")
