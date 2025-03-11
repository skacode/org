# CI/CD - Security Pipeline with SpotBugs, Dependency Track, Trivy and ZAP

## Resumen del Despliegue

Este documento describe el pipeline de seguridad implementado para un proyecto en Kubernetes. La aplicación se despliega en el namespace `training`, y se valida mediante el uso de herramientas como Spotbugs, Dependency Track, Trivy, Zap, Kubeval y Kubesec.

## Estructura del Pipeline

El pipeline se divide en los siguientes pasos:

1. **Configuración de DefectDojo**: Se inicializa un producto en DefectDojo para centralizar los hallazgos de seguridad.
2. **Análisis de Dependencias con Dependency-Track**: Se genera un SBOM y se sube a Dependency-Track.
3. **Escaneo de Código Estático con SpotBugs**: Se analiza el código en busca de vulnerabilidades estáticas.
4. **Escaneo de Imagen Docker con Trivy**: Se identifican vulnerabilidades en la imagen Docker.
5. **Construcción y Publicación de Imagen Docker**: Se reconstruye y sube la imagen a Docker Hub.
6. **Despliegue en Kubernetes**: Se validan los manifiestos y se aplican en el cluster.
7. **Escaneo Dinámico con OWASP ZAP**: Se ejecuta un análisis de seguridad contra la aplicación desplegada.

## Herramientas de Validación

### Kubeval
Validación de la estructura de los manifiestos YAML de Kubernetes.
```sh
kubeval -d manifests-${{ inputs.project_name }}/
```

### Kubesec
Análisis de seguridad de los manifiestos.
```sh
kubesec scan manifests-${{ inputs.project_name }}/*.yaml | tee kubesec-output.json
```

### Trivy
Escaneo de la imagen Docker en busca de vulnerabilidades.
```sh
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ${{ github.workspace }}:/workspace \
  aquasec/trivy image --format json -o /workspace/trivy-report.json \
  ${{ inputs.docker_image }}:run-${{ github.run_number }}
```

### SpotBugs
Análisis de código estático con SpotBugs.
```sh
docker run --rm \
  -v ${{ github.workspace }}/${{ inputs.working_directory }}:/workspace \
  nemooudeis/spotbugs sh -c "spotbugs -textui -effort:max -xml:withMessages -output /workspace/spotbugsXml.xml /workspace/target/classes"
```

### OWASP ZAP
Escaneo de seguridad dinámico de la aplicación.
```sh
docker run --rm -v $(pwd):/zap/wrk:rw --network=host \
  -t zaproxy/zap-stable zap-baseline.py \
  -t ${{ inputs.app_url }} \
  -x zap-report.xml -m 2 || true
```

## Resultados de los Análisis

Los reportes generados se suben a DefectDojo:

```sh
python org/.github/scripts/uploadtodojo.py \
  --scan_type "Trivy Scan" \
  --file_path "${{ github.workspace }}/trivy-report.json" \
  --engagement_id "${{ needs.SetupDefectDojo.outputs.engagement_id }}" \
  --product_id "${{ needs.SetupDefectDojo.outputs.product_id }}"
```
## Problemas y Soluciones

### Problema: Dependency-Track no inicia automáticamente
**Solución:** Se verifica su estado y se inicia si es necesario.
```sh
if [ "$(docker ps -q -f name=dt-apiserver-1)" ]; then
  echo "Dependency-Track en ejecución."
else
  docker compose up -d
fi
```

### Problema: Kubernetes puede no estar corriendo
**Solución:** Se inicia Minikube si es necesario.
```sh
if kubectl cluster-info > /dev/null 2>&1; then
  echo "Kubernetes en ejecución."
else
  minikube start --driver=docker
fi
```

### Problema: DefectDojo no crea automáticamente un producto y engagement
**Solución:** Se inicia DefectDojo y se verifica si existe ya el nombre del producto que vamos a analizar el pipeline, si existe confirma que exista su engagement y si no lo crea. Si no existe el producto ni el engagement los crea.
```sh
if product_count == 0:
        print("Producto no encontrado. Creando...")
        create_product_url = f"{lista[0]}/products/"
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
    get_engagement_url = f"{lista[0]}/engagements/?product={product_id}"
    engagement_response = requests.get(get_engagement_url, headers=headers)
    engagement_response.raise_for_status()
    engagement_data = engagement_response.json()
    engagement_count = engagement_data.get("count", 0)
    if engagement_count == 0:
        print("Engagement no encontrado. Creando...")
        create_engagement_url = f"{lista[0]}/engagements/"
        engagement_payload = {
            "product": product_id,
            "name": "CI/CD Engagement",
            "status": "In Progress",
            "target_start": datetime.now().strftime('%Y-%m-%d'),
            "target_end": (datetime.now()+timedelta(days=30)).strftime('%Y-%m-%d'),
            "active": True
        }
        new_engagement = requests.post(create_engagement_url, headers=headers, json=engagement_payload)
        new_engagement.raise_for_status()
        engagement_json = new_engagement.json()
        engagement_id = engagement_json.get("id")
    else:
        engagement_id = engagement_data.get("results", [{}])[0].get("id")
        print(f"Engagement encontrado con ID: {engagement_id}")
```

### Problema: Demasiada repetición de código en la subida de findings a DefectDojo
**Solución:** Creamos un .py para repetir la subida de archivos con los findings de cada herramienta a DefectDojo sin necesidad de repetir el mismo código.
```sh
Ver en https://github.com/skacode/org/blob/main/.github/scripts/uploadtodojo.py
```

### Problema: Los findings se duplican en DefectDojo
**Solución:** Se puede hacer de varias maneras, se puede usar el reimport-scan de Dojo pero nosotros hemos utilizado una manera más sencilla y es activando la opción de deduplication y delete duplicates en Dojo.
![image](https://github.com/user-attachments/assets/ae40ee9a-bab4-439a-92f0-bf7554b9b5dc)

### Problema: Dependencias desactualizadas y mejoras en la configuración de Maven
**Solución:** Se actualizaron los siguientes cambios en el `pom.xml`:
- **Actualización del `maven-compiler-plugin`** de la versión `3.3` a `3.8.1`, lo que permite compatibilidad con **JDK 1.8**.
- **Cambio en la configuración de compilación:** Ahora `source` y `target` están en `1.8` en lugar de `1.7`.
- **Adición del `maven-war-plugin` versión `3.4.0`** para mejorar la gestión del empaquetado **WAR**.
Además, en la construcción de la aplicación con **Maven**, usamos la versión de **Java 1.8** para evitar problemas de incompatibilidad.

```sh
- name: Construir la aplicación con Maven
  run: |
      export JAVA_HOME=$(/usr/libexec/java_home -v 1.8)
      mvn clean install -U -DskipTests
  working-directory: ${{ github.workspace }}/${{ inputs.working_directory }}
```




