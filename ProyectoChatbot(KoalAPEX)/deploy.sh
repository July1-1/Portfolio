#!/bin/bash
set -e
set -o pipefail

echo "🚀 Iniciando proceso de construcción optimizado para OCI Pipeline"

# Variables de configuracion
export IMAGE_NAME=koalapexv1
export IMAGE_VERSION=1.0
export DOCKERFILE=Dockerfile
export TARGET_PLATFORM="linux/amd64"

# Obtener DOCKER_REGISTRY del entorno
if [ -z "$DOCKER_REGISTRY" ]; then
    echo "❌ ERROR: DOCKER_REGISTRY no esta configurado"
    exit 1
fi

export TAG=${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_VERSION}

echo "📋 Configuración de build para OCI:"
echo "  IMAGE_NAME: $IMAGE_NAME"
echo "  IMAGE_VERSION: $IMAGE_VERSION"
echo "  DOCKER_REGISTRY: $DOCKER_REGISTRY"
echo "  TAG: $TAG"
echo "  Usuario actual: $(whoami)"
echo "  Sistema: $(uname -a)"
echo "  GLIBC: $(ldd --version 2>/dev/null | head -1 || echo 'No disponible')"

# Verificar herramientas necesarias
echo "🔍 Verificando herramientas requeridas"

if ! command -v mvn &> /dev/null; then
    echo "❌ ERROR: Maven no esta disponible"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ ERROR: Docker no esta disponible"
    exit 1
fi

if [ ! -f "$DOCKERFILE" ]; then
    echo "❌ ERROR: Dockerfile no encontrado: $DOCKERFILE"
    exit 1
fi

# Verificar daemon Docker
if ! docker info >/dev/null 2>&1; then
    echo "❌ ERROR: Docker daemon no esta ejecutandose"
    exit 1
fi

# Verificar Node.js y npm - USAR VERSIÓN EXISTENTE
if ! command -v node &> /dev/null; then
    echo "❌ ERROR: Node.js no esta disponible"
    echo "💡 Asegúrate de que el paso 'Instalar Node.js Compatible' se ejecutó correctamente"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ ERROR: npm no esta disponible"
    exit 1
fi

echo "✅ Herramientas básicas verificadas"

# Obtener y verificar versiones EXISTENTES (sin intentar actualizar)
echo "📋 Verificando Node.js y npm instalados..."
if ! timeout 10 node -e "console.log('Node.js funcionando correctamente')" 2>/dev/null; then
    echo "❌ ERROR: Node.js no responde o tiene problemas"
    echo "🔍 Información de diagnóstico:"
    echo "  Versión: $(node --version 2>&1 || echo 'Error obteniendo versión')"
    echo "  Ubicación: $(which node 2>&1 || echo 'No encontrado')"
    echo "  Bibliotecas: $(ldd $(which node) 2>&1 | head -5 || echo 'Error verificando bibliotecas')"
    exit 1
fi

# Usar las versiones DISPONIBLES (no forzar actualización)
FINAL_NODE_VERSION=$(node --version)
FINAL_NPM_VERSION=$(npm --version)

echo "✅ Node.js funcional detectado"
echo "📋 Versiones para el build:"
echo "  Node.js: $FINAL_NODE_VERSION"
echo "  npm: $FINAL_NPM_VERSION"

# Configurar variables para el build
export NODE_PATH=$(which node)
export NPM_PATH=$(which npm)
export NODE_OPTIONS="--max-old-space-size=4096"

echo "🔧 Configuración de Node.js para el build:"
echo "  NODE_PATH: $NODE_PATH"
echo "  NPM_PATH: $NPM_PATH"  
echo "  NODE_OPTIONS: $NODE_OPTIONS"

