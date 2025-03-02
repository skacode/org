import sys

def replace_in_file(file_path, string_to_replace, string_replacement):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        if string_to_replace in content:
            content = content.replace(string_to_replace, string_replacement)
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(content)
            print("Reemplazo realizado correctamente.")
        else:
            print("No se encontró la cadena a reemplazar. No se hicieron cambios.")

    except Exception as e:
        print(f"Error al modificar el archivo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python replace_vuln.py <file_path> <string_to_replace> <string_replacement>")
        sys.exit(1)

    file_path = sys.argv[1]
    string_to_replace = sys.argv[2]
    string_replacement = sys.argv[3]

    replace_in_file(file_path, string_to_replace, string_replacement)
