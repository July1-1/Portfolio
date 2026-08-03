#!/bin/bash

echo "=== Testing SSL Configuration ==="

# Esperar a que el contenedor esté listo
echo "⏳ Esperando que el servicio esté listo..."
sleep 30

# Función para probar un endpoint
test_endpoint() {
    local url=$1
    local description=$2
    echo "🔍 Probando $description: $url"
    
    response=$(curl -k -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$url")
    
    if [ "$response" = "200" ] || [ "$response" = "302" ]; then
        echo "✅ $description: OK (HTTP $response)"
    else
        echo "❌ $description: FAILED (HTTP $response)"
    fi
}

# Probar endpoints
test_endpoint "http://localhost:8080/actuator/health" "HTTP Redirect"
test_endpoint "https://localhost:8443/actuator/health" "HTTPS Health Check"
test_endpoint "https://localhost:8443/" "HTTPS Main Page"

# Verificar certificado SSL
echo "🔍 Verificando certificado SSL..."
echo | openssl s_client -servername localhost -connect localhost:8443 2>/dev/null | \
    openssl x509 -noout -subject -dates 2>/dev/null

# Mostrar información del keystore dentro del contenedor
echo "🔍 Verificando keystore en el contenedor..."
docker exec $(docker ps -q --filter "name=frontend") keytool -list -keystore /agileorganizer/keystore.p12 -storepass password 2>/dev/null || echo "❌ No se pudo verificar el keystore"

echo "=== Pruebas completadas ==="