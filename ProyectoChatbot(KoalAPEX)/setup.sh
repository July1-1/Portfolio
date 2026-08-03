#!/bin/bash

# Definir variables
TARGET_HOST="localhost"
TARGET_PORT="8080"
TARGET_URL="http://${TARGET_HOST}:${TARGET_PORT}"

echo "====================================================="
echo "  Iniciando escaneo de seguridad con Sn1per"
echo "  Objetivo: $TARGET_URL"
echo "====================================================="

# Ejecutar contenedor de BlackArch con Sn1per
echo "[+] Lanzando contenedor de BlackArch..."
docker run -it --rm \
  --network="host" \
  docker.io/blackarchlinux/blackarch:latest \
  /bin/bash -c "
    echo '[+] Actualizando el sistema...'
    pacman -Syu --noconfirm
    
    echo '[+] Instalando Sn1per...'
    pacman -Sy sn1per --noconfirm
    
    # Crear el archivo machine-id (faltante en el error)
    echo '[+] Creando archivo machine-id...'
    mkdir -p /etc
    echo 'containerized-sn1per' > /etc/machine-id
    
    echo '[+] Ejecutando Sn1per contra $TARGET_URL...'
    # Usar la ruta completa al ejecutable de Sn1per
    /usr/bin/sniper -t $TARGET_URL
    
    # Si la ruta anterior no funciona, intentar con estas alternativas:
    # Opción 1: buscar la ubicación de Sn1per e intentar ejecutarlo
    if [ \$? -ne 0 ]; then
      echo '[!] Error al ejecutar Sn1per. Intentando localizar el binario...'
      SNIPER_PATH=\$(find /usr -name sniper -type f -executable 2>/dev/null | head -n 1)
      if [ -n \"\$SNIPER_PATH\" ]; then
        echo \"[+] Encontrado Sn1per en \$SNIPER_PATH\"
        \$SNIPER_PATH -t $TARGET_URL
      fi
    fi
    
    # Opción 2: Clonar e instalar Sn1per directamente desde GitHub
    if [ \$? -ne 0 ]; then
      echo '[!] Intentando instalar Sn1per desde GitHub...'
      pacman -Sy git --noconfirm
      cd /tmp
      git clone https://github.com/1N3/Sn1per
      cd Sn1per
      bash install.sh
      ./sniper -t $TARGET_URL
    fi
    
    echo '[+] Escaneo completado.'
    read -p 'Presiona Enter para salir del contenedor...'
  "

echo "====================================================="
echo "  Escaneo de seguridad finalizado"
echo "====================================================="