#!/bin/bash
set -e
set -o pipefail

echo "Configurando Docker y Kubernetes"

# Descargar configuracion de deployment
echo "Descargando configuracion de deployment"
oci os object get --bucket-name reacttodo-a2fwz --name deployment_config.tgz --file deployment_config.tgz
tar -xzvf deployment_config.tgz

# Verificar archivo de configuracion
if [ ! -f at.cfg ]; then
    echo "ERROR: Archivo de configuracion at.cfg no encontrado"
    exit 1
fi

# Login a Docker registry
echo "Iniciando sesion en Docker registry: $DOCKER_REGISTRY"
cat at.cfg | docker login -u axbkferrc7jy/a01741176@tec.mx --password-stdin mx-queretaro-1.ocir.io

if [ $? -eq 0 ]; then
    echo "Login Docker exitoso"
else
    echo "ERROR: Login Docker fallo"
    exit 1
fi

# Crear secret de Kubernetes
echo "Creando secret de Kubernetes"
#kubectl delete secret oci-registry-secret --ignore-not-found=true

#kubectl create secret docker-registry oci-registry-secret \
#  --docker-server=mx-queretaro-1.ocir.io \
#  --docker-username=axbkferrc7jy/a01741176@tec.mx \
#  --docker-password=$(cat at.cfg)

#if [ $? -eq 0 ]; then
#    echo "Secret de Kubernetes creado exitosamente"
#else
#    echo "ERROR: Fallo creacion de secret Kubernetes"
#    exit 1
#fi

# Limpiar archivo sensible
rm -f at.cfg deployment_config.tgz

echo "Configuracion Docker completada"