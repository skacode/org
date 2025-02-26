#!/usr/bin/env python3
import argparse
import os
import requests
import sys

def main():
    parser = argparse.ArgumentParser(description="Subir reporte a DefectDojo")
    parser.add_argument("--scan_type", required=True, help="Tipo de scan (por ejemplo, 'SpotBugs Scan')")
    parser.add_argument("--file_path", required=True, help="Ruta del archivo a subir")
    parser.add_argument("--engagement_id", required=True, help="ID del engagement en DefectDojo")
    parser.add_argument("--product_id", required=False, help="ID del producto en DefectDojo (opcional)")
    args = parser.parse_args()

    API_URL = "http://localhost:9090/api/v2"
    endpoint = f"{API_URL}/import-scan/"

    api_key = os.environ.get("DEFECTDOJO_API_KEY")
    if not api_key:
        print("Error: La variable de entorno DEFECTDOJO_API_KEY no está definida.")
        sys.exit(1)

    headers = {
        "Authorization": f"Token {api_key}"
    }

    print(f"Subiendo reporte de {args.scan_type}...")

    data = {
        "scan_type": args.scan_type,
        "engagement": args.engagement_id
    }
    
    if args.product_id:
        data["product"] = args.product_id

    try:
        with open(args.file_path, "rb") as file_obj:
            files = {
                "file": file_obj
            }
            response = requests.post(endpoint, headers=headers, data=data, files=files)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {args.file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error al subir el reporte: {e}")
        sys.exit(1)

    if response.status_code >= 200 and response.status_code < 300:
        print("Reporte subido exitosamente.")
    else:
        print(f"Error al subir el reporte. Código de estado: {response.status_code}")
        print("Respuesta:", response.text)
        sys.exit(1)

if __name__ == "__main__":
    main()
