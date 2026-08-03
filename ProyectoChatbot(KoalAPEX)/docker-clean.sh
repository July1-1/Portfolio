#!/bin/bash
set -e

# Variables (ajústalas según tus necesidades)
export DOCKER_REGISTRY=<tu-registro-docker>
export TODO_PDB_NAME=<nombre-de-tu-pdb>
export OCI_REGION=<tu-region-oci>
export UI_USERNAME=<nombre-de-usuario-ui>

# Crear namespace si no existe
kubectl create namespace mtdrworkshop 2>/dev/null || true

# Crear PVCs necesarios
echo "Creando PVCs para datos persistentes..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-data-pvc
  namespace: mtdrworkshop
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF

kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ollama-models-pvc
  namespace: mtdrworkshop
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
EOF

# Crear el YAML de despliegue
echo "Generando archivo de despliegue..."
cat > todolistapp-springboot.yaml << 'EOL'
# Aquí va el contenido del YAML (copiar el YAML completo del paso 6)
EOL

# Reemplazar variables
sed -i "s|%DOCKER_REGISTRY%|${DOCKER_REGISTRY}|g" todolistapp-springboot.yaml
sed -i "s|%TODO_PDB_NAME%|${TODO_PDB_NAME}|g" todolistapp-springboot.yaml
sed -i "s|%OCI_REGION%|${OCI_REGION}|g" todolistapp-springboot.yaml
sed -i "s|%UI_USERNAME%|${UI_USERNAME}|g" todolistapp-springboot.yaml

# Aplicar el despliegue
echo "Desplegando la aplicación..."
kubectl apply -f todolistapp-springboot.yaml -n mtdrworkshop

# Esperar a que los pods estén listos
echo "Esperando a que los pods estén listos..."
kubectl wait --for=condition=Ready pods --all -n mtdrworkshop --timeout=300s

# Obtener IP pública
echo "Obteniendo IP pública..."
ATTEMPTS=0
EXTERNAL_IP=""
while [ -z "$EXTERNAL_IP" ] && [ $ATTEMPTS -lt 30 ]; do
  EXTERNAL_IP=$(kubectl get svc todolistapp-springboot-service -n mtdrworkshop -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
  if [ -z "$EXTERNAL_IP" ]; then
    echo "Esperando la asignación de IP externa... (intento $ATTEMPTS/30)"
    sleep 10
    ATTEMPTS=$((ATTEMPTS+1))
  fi
done

if [ -z "$EXTERNAL_IP" ]; then
  echo "No se pudo obtener la IP externa después de 5 minutos. Verifica el estado del servicio:"
  kubectl get svc todolistapp-springboot-service -n mtdrworkshop
else
  echo "¡Despliegue completado!"
  echo "La aplicación se ha desplegado con éxito y está disponible en:"
  echo "- Frontend: http://${EXTERNAL_IP}:80"
  echo "- Web UI: http://${EXTERNAL_IP}:3001"
  echo "- Ollama API: http://${EXTERNAL_IP}:11434"
  echo "- Redis está disponible en el puerto 6379 (principalmente para uso interno)"
  
  # Verificar que la aplicación responde
  echo "Verificando que la aplicación responde..."
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://${EXTERNAL_IP}:80 || echo "Error")
  if [ "$HTTP_STATUS" == "200" ]; then
    echo "✅ La aplicación responde correctamente."
  else
    echo "⚠️ La aplicación no responde con estado 200. Estado: $HTTP_STATUS"
    echo "Verificando los logs de los pods:"
    kubectl logs -l app=todolistapp-springboot -n mtdrworkshop --tail=50
  fi
fi