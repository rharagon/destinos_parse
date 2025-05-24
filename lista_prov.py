import PyPDF2
import os
import csv  # Importa el módulo para manejar CSV
import re

def read_pdf(file_path):
    print("Reading PDF file...")  # Verifica si se llama a esta función
    try:
        with open(file_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            print("PDF file read successfully.")  # Confirma que se leyó el PDF
            print("Extracted text from PDF:")  # Imprime el texto extraído
            print(text)  # Muestra todo el texto extraído
            return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None


def extract_scores(text):
    """
    Busca solo las líneas con formato:
    APELLIDO1 APELLIDO2, NOMBRE ***DNI** PUNTUACIÓN
    y devuelve una lista de tuplas:
    (apellido1, apellido2, nombre, dni_ofuscado, puntuacion_float)
    """
    print("Extracting scores...")
    # Patrón sin comillas
    pattern = re.compile(
        r'(?P<apellido1>[^ ,*]+)\s+'        # primer apellido
        r'(?P<apellido2>[^,]+),\s*'         # segundo apellido + coma
        r'(?P<nombre>[^*]+?)\s+'            # nombre (hasta los asteriscos)
        r'\*{3}(?P<dni>\d+)\*{2}\s+'        # ***DNI**
        r'(?P<score>\d{1,2},\d{2})'         # puntuación
    , re.UNICODE)

    scores = []
    for line in text.splitlines():
        raw = line.strip()
        if not raw:
            continue
        # Quita comillas al inicio/fin para que casen las líneas sin ellas
        line_clean = raw.strip('"')
        print(f"→ intentando con: {line_clean}")
        m = pattern.match(line_clean)
        if not m:
            continue
        print(f"✓ match: {line_clean}")
        a1 = m.group('apellido1')
        a2 = m.group('apellido2')
        nombre = m.group('nombre').strip()
        dni_ofus = f'***{m.group("dni")}**'
        score = float(m.group('score').replace(',', '.'))
        scores.append((a1, a2, nombre, dni_ofus, score))

    scores.sort(key=lambda x: x[4], reverse=True)
    print(f"Extraídos {len(scores)} registros válidos.")
    return scores

def export_scores_to_csv(scores, output_file):
    """
    Escribe un CSV con:
    Apellido1,Apellido2,Nombre,DNI_ofuscado,Puntuación
    sin comillas en la puntuación (usar coma decimal).
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        # Cabecera
        f.write("Apellido1;Apellido2;Nombre;DNI_ofuscado;Puntuación\n")
        for a1, a2, nombre, dni, score in scores:
            # formateamos la puntuación con coma decimal
            score_str = f"{score:.2f}".replace('.', ',')
            # unimos manualmente con comas, sin quoting
            f.write(f"{a1};{a2};{nombre};{dni};{score_str}\n")

def export_to_csv(scores_table, output_file):
    print(f"Exporting data to {output_file}...")  # Mensaje de inicio de exportación
    if not scores_table:
        print("No data to export. The scores table is empty.")  # Mensaje si no hay datos
        return
    try:
        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "DNI", "Score"])  # Escribe la cabecera
            writer.writerows(scores_table)  # Escribe los datos
        print(f"Data successfully exported to {output_file}.")
    except Exception as e:
        print(f"Error exporting data to CSV: {e}")

def export_text_to_csv(text, output_file):
    print(f"Exporting text to {output_file}...")  # Mensaje de inicio de exportación
    try:
        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Line"])  # Escribe la cabecera
            for line in text.splitlines():
                writer.writerow([line])  # Escribe cada línea como una fila
        print(f"Text successfully exported to {output_file}.")
    except Exception as e:
        print(f"Error exporting text to CSV: {e}")

if __name__ == "__main__":
    pdf_path = input("Ruta al PDF: ")
    pdf_text = read_pdf(pdf_path)
    if pdf_text:
        scores = extract_scores(pdf_text)
        output_csv = os.path.join(os.path.dirname(pdf_path), "scores_filtrados.csv")
        export_scores_to_csv(scores, output_csv)
        print(f"CSV generado en {output_csv} con {len(scores)} registros.")
