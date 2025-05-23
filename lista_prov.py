import PyPDF2
import os
import csv  # Importa el módulo para manejar CSV

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
    print("Extracting scores...")  # Verifica si se llama a esta función
    if not text.strip():
        print("No text found in the PDF.")  # Mensaje si el PDF está vacío
        return []
    
    # Procesa el texto para extraer datos
    scores = []
    lines = text.splitlines()
    print("Lines extracted from PDF:")  # Imprime las líneas extraídas
    for line in lines:
        print(f"Line: {line}")  # Imprime cada línea para depuración
        parts = line.split()
        if len(parts) >= 3:  # Asegúrate de que haya al menos 3 columnas (nombre, DNI, puntuación)
            try:
                name = " ".join(parts[:-2])  # Nombre y apellidos
                dni = parts[-2]  # DNI
                score = float(parts[-1])  # Puntuación
                scores.append((name, dni, score))
            except ValueError:
                print(f"Skipping line due to invalid score: {line}")  # Mensaje si la puntuación no es válida
                print(f"Parts: {parts}")  # Imprime las partes de la línea para depuración
                continue  # Ignora líneas donde la puntuación no sea un número
    
    # Ordena las puntuaciones en orden descendente
    scores.sort(key=lambda x: x[2], reverse=True)
    print(f"Extracted and sorted {len(scores)} scores.")  # Confirma cuántos registros se extrajeron y ordenaron
    return scores

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

if name == "main":
    pdf_path = input("Enter the path to the PDF file: ")
    pdf_text = read_pdf(pdf_path)
    if pdf_text:
        print("Exporting extracted text to CSV...")
        output_csv = os.path.join(os.path.dirname(file), "extracted_text.csv")
        export_text_to_csv(pdf_text, output_csv)
