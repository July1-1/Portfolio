#!/bin/bash
SCRIPT_DIR=$(pwd)

# Validación de variables de entorno necesarias
if [ -z "$DOCKER_REGISTRY" ]; then
    export DOCKER_REGISTRY=$(state_get DOCKER_REGISTRY)
    echo "DOCKER_REGISTRY set."
fi
if [ -z "$DOCKER_REGISTRY" ]; then
    echo "Error: DOCKER_REGISTRY env variable needs to be set!"
    exit 1
fi

if [ -z "$TODO_PDB_NAME" ]; then
    export TODO_PDB_NAME=$(state_get MTDR_DB_NAME)
    echo "TODO_PDB_NAME set."
fi
if [ -z "$TODO_PDB_NAME" ]; then
    echo "Error: TODO_PDB_NAME env variable needs to be set!"
    exit 1
fi

if [ -z "$OCI_REGION" ]; then
    echo "OCI_REGION not set. Will get it with state_get"
    export OCI_REGION=$(state_get REGION)
fi
if [ -z "$OCI_REGION" ]; then
    echo "Error: OCI_REGION env variable needs to be set!"
    exit 1
fi

if [ -z "$UI_USERNAME" ]; then
    echo "UI_USERNAME not set. Will get it with state_get"
    export UI_USERNAME=$(state_get UI_USERNAME)
fi
if [ -z "$UI_USERNAME" ]; then
    echo "Error: UI_USERNAME env variable needs to be set!"
    exit 1
fi

# Creación de secretos si no existen
echo "Checking if secrets exist..."
kubectl get secret dbuser -n mtdrworkshop &>/dev/null
if [ $? -ne 0 ]; then
    echo "Creating database user secret..."
    read -s -p "Enter database password: " DBPASSWORD
    echo
    kubectl create secret generic dbuser --from-literal=dbpassword=$DBPASSWORD -n mtdrworkshop
fi

kubectl get secret frontendadmin -n mtdrworkshop &>/dev/null
if [ $? -ne 0 ]; then
    echo "Creating frontend admin secret..."
    read -s -p "Enter frontend admin password: " UI_PASSWORD
    echo
    kubectl create secret generic frontendadmin --from-literal=password=$UI_PASSWORD -n mtdrworkshop
fi

kubectl get secret db-wallet-secret -n mtdrworkshop &>/dev/null
if [ $? -ne 0 ]; then
    echo "Creating database wallet secret..."
    echo "Make sure you have your wallet files in the ./wallet directory"
    kubectl create secret generic db-wallet-secret --from-file=./wallet -n mtdrworkshop
fi

echo "Creating springboot deployment and service"
export CURRENTTIME=$(date '+%F_%H:%M:%S')
echo "CURRENTTIME is $CURRENTTIME ...this will be appended to generated deployment yaml"
cp src/main/resources/todolistapp-springboot.yaml todolistapp-springboot-$CURRENTTIME.yaml

# Reemplazar variables
sed -i "s|%DOCKER_REGISTRY%|${DOCKER_REGISTRY}|g" todolistapp-springboot-$CURRENTTIME.yaml
sed -i "s|%TODO_PDB_NAME%|${TODO_PDB_NAME}|g" todolistapp-springboot-$CURRENTTIME.yaml
sed -i "s|%OCI_REGION%|${OCI_REGION}|g" todolistapp-springboot-$CURRENTTIME.yaml
sed -i "s|%UI_USERNAME%|${UI_USERNAME}|g" todolistapp-springboot-$CURRENTTIME.yaml

# Crear el namespace si no existe
kubectl get namespace mtdrworkshop &>/dev/null || kubectl create namespace mtdrworkshop

# Aplicar la configuración
if [ -z "$1" ]; then
    kubectl apply -f $SCRIPT_DIR/todolistapp-springboot-$CURRENTTIME.yaml -n mtdrworkshop
else
    kubectl apply -f <(istioctl kube-inject -f $SCRIPT_DIR/todolistapp-springboot-$CURRENTTIME.yaml) -n mtdrworkshop
fi

# Verificar la IP pública
echo "Waiting for LoadBalancer IP to be assigned..."
for i in {1..30}; do
    IP=$(kubectl get svc todolistapp-springboot-service -n mtdrworkshop -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    if [ -n "$IP" ]; then
        echo "Application deployed successfully! Access it at:"
        echo "Frontend: http://$IP"
        echo "Redis: $IP:6379"
        echo "Ollama: http://$IP:11434"
        echo "Web: http://$IP:3001"
        break
    fi
    echo "Waiting for IP... ($i/30)"
    sleep 10
done

if [ -z "$IP" ]; then
    echo "Timeout waiting for LoadBalancer IP. Check your service with:"
    echo "kubectl get svc todolistapp-springboot-service -n mtdrworkshop"
fi