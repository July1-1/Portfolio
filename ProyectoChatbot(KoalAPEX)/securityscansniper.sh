#!/bin/bash

# Script de automatización para pentesting con OWASP ZAP para localhost
# Uso: ./zap_pentest_localhost.sh [PUERTO_APP] [PUERTO_ZAP]

# Colores para mejor visualización
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar sistema operativo para determinar la IP del host
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    HOST_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1)
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    HOST_IP=$(hostname -I | awk '{print $1}')
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows con Git Bash o similar
    HOST_IP=$(ipconfig | grep -A 5 "Wireless\|Ethernet" | grep "IPv4" | head -1 | awk '{print $NF}')
else
    # Fallback - intentar con interface común
    HOST_IP=$(ip addr show | grep -E "inet .* global" | grep -v docker | head -1 | awk '{print $2}' | cut -d/ -f1)
fi

# Configurar puertos
APP_PORT=${1:-8080}
ZAP_PORT=${2:-8090}  # Puerto para el proxy de ZAP (diferente del puerto de la aplicación)
TARGET_URL="http://${HOST_IP}:${APP_PORT}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="zap_results_${TIMESTAMP}"
XML_REPORT="${RESULTS_DIR}/zap_report.xml"
HTML_REPORT="${RESULTS_DIR}/zap_report.html"
LOG_FILE="${RESULTS_DIR}/zap_scan.log"

# Crear directorio para resultados
echo -e "${BLUE}Creando directorio para resultados: ${RESULTS_DIR}${NC}"
mkdir -p "${RESULTS_DIR}"

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker no está instalado. Por favor, instala Docker primero.${NC}"
    exit 1
fi

# Verificar si la imagen de ZAP está disponible
echo -e "${BLUE}Verificando imagen de Docker para OWASP ZAP...${NC}"
if ! docker images | grep -q "ghcr.io/zaproxy/zaproxy"; then
    echo -e "${YELLOW}Imagen de ZAP no encontrada, descargando...${NC}"
    docker pull ghcr.io/zaproxy/zaproxy:stable
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error al descargar la imagen de ZAP${NC}"
        exit 1
    fi
fi

# Verificar conectividad con la aplicación local
echo -e "${BLUE}Verificando conectividad con la aplicación en ${TARGET_URL}...${NC}"
if command -v curl &> /dev/null; then
    if ! curl -s --connect-timeout 5 "${TARGET_URL}" > /dev/null; then
        echo -e "${RED}Error: No se puede conectar a ${TARGET_URL}${NC}"
        echo -e "${YELLOW}Asegúrate de que tu aplicación esté corriendo y sea accesible.${NC}"
        exit 1
    fi
elif command -v wget &> /dev/null; then
    if ! wget -q --spider --timeout=5 "${TARGET_URL}"; then
        echo -e "${RED}Error: No se puede conectar a ${TARGET_URL}${NC}"
        echo -e "${YELLOW}Asegúrate de que tu aplicación esté corriendo y sea accesible.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}No se puede verificar la conectividad (curl o wget no disponibles)${NC}"
    echo -e "${YELLOW}Asegúrate de que tu aplicación esté corriendo en ${TARGET_URL}${NC}"
fi

# Ejecutar el escaneo con ZAP con puerto de proxy específico
echo -e "${GREEN}Iniciando escaneo de seguridad con OWASP ZAP para: ${TARGET_URL}${NC}"
echo -e "${YELLOW}Usando el puerto ${ZAP_PORT} para el proxy de ZAP${NC}"
echo -e "${YELLOW}Esto puede tomar algunos minutos...${NC}"

# Usando la red host y especificando puerto para el proxy
docker run --rm \
    --network host \
    -v "$(pwd)/${RESULTS_DIR}:/zap/wrk/:rw" \
    -t ghcr.io/zaproxy/zaproxy:stable zap.sh \
    -cmd \
    -port ${ZAP_PORT} \
    -quickurl "${TARGET_URL}" \
    -quickout /zap/wrk/zap_report.xml \
    2>&1 | tee "${LOG_FILE}"

if [ ! -f "${XML_REPORT}" ]; then
    echo -e "${RED}Error: No se pudo generar el reporte XML${NC}"
    exit 1
fi

# Generar reporte HTML a partir del XML usando XSLT
echo -e "${BLUE}Generando reporte HTML...${NC}"

# Crear un archivo XSLT para la transformación
cat > "${RESULTS_DIR}/transform.xslt" << 'EOL'
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/">
<html>
<head>
    <title>Reporte de Pentesting OWASP ZAP</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #2c3e50; }
        h2 { color: #3498db; }
        .high { color: #e74c3c; font-weight: bold; }
        .medium { color: #f39c12; font-weight: bold; }
        .low { color: #27ae60; font-weight: bold; }
        .info { color: #3498db; font-weight: bold; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:hover { background-color: #f5f5f5; }
    </style>
</head>
<body>
    <h1>Reporte de Pentesting - OWASP ZAP</h1>
    <p><strong>Fecha:</strong> <xsl:value-of select="substring(OWASPZAPReport/@generated, 1, 10)"/></p>
    <p><strong>URL Analizada:</strong> <xsl:value-of select="OWASPZAPReport/site/@name"/></p>
    
    <h2>Resumen de Vulnerabilidades</h2>
    <table>
        <tr>
            <th>Nivel de Riesgo</th>
            <th>Cantidad</th>
        </tr>
        <tr>
            <td class="high">Alto</td>
            <td><xsl:value-of select="count(//alertitem[riskcode='3'])"/></td>
        </tr>
        <tr>
            <td class="medium">Medio</td>
            <td><xsl:value-of select="count(//alertitem[riskcode='2'])"/></td>
        </tr>
        <tr>
            <td class="low">Bajo</td>
            <td><xsl:value-of select="count(//alertitem[riskcode='1'])"/></td>
        </tr>
        <tr>
            <td class="info">Informativo</td>
            <td><xsl:value-of select="count(//alertitem[riskcode='0'])"/></td>
        </tr>
    </table>
    
    <h2>Detalles de Vulnerabilidades</h2>
    <xsl:for-each select="//alertitem">
        <div>
            <h3>
                <xsl:choose>
                    <xsl:when test="riskcode='3'"><span class="high">[ALTO] </span></xsl:when>
                    <xsl:when test="riskcode='2'"><span class="medium">[MEDIO] </span></xsl:when>
                    <xsl:when test="riskcode='1'"><span class="low">[BAJO] </span></xsl:when>
                    <xsl:otherwise><span class="info">[INFO] </span></xsl:otherwise>
                </xsl:choose>
                <xsl:value-of select="name"/>
            </h3>
            <p><strong>Descripción:</strong> <xsl:value-of select="desc"/></p>
            <p><strong>URL:</strong> <xsl:value-of select="uri"/></p>
            <p><strong>Solución:</strong> <xsl:value-of select="solution"/></p>
            <p><strong>Referencia:</strong> <xsl:value-of select="reference"/></p>
            <hr/>
        </div>
    </xsl:for-each>
</body>
</html>
</xsl:template>
</xsl:stylesheet>
EOL

# Convertir XML a HTML usando xsltproc si está disponible
if command -v xsltproc &> /dev/null; then
    xsltproc -o "${HTML_REPORT}" "${RESULTS_DIR}/transform.xslt" "${XML_REPORT}"
    echo -e "${GREEN}Reporte HTML generado en: ${HTML_REPORT}${NC}"
else
    # Alternativa usando Saxon con Docker
    echo -e "${YELLOW}xsltproc no encontrado, usando una alternativa...${NC}"
    echo -e "${YELLOW}Nota: Para conversión automática a HTML, instala xsltproc con: sudo apt-get install xsltproc${NC}"
    echo -e "${GREEN}Reporte XML disponible en: ${XML_REPORT}${NC}"
    echo -e "Puedes convertirlo a HTML manualmente o visualizarlo en un navegador XML."
fi

echo -e "\n${GREEN}¡Proceso completado!${NC}"
echo -e "${BLUE}Resumen:${NC}"
echo -e "- URL analizada: ${TARGET_URL}"
echo -e "- Puerto del proxy ZAP: ${ZAP_PORT}"
echo -e "- Reporte XML: ${XML_REPORT}"
if [ -f "${HTML_REPORT}" ]; then
    echo -e "- Reporte HTML: ${HTML_REPORT}"
fi
echo -e "- Log del escaneo: ${LOG_FILE}"
echo -e "\n${YELLOW}Revisa los reportes para obtener detalles sobre las vulnerabilidades encontradas.${NC}"