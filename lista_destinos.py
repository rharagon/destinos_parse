import pdfplumber
import csv
import re

PDF_PATH = 'listado0.pdf'
CSV_OUT  = 'vacantes.csv'

# Lista de provincias en mayúsculas tal como aparecen en el PDF
PROVINCIAS = [
    'A CORUÑA','ALBACETE','ALICANTE','ALMERIA','ASTURIAS','AVILA',
    'BADAJOZ','BALEARES','BARCELONA','BURGOS','CACERES','CADIZ','CANTABRIA',
    'CASTELLON','CEUTA','CIUDAD REAL','CORDOBA','CUENCA','GIRONA','GRANADA',
    'GUADALAJARA','GIPUZCOA','HUELVA','HUESCA','JAEN','LA RIOJA',
    'LAS PALMAS','LEON','LLEIDA','LUGO','MADRID','MALAGA','MELILLA','MURCIA',
    'NAVARRA','OURENSE','PALENCIA','PONTEVEDRA','SALAMANCA','SANTA CRUZ DE TENERIFE',
    'SEGOVIA','SEVILLA','SORIA','TARRAGONA','TERUEL','TOLEDO','VALENCIA','VALLADOLID',
    'VIZCAYA','ZAMORA','ZARAGOZA'
]

# Prefijos que pueden arrancar un bloque de MINISTERIO/ENTIDAD
ENCABEZADOS = (
    'MINISTERIO','AGENCIA','JEFATURA','ORGANISMO','CONFEDERACION',
    'INSTITUTO','FONDO','MUTUALIDAD','TESORERIA','CONSEJO',
    'BIBLIOTECA','CENTRO','ENTIDAD','GERENCIA','MUSEO',
    'OFICINA','S.GRAL','COMISION','MANCOMUNIDAD'
)

with pdfplumber.open(PDF_PATH) as pdf, \
     open(CSV_OUT, 'w', newline='', encoding='utf-8-sig') as fout:

    writer = csv.DictWriter(fout,
        fieldnames=[
            'MINISTERIO','CDIR','CDES',
            'PROVINCIA','LOCALIDAD',
            'PUESTO','CPUESTO','ESPECIFICO'
        ],
        delimiter=';'
    )
    writer.writeheader()

    for page in pdf.pages:
        lines = page.extract_text().split('\n')
        i = 0
        current_min = ''

        while i < len(lines):
            line = lines[i].strip()

            # 1) Si es encabezado de sección, lo guardamos
            if any(line.startswith(pref) for pref in ENCABEZADOS):
                current_min = line
                i += 1
                continue

            # 2) Si es la primera línea de cabecera de la tabla
            if line.startswith('PUESTO CENTRO DIRECTIVO'):
                # Saltamos las dos filas de cabecera
                i += 2

                # 3) Procesamos bloques de 3 líneas hasta el próximo encabezado o fin
                while i + 2 < len(lines):
                    # Parada si encontramos un nuevo encabezado
                    if any(lines[i].startswith(pref) for pref in ENCABEZADOS):
                        break
                    num = lines[i+1].strip()
                    if not num.isdigit():
                        break

                    L1 = lines[i].strip()    # línea con CDIR, PROVINCIA, PUESTO, NIVEL
                    L3 = lines[i+2].strip()  # línea con CDES, LOCALIDAD, CÓDIGO, ESPECÍFICO

                    # --- Extraer CDIR y PUESTO ---
                    # Quitamos el nivel final (último token)
                    core1 = L1.rsplit(' ', 1)[0]

                    # Buscamos la provincia
                    provincia = ''
                    for prov in PROVINCIAS:
                        if f' {prov} ' in f' {core1} ':
                            provincia = prov
                            break

                    if provincia:
                        idx = core1.find(provincia)
                        cdir   = core1[:idx].strip()
                        puesto = core1[idx+len(provincia):].strip()
                    else:
                        cdir   = ''
                        puesto = ''

                    # --- Extraer CDES, LOCALIDAD, CPUESTO y ESPECÍFICO ---
                    toks = L3.split()
                    # Código = penúltimo token
                    cpuesto   = toks[-2] if len(toks) >= 2 else ''
                    especifico= toks[-1] if len(toks) >= 1 else ''

                    # CDES = hasta el '-' y la palabra que sigue
                    if '-' in toks:
                        dash = toks.index('-')
                        # incluimos el guión y el primer token tras él
                        cdes = ' '.join(toks[:dash+2])
                        # LOCALIDAD = el resto antes de código y específico
                        loc = toks[dash+2:-2]
                        localidad = ' '.join(loc).strip(',')
                    else:
                        cdes       = ''
                        localidad  = ''

                    writer.writerow({
                        'MINISTERIO': current_min,
                        'CDIR':       cdir,
                        'CDES':       cdes,
                        'PROVINCIA':  provincia,
                        'LOCALIDAD':  localidad,
                        'PUESTO':     puesto,
                        'CPUESTO':    cpuesto,
                        'ESPECIFICO': especifico,
                    })

                    i += 3
                continue

            # Si no es nada de lo anterior, avanzamos
            i += 1

print(f"Generado {CSV_OUT}")