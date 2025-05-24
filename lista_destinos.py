from camelot.io import read_pdf
import pdfplumber
import pandas as pd

PDF_PATH = 'listado0.pdf'
CSV_OUT = 'vacantes.csv'

PREFIXES = (
    'MINISTERIO', 'AGENCIA', 'JEFATURA', 'ORGANISMO', 'CONFEDERACION',
    'INSTITUTO', 'FONDO', 'MUTUALIDAD', 'TESORERIA', 'CONSEJO',
    'BIBLIOTECA', 'CENTRO', 'ENTIDAD', 'GERENCIA', 'MUSEO',
    'OFICINA', 'S.GRAL', 'COMISION', 'MANCOMUNIDAD'
)


def extract_ministerios(pdf_path):
    print("Extraer tablas")
    ministerios = {}
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            for line in page.extract_text().split('\n'):
                if any(line.startswith(pref) for pref in PREFIXES):
                    ministerios[str(i)] = line.strip()
                    break
    return ministerios, len(pdf.pages)


def parse_tables(tables, ministerios, page):
    """
    Intento de parseo de las tablas extraídas.
    Retorna lista de dicts (registros) o [] si no puede encontrar columnas esperadas.
    """
    registros = []
    for table in tables:
        df = table.df
        # primer fila = header real
        header = df.iloc[0].tolist()
        df = df[1:].copy()
        df.columns = header

        cols = df.columns.tolist()
        cd_col     = next((c for c in cols if 'CENTRO DIRECTIVO' in c), None)
        prov_col   = next((c for c in cols if 'PROVINCIA' in c),       None)
        puesto_col = next((c for c in cols if 'PUESTO DE TRABAJO' in c),None)
        espec_col  = next((c for c in cols if 'ESPECÍFICO' in c),      None)

        if not all([cd_col, prov_col, puesto_col, espec_col]):
            return []

        for _, row in df.iterrows():
            # descomponemos cada campo multi-línea
            cd_parts     = row[cd_col].split('\n')
            prov_parts   = row[prov_col].split('\n')
            puesto_parts = row[puesto_col].split('\n')
            espec_parts  = row[espec_col].split('\n')

            registros.append({
                'MINISTERIO': ministerios.get(str(page), ''),
                'CDIR':       cd_parts[0].strip()   if len(cd_parts) > 0 else '',
                'CDES':       cd_parts[1].strip()   if len(cd_parts) > 1 else '',
                'PROVINCIA':  prov_parts[0].strip() if len(prov_parts) > 0 else '',
                'LOCALIDAD':  prov_parts[1].strip() if len(prov_parts) > 1 else '',
                'PUESTO':     puesto_parts[0].strip() if len(puesto_parts) > 0 else '',
                'CPUESTO':    puesto_parts[1].strip() if len(puesto_parts) > 1 else '',
                'ESPECIFICO': espec_parts[1].strip() if len(espec_parts) > 1 else '',
            })
    return registros

def main():
    ministerios, total_pages = extract_ministerios(PDF_PATH)
    all_records = []

    for page in range(1, total_pages + 1):
        # Primer intento con lattice
        tables   = read_pdf(PDF_PATH, pages=str(page), flavor='lattice')
        registros = parse_tables(tables, ministerios, page)

        # Si falla, reintenta con stream
        if not registros:
            tables   = read_pdf(PDF_PATH, pages=str(page), flavor='stream')
            registros = parse_tables(tables, ministerios, page)

        all_records.extend(registros)

    df_out = pd.DataFrame(
        all_records,
        columns=[
            'MINISTERIO','CDIR','CDES',
            'PROVINCIA','LOCALIDAD',
            'PUESTO','CPUESTO','ESPECIFICO'
        ]
    )
    df_out.to_csv(CSV_OUT, sep=";", index=False, encoding='utf-8-sig')
    print(f"Se ha generado '{CSV_OUT}' con {len(df_out)} registros.")

if __name__ == '__main__':
    main()