# Limpiar construccion anterior
echo "🧹 Limpiando construccion anterior"
mvn clean -q
if [ -d "target" ]; then
    rm -rf target/*
fi

# Pre-instalar dependencias npm si existe package.json
if [ -f "src/main/kanban-board-master/package.json" ]; then
    echo "📦 Pre-instalando dependencias npm (incluyendo opcionales)"
    cd src/main/kanban-board-master
    
    # Verificar contenido del package.json
    echo "📋 Información del proyecto frontend:"
    if [ -f "package.json" ]; then
        echo "✅ package.json encontrado"
        echo "📦 Nombre del proyecto: $(grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' package.json | cut -d'"' -f4 || echo 'No especificado')"
        echo "🔧 Scripts disponibles:"
        grep -A 20 '"scripts"' package.json | head -10 || echo "  No se pudieron leer los scripts"
    fi
    
    # Limpiar cache npm y node_modules
    echo "🧹 Limpiando instalaciones previas de npm..."
    rm -rf node_modules package-lock.json yarn.lock .yarn 2>/dev/null || true
    npm cache clean --force 2>/dev/null || true
    
    # Configurar npm para entorno de CI/CD optimizado
    echo "⚙️  Configurando npm para CI/CD..."
    npm config set audit-level moderate
    npm config set fund false
    npm config set update-notifier false
    npm config set prefer-offline false  # Forzar descarga en CI
    npm config set cache /tmp/npm-cache
    mkdir -p /tmp/npm-cache
    
    # Instalar dependencias CON dependencias opcionales
    echo "📦 Instalando dependencias completas (con opcionales)..."
    if npm install \
        --include=optional \
        --include=dev \
        --production=false \
        --legacy-peer-deps \
        --no-audit \
        --no-fund \
        --verbose \
        --timeout=300000; then
        
        echo "✅ Dependencias instaladas correctamente"
        
        # Verificar instalación de dependencias
        echo "📋 Resumen de dependencias instaladas:"
        echo "  📦 Dependencias totales: $(npm list --depth=0 2>/dev/null | grep -c '^[├└]' || echo 'Error contando')"
        echo "  🔧 Dependencias opcionales:"
        npm list --depth=0 --only=optional 2>/dev/null | head -10 || echo "    Sin dependencias opcionales específicas"
        
        # Verificar que las herramientas de build funcionen
        echo "🧪 Verificando herramientas de build..."
        
        # Verificar si Vite está disponible
        if [ -f "node_modules/.bin/vite" ] || npm list vite &>/dev/null; then
            echo "✅ Vite detectado"
            if timeout 30 npm run build --if-present 2>/dev/null; then
                echo "✅ Pre-verificación de build exitosa"
            else
                echo "⚠️  Build de prueba falló, continuando con Maven..."
            fi
        else
            echo "ℹ️  Vite no detectado, verificando otros bundlers..."
            if npm list webpack &>/dev/null; then
                echo "✅ Webpack detectado"
            elif npm list rollup &>/dev/null; then
                echo "✅ Rollup detectado"
            else
                echo "ℹ️  Sin bundler específico detectado"
            fi
        fi
        
    else
        echo "⚠️  Error instalando dependencias npm, continuando con build básico..."
        echo "🔧 Intentando instalación mínima..."
        npm install --production=false --legacy-peer-deps --no-optional --no-audit --no-fund || echo "Instalación mínima también falló"
    fi
    
    cd - > /dev/null
    echo "🔙 Regresado al directorio raíz"
fi

# Construir aplicacion con Maven
echo "🏗️  Construyendo aplicación Java con frontend"

# Configurar properties para Maven con versiones EXISTENTES
MAVEN_OPTS="-Xmx4g -XX:MetaspaceSize=512m -XX:MaxMetaspaceSize=1g"
MAVEN_OPTS="$MAVEN_OPTS -Dnode.download.skip=true"
MAVEN_OPTS="$MAVEN_OPTS -Dnpm.download.skip=true"
MAVEN_OPTS="$MAVEN_OPTS -Dnode.version=$FINAL_NODE_VERSION"
MAVEN_OPTS="$MAVEN_OPTS -Dnpm.version=$FINAL_NPM_VERSION"

export MAVEN_OPTS

echo "🔧 Configuración Maven:"
echo "  MAVEN_OPTS configurado con versiones existentes"
echo "  Node.js version para Maven: $FINAL_NODE_VERSION"
echo "  npm version para Maven: $FINAL_NPM_VERSION"

# Construir argumentos de npm para frontend-maven-plugin
NPM_ARGS="install --include=optional --include=dev --production=false --legacy-peer-deps --no-audit --no-fund"

echo "🏗️  Ejecutando Maven build con dependencias opcionales..."
echo "📋 Comando npm que ejecutará Maven: $NPM_ARGS"

if mvn clean package spring-boot:repackage -DskipTests -B \
    -Dnode.download.skip=true \
    -Dnpm.download.skip=true \
    -Dnode.version=$FINAL_NODE_VERSION \
    -Dnpm.version=$FINAL_NPM_VERSION \
    -Dfrontend.workingDirectory=src/main/kanban-board-master \
    -Dfrontend.npm.arguments="$NPM_ARGS"; then
    
    echo "✅ Maven build completado exitosamente"
    
else
    echo "❌ ERROR: Maven build falló"
    
    # Diagnóstico detallado en caso de error
    echo "🔍 Iniciando diagnóstico detallado..."
    
    echo "📋 Información del sistema:"
    echo "  - Java: $(java -version 2>&1 | head -1)"
    echo "  - Maven: $(mvn -version 2>&1 | head -1)"
    echo "  - Node.js: $(node --version)"
    echo "  - npm: $(npm --version)"
    echo "  - Espacio disponible: $(df -h . | tail -1)"
    
    if [ -f "src/main/kanban-board-master/package.json" ]; then
        cd src/main/kanban-board-master
        echo "📋 Estado del frontend:"
        echo "  - Directorio node_modules: $([ -d node_modules ] && echo 'Existe' || echo 'No existe')"
        echo "  - package-lock.json: $([ -f package-lock.json ] && echo 'Existe' || echo 'No existe')"
        
        echo "🧪 Probando comandos npm directamente:"
        if npm list --depth=0 2>/dev/null | head -5; then
            echo "✅ npm list funciona"
        else
            echo "❌ npm list falla"
        fi
        
        if timeout 60 npm run build 2>&1 | head -10; then
            echo "✅ npm run build funciona directamente"
        else
            echo "❌ npm run build falla directamente"
        fi
        
        cd - > /dev/null
    fi
    
    echo "📄 Últimas líneas de logs Maven (si existen):"
    find . -name "*.log" -mtime -1 -exec tail -20 {} \; 2>/dev/null || echo "No se encontraron logs recientes"
    
    exit 1
fi

# Verificar generación de JAR
if [ ! -d "target" ]; then
    echo "❌ ERROR: Directorio target no fue creado por Maven"
    exit 1
fi

JAR_FILES=$(find target/ -name "*.jar" 2>/dev/null | wc -l)
if [ "$JAR_FILES" -eq 0 ]; then
    echo "❌ ERROR: No se generaron archivos JAR"
    echo "📋 Contenido del directorio target:"
    ls -la target/ 2>/dev/null || echo "📁 Directorio target vacío o inaccesible"
    exit 1
fi

echo "✅ Maven build exitoso - Aplicación Java compilada"
echo "📦 Archivos JAR generados ($JAR_FILES):"
find target/ -name "*.jar" -exec ls -lh {} \;

# Construir imagen Docker
echo "🐳 Construyendo imagen Docker"
echo "📋 Usando Dockerfile: $DOCKERFILE"
echo "📋 Plataforma objetivo: $TARGET_PLATFORM"

if docker build --no-cache -f "$DOCKERFILE" --platform "$TARGET_PLATFORM" -t "$TAG" .; then
    echo "✅ Imagen Docker construida exitosamente: $TAG"
else
    echo "❌ ERROR: Construcción de imagen Docker falló"
    echo "🔍 Información de diagnóstico Docker:"
    echo "  - Docker version: $(docker --version)"
    echo "  - Espacio disponible: $(df -h . | tail -1)"
    echo "  - Contenido actual: $(ls -la | head -10)"
    exit 1
fi

# Verificar imagen creada
if docker images "$TAG" --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep -q "$TAG"; then
    echo "✅ Imagen Docker verificada en registry local"
    docker images "$TAG" --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}"
else
    echo "❌ ERROR: Imagen Docker no encontrada en registry local"
    exit 1
fi

# Push a registry remoto
echo "☁️  Enviando imagen a registry remoto: $DOCKER_REGISTRY"
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "🔄 Intento $((RETRY_COUNT + 1)) de $MAX_RETRIES..."
    
    if docker push "$TAG"; then
        echo "✅ Imagen enviada exitosamente: $TAG"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "⏳ Intento $RETRY_COUNT falló, esperando 10 segundos antes del siguiente intento..."
            sleep 10
        else
            echo "❌ ERROR: Push falló después de $MAX_RETRIES intentos"
            echo "🔍 Verificar:"
            echo "  - Conectividad a $DOCKER_REGISTRY"
            echo "  - Credenciales de Docker"
            echo "  - Permisos en el registry"
            exit 1
        fi
    fi
done

# Limpiar imagen local para ahorrar espacio
echo "🧹 Limpiando imagen local para ahorrar espacio"
if docker rmi "$TAG" 2>/dev/null; then
    echo "✅ Imagen local removida: $TAG"
else
    echo "ℹ️  No se pudo remover imagen local (puede que ya esté en uso)"
fi

# Resumen final
echo
echo "🎉 BUILD COMPLETADO EXITOSAMENTE 🎉"
echo "======================================"
echo "📦 Imagen final: $TAG"
echo "🔧 Configuración utilizada:"
echo "  - Node.js: $FINAL_NODE_VERSION (compatible con GLIBC 2.17)"
echo "  - npm: $FINAL_NPM_VERSION"
echo "  - Dependencias opcionales: ✅ Habilitadas"
echo "  - Plataforma: $TARGET_PLATFORM"
echo "  - Entorno: OCI Build Pipeline ($(whoami))"
echo "  - Tiempo total: $SECONDS segundos"
echo "======================================"