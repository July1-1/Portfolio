#!/bin/bash

# Docker Development Environment - Versión Mejorada
# Configuración con interfaces estéticas y retroalimentación mejorada

# File: docker-compose.sh

set -euo pipefail  # Modo estricto

# Obtener directorio actual del script para referencias relativas correctas
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Cargar biblioteca visual compartida primero
source "$SCRIPT_DIR/visual-lib.sh" 2>/dev/null || {
    echo "Error: No se pudo cargar la biblioteca visual"
    exit 1
}

# Colores
BLACK='\033[0;30m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
BOLD='\033[1m'
NC='\033[0m' # Sin color

# Configuración
COMPOSE_PROJECT_NAME="myproject"
COMPOSE_FILE="$PROJECT_ROOT/Docker/docker-compose.yaml"
START_TIME=$(date +%s)

# Verificar que los archivos necesarios existen
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}Error: El archivo docker-compose.yaml no existe en la ruta $COMPOSE_FILE${NC}"
    echo -e "${YELLOW}Directorio actual: $(pwd)${NC}"
    echo -e "${YELLOW}Directorio del script: $SCRIPT_DIR${NC}"
    echo -e "${YELLOW}Directorio raíz del proyecto: $PROJECT_ROOT${NC}"
    exit 1
fi

# Función para mensajes de estado
status_message() {
    local type=$1
    local message=$2
    local timestamp=$(date '+%H:%M:%S')
    
    case $type in
        info)
            echo -e "${CYAN}[${timestamp}]${NC} ${BLUE}ℹ️  ${message}${NC}"
            ;;
        success)
            echo -e "${CYAN}[${timestamp}]${NC} ${GREEN}✅ ${message}${NC}"
            ;;
        warning)
            echo -e "${CYAN}[${timestamp}]${NC} ${YELLOW}⚠️  ${message}${NC}"
            ;;
        error)
            echo -e "${CYAN}[${timestamp}]${NC} ${RED}❌ ${message}${NC}"
            ;;
        loading)
            echo -e "${CYAN}[${timestamp}]${NC} ${YELLOW}⏳ ${message}${NC}"
            ;;
    esac
}

#=====================================================================
# Ejecución principal
#=====================================================================

# Mostrar banner de inicio
show_banner "🐳 DOCKER DEVELOPMENT ENVIRONMENT" "Versión 1.0.0"

# Limpieza de contenedores
status_message "info" "Limpiando entorno anterior..."
show_progress_bar 1.5 "Limpieza"

# Usar comando directo en lugar de run_command para mejor depuración
echo -e "${YELLOW}Ejecutando: docker compose -p $COMPOSE_PROJECT_NAME -f $COMPOSE_FILE down${NC}"
if ! docker compose -p $COMPOSE_PROJECT_NAME -f $COMPOSE_FILE down; then
    status_message "error" "Error al detener contenedores previos"
    exit 1
fi
status_message "success" "Contenedores previos detenidos"

# Compilar proyecto (si existe un pom.xml)
if [ -f "$PROJECT_ROOT/pom.xml" ]; then
    status_message "loading" "Compilando el proyecto..."
    echo -e "${YELLOW}Ejecutando: mvn clean verify -B -Dorg.slf4j.simpleLogger.defaultLogLevel=WARN${NC}"
    if ! mvn -f "$PROJECT_ROOT/pom.xml" clean verify -B -Dorg.slf4j.simpleLogger.defaultLogLevel=WARN; then
        status_message "error" "Error al compilar con Maven"
        exit 1
    fi
    status_message "success" "Proyecto compilado"
else
    status_message "info" "No se encontró pom.xml, omitiendo compilación Maven"
fi

# Construir imagen Docker
status_message "loading" "Construyendo imagen Docker..."
echo -e "${YELLOW}Ejecutando: docker compose -p $COMPOSE_PROJECT_NAME -f $COMPOSE_FILE build${NC}"
if ! docker compose -p $COMPOSE_PROJECT_NAME -f $COMPOSE_FILE build; then
    status_message "error" "Error al construir imágenes Docker"
    exit 1
fi
status_message "success" "Imágenes Docker construidas"

# Iniciar contenedores
status_message "loading" "Iniciando contenedores..."
echo -e "${YELLOW}Ejecutando: docker compose -p $COMPOSE_PROJECT_NAME -f $COMPOSE_FILE up -d${NC}"
if ! docker compose -p $COMPOSE_PROJECT_NAME -f $COMPOSE_FILE up -d; then
    status_message "error" "Error al iniciar servicios"
    exit 1
fi
status_message "success" "Servicios iniciados"

# Esperar a que los servicios estén listos
#wait_for_service "${COMPOSE_PROJECT_NAME}-redis-1" 120 || exit 1
#wait_for_service "${COMPOSE_PROJECT_NAME}-ollama-1" 120 || exit 1
#wait_for_service "${COMPOSE_PROJECT_NAME}-frontend-1" 120 || exit 1

# Mostrar tiempo de ejecución
show_execution_time "$START_TIME"

echo -e "\n${GREEN}✨ ¡Entorno de desarrollo listo para usar! ✨${NC}\n"

exit 0