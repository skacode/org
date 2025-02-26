#!/usr/bin/env python3
import os
import requests
import sys
import subprocess
import time

def check_and_start_defectdojo(api_url):
    test_url = f"{api_url}/products/?name=check"
    try:
        print("Verificando conexión con DefectDojo...")
        response = requests.get(test_url, timeout=5)
        response.raise_for_status()
        print("DefectDojo ya está corriendo.")
    except requests.exceptions.RequestException as e:
        print("DefectDojo no está corriendo:", e)
        print("Intentando iniciar DefectDojo...")
        # Comando para iniciar DefectDojo; ajústalo según tu entorno y imagen
        command = ["docker", "run", "-d", "--name", "defectdojo", "-p", "9090:9090", "defectdojo/defectdojo:latest"]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print("Error al iniciar DefectDojo:", result.stderr.decode())
            sys.exit(1)
        else:
            print("DefectDojo iniciado, esperando a que se estabilice...")
        # Esperar unos segundos para que el servicio esté disponible
        time.sleep(10)
        # Reintentar la conexión
        try:
            response = requests.get(test_url, timeout=5)
            response.raise_for_status()
            print("DefectDojo está ahora corriendo.")
        except Exception as e:
            print("DefectDojo sigue sin estar disponible:", e)
            sys.exit(1)

def main():
    project_name = os.environ.get("INPUT_PROJECT_NAME")
    api_key = os.environ.get("DEFECTDOJO_API_KEY")
    api_url = os.environ.get("API_URL", "http://localhost:9090/api/v2")

    if not project_name or not api_key:
        print("Error: se deben definir INPUT_PROJECT_NAME y DEFECTDOJO_API_KEY en las variables de entorno.")
        sys.exit(1)

    check_and_start_defectdojo(api_url)

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }

    print(f"Verificando si el producto '{project_name}' existe...")
    get_product_url = f"{api_url}/products/?name={project_name}"
    product_response = requests.get(get_product_url, headers=headers)
    product_response.raise_for_status()
    product_data = product_response.json()
    product_count = product_data.get("count", 0)

    if product_count == 0:
        print("Producto no encontrado. Creando...")
        create_product_url = f"{api_url}/products/"
        product_payload = {
            "name": project_name,
            "prod_type": 1,
            "description": "Producto creado automáticamente por Pipeline"
        }
        new_product = requests.post(create_product_url, headers=headers, json=product_payload)
        new_product.raise_for_status()
        product_json = new_product.json()
        product_id = product_json.get("id")
    else:
        product_id = product_data.get("results", [{}])[0].get("id")
        print(f"Producto encontrado con ID: {product_id}")

    print("Verificando si existe engagement para el producto...")
    get_engagement_url = f"{api_url}/engagements/?product={product_id}"
    engagement_response = requests.get(get_engagement_url, headers=headers)
    engagement_response.raise_for_status()
    engagement_data = engagement_response.json()
    engagement_count = engagement_data.get("count", 0)

    if engagement_count == 0:
        print("Engagement no encontrado. Creando...")
        create_engagement_url = f"{api_url}/engagements/"
        engagement_payload = {
            "product": product_id,
            "name": "CI/CD Engagement",
            "status": "In Progress"
        }
        new_engagement = requests.post(create_engagement_url, headers=headers, json=engagement_payload)
        new_engagement.raise_for_status()
        engagement_json = new_engagement.json()
        engagement_id = engagement_json.get("id")
    else:
        engagement_id = engagement_data.get("results", [{}])[0].get("id")
        print(f"Engagement encontrado con ID: {engagement_id}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as output_file:
            output_file.write(f"product_id={product_id}\n")
            output_file.write(f"engagement_id={engagement_id}\n")
    else:
        print("GITHUB_OUTPUT no está definido. Resultados:")
        print(f"product_id={product_id}")
        print(f"engagement_id={engagement_id}")

if __name__ == "__main__":
    main()
