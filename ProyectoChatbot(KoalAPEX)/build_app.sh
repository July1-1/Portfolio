#!/bin/bash

# Definición de variables principales
export IMAGE_NAME=todolistapp-springboot
export IMAGE_VERSION=0.1
export COMPOSE_FILE="Docker/docker-compose.yaml"

# Verificar el registro de Docker
if [ -z "$DOCKER_REGISTRY" ]; then
    export DOCKER_REGISTRY=$(state_get DOCKER_REGISTRY)
    echo "DOCKER_REGISTRY set."
fi
if [ -z "$DOCKER_REGISTRY" ]; then
    echo "Error: DOCKER_REGISTRY env variable needs to be set!"
    exit 1
fi

# Función para construir y subir una imagen
build_and_push() {
    local service=$1
    local tag=$2
    
    echo "Building image for $service as $tag..."
    
    # Si es el servicio frontend (Spring Boot), compilar primero
    if [ "$service" = "frontend" ]; then
        echo "Compiling Spring Boot application..."
        mvn clean package spring-boot:repackage
        
        echo "Building Docker image for $service..."
        docker build -f Dockerfile -t $tag .
    elif [ "$service" = "ollama" ]; then
        # Para ollama, construir desde su directorio
        echo "Building Docker image for ollama..."
        docker build -f Docker/ollama/Dockerfile -t $tag ./Docker/ollama
    fi
    
    echo "Pushing $tag to registry..."
    docker push $tag
    
    if [ $? -eq 0 ]; then
        echo "Successfully pushed $tag"
        docker rmi "$tag" # Eliminar imagen local
    else
        echo "Failed to push $tag"
        exit 1
    fi
}

# Verificar que el archivo docker-compose existe
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "Error: Docker Compose file not found at $COMPOSE_FILE"
    exit 1
fi

# Construir y subir la imagen principal de Spring Boot
MAIN_IMAGE=${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_VERSION}
build_and_push "frontend" $MAIN_IMAGE

# Comprobar si necesitamos construir imágenes adicionales desde docker-compose
echo "Checking additional services in docker-compose.yaml..."

# Determinar si ollama requiere una build personalizada
if grep -q "build:" "$COMPOSE_FILE" && grep -q "ollama" "$COMPOSE_FILE"; then
    OLLAMA_IMAGE=${DOCKER_REGISTRY}/todolistapp-ollama:${IMAGE_VERSION}
    build_and_push "ollama" $OLLAMA_IMAGE
    echo "Note: Update your Kubernetes manifest to use $OLLAMA_IMAGE for the ollama container"
fi

echo "Build process completed successfully"