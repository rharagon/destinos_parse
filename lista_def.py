import PyPDF2
import os
import csv
import re

def read_pdf(file_path):
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for p in reader.pages:
            # extrae texto plano
            txt = p.extract_text()
            if txt:
                text += txt + "\n"
    return text

def extract_definitivos(text):
    """
    Extrae líneas con formato:
      ***DNI** APELLIDOS Y NOMBRE. P1 A1 E1 P2 A2 E2 TPS ORDEN
    y devuelve una lista de listas con los 10 campos.
    """
    pattern = re.compile(
        r'^\*{3}(?P<dni>\d+)\*{2}\s+'                    # ***DNI**
        r'(?P<apellidos>[^.]+?)\.\s+'                    # Apellidos y nombre (hasta el punto)
        r'(?P<p1>\d{1,2}(?:,\d{1,2})?)\s+'               # Punt.Dir -Parte1
        r'(?P<a1>\d+)\s+'                                # Aciertos-Parte1
        r'(?P<e1>\d+)\s+'                                # Errores-Parte1
        r'(?P<p2>\d{1,2}(?:,\d{1,2})?)\s+'               # Punt.Dir -Parte2
        r'(?P<a2>\d+)\s+'                                # Aciertos-Parte2
        r'(?P<e2>\d+)\s+'                                # Errores-Parte2
        r'(?P<tps>\d{1,2}(?:,\d{1,2})?)\s+'              # TPS
        r'(?P<orden>\d+)$'                               # Orden
    )
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if not m:
            continue
        rows.append([
            f'***{m.group("dni")}**',
            m.group("apellidos").strip(),
            m.group("p1"),
            m.group("a1"),
            m.group("e1"),
            m.group("p2"),
            m.group("a2"),
            m.group("e2"),
            m.group("tps"),
            m.group("orden")
        ])
    return rows

def save_definitivos_csv(rows, output_path):
    header = [
        "DNI",
        "Apellidos y nombre",
        "Punt.Dir -Parte1",
        "Aciertos-Parte1",
        "Errores-Parte1",
        "Punt.Dir -Parte2",
        "Aciertos-Parte2",
        "Errores-Parte2",
        "TPS",
        "Orden"
    ]
    dirpath = os.path.dirname(output_path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)

if __name__ == "__main__":
    pdf_path = input("Ruta al PDF: ").strip()
    print("Leyendo PDF…")
    text = read_pdf(pdf_path)
    print("Buscando líneas con 10 campos…")
    filas = extract_definitivos(text)
    if not filas:
        print("No se encontró ninguna línea válida.")
        print(text)
    else:
        salida = "definitivos.csv"
        save_definitivos_csv(filas, salida)
        print(f"CSV generado en {salida} con {len(filas)} registros.")
