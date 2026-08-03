#!/bin/bash

# Docker Cleanup Script - Versión Mejorada
# Con soporte para efectos visuales consistentes

# File: docker-clean.sh

set -euo pipefail  # Enable strict mode

# Cargar biblioteca visual compartida si no está ya cargada
if [ -z "${VISUAL_MODE:-}" ]; then
    source "$(dirname "$0")/visual-lib.sh" 2>/dev/null || {
        # Definir colores básicos como fallback
        RED='\033[0;31m'
        GREEN='\033[0;32m'
        YELLOW='\033[1;33m'
        BLUE='\033[0;34m'
        CYAN='\033[0;36m'
        MAGENTA='\033[0;35m'
        BOLD='\033[1m'
        NC='\033[0m'
        
        # Emojis
        EMOJI_STOP="🛑"
        EMOJI_DELETE="🗑️"
        EMOJI_SUCCESS="✅"
        EMOJI_SKIP="⏭️"
        EMOJI_PENDING="⏳"
        EMOJI_ERROR="❌"
    }
    
    # Si se ejecuta como script independiente, mostrar banner
    show_banner "🗑️ LIMPIEZA DE DOCKER" "v1.0.0"
else
    # Ya tenemos las variables visuales heredadas del script padre
    echo -e "${MAGENTA}┌─────────────────────────────────────────────────────┐${NC}"
    echo -e "${MAGENTA}│${NC}         🗑️  ${BOLD}Iniciando Proceso de Limpieza${NC}          ${MAGENTA}│${NC}"
    echo -e "${MAGENTA}└─────────────────────────────────────────────────────┘${NC}"
fi

# Define all containers to clean up in a single array
containers=(
    "myproject-redis-1"
    "myproject-ollama-1"
    "myproject-web-1"
    "myproject-frontend-1"
)

# Progress bar function (versión avanzada)

# Function to handle container operations with visual progress
handle_container() {
    local container=$1
    local operation=$2
    local emoji=$3
    local start_time=$(date +%s.%N)
    
    echo -ne "${CYAN}[$(date '+%H:%M:%S')]${NC} ${YELLOW}${emoji} "
    printf "%-30s" "$operation contenedor: $container"
    
    if docker inspect "$container" &>/dev/null; then
        if [ "$operation" = "stop" ]; then
            if ! docker inspect --format='{{.State.Running}}' "$container" 2>/dev/null | grep -q "true"; then
                echo -e "${CYAN}${EMOJI_SKIP} Ya detenido${NC}"
                return 0
            fi
        fi
        
        echo -ne "${EMOJI_PENDING} "
        
        # Mostrar actividad mientras se ejecuta el comando
        docker "$operation" "$container" > /tmp/docker_output.log 2>&1 &
        local docker_pid=$!
        
        # Mostrar spinner mientras se ejecuta el comando
        local spinner=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")
        local i=0
        while kill -0 $docker_pid 2>/dev/null; do
            echo -ne "\r${CYAN}[$(date '+%H:%M:%S')]${NC} ${YELLOW}${emoji} "
            printf "%-30s" "$operation contenedor: $container"
            echo -ne "${CYAN}${spinner[$i]}${NC}"
            i=$(( (i+1) % ${#spinner[@]} ))
            sleep 0.1
        done
        
        wait $docker_pid
        local status=$?
        
        if [ $status -eq 0 ]; then
            local end_time=$(date +%s.%N)
            local duration=$(echo "$end_time - $start_time" | bc)
            echo -e "\r${CYAN}[$(date '+%H:%M:%S')]${NC} ${YELLOW}${emoji} "
            printf "%-30s" "$operation contenedor: $container"
            echo -e "${GREEN}${EMOJI_SUCCESS} Completado en $(printf "%.2f" $duration)s${NC}"
        else
            echo -e "\r${CYAN}[$(date '+%H:%M:%S')]${NC} ${YELLOW}${emoji} "
            printf "%-30s" "$operation contenedor: $container"
            echo -e "${RED}${EMOJI_ERROR} Fallido${NC}"
            cat /tmp/docker_output.log | sed 's/^/    /'
            return 1
        fi
        
        rm -f /tmp/docker_output.log
    else
        echo -e "${CYAN}${EMOJI_SKIP} No encontrado${NC}"
        return 0
    fi
}

# Check if verbose mode is requested
VERBOSE=false
if [[ "${1:-}" == "--verbose" ]]; then
    VERBOSE=true
fi

# Display header with animation
echo -e "\n${YELLOW}🔄 Iniciando limpieza de Docker...${NC}"
echo -e "${YELLOW}${BOLD}Verificando contenedores a limpiar${NC}"

# Mostrar barra de progreso de inicialización
progress_bar 1 "Inicializando"

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Process all containers with visual feedback
for container in "${containers[@]}"; do
    # Stop the container if it's running
    handle_container "$container" "stop" "${EMOJI_STOP}"
    
    # Remove the container if it exists
    handle_container "$container" "rm" "${EMOJI_DELETE}"
done

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Mostrar resumen en formato tabla
echo -e "\n${BLUE}┌─────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│${NC} ${BOLD}RESUMEN DE LIMPIEZA${NC}                      ${BLUE}│${NC}"
echo -e "${BLUE}├─────────────────────────────────────────┤${NC}"
echo -e "${BLUE}│${NC} Contenedores procesados: ${GREEN}${#containers[@]}${NC}           ${BLUE}│${NC}"
echo -e "${BLUE}│${NC} Estado final: ${GREEN}Limpio${NC}                     ${BLUE}│${NC}"
echo -e "${BLUE}└─────────────────────────────────────────┘${NC}\n"

echo -e "${GREEN}✅ Limpieza completada exitosamente.${NC}\n"