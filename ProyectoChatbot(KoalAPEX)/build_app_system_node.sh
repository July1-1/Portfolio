#!/bin/bash
set -e
set -o pipefail

echo "Iniciando proceso de construccion con Node.js del sistema"

# Variables de configuracion
export IMAGE_NAME=koalapexv1
export IMAGE_VERSION=1.0
export DOCKERFILE=Dockerfile
export TARGET_PLATFORM="linux/amd64"

# Obtener DOCKER_REGISTRY del entorno
if [ -z "$DOCKER_REGISTRY" ]; then
    echo "ERROR: DOCKER_REGISTRY no esta configurado"
    exit 1
fi

export TAG=${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_VERSION}

echo "Configuracion de build:"
echo "  IMAGE_NAME: $IMAGE_NAME"
echo "  IMAGE_VERSION: $IMAGE_VERSION"
echo "  DOCKER_REGISTRY: $DOCKER_REGISTRY"
echo "  TAG: $TAG"

# Verificar herramientas necesarias
echo "Verificando herramientas requeridas"

    if ! command -v mvn &> /dev/null; then
        echo "ERROR: Maven no esta disponible"
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        echo "ERROR: Docker no esta disponible"
        exit 1
    fi

    if ! command -v node &> /dev/null; then
        echo "ERROR: Node.js no esta disponible"
        exit 1
    fi

    if ! command -v npm &> /dev/null; then
        echo "ERROR: NPM no esta disponible"
        exit 1
    fi

    if [ ! -f "$DOCKERFILE" ]; then
        echo "ERROR: Dockerfile no encontrado: $DOCKERFILE"
        exit 1
    fi

    # Verificar daemon Docker
    if ! docker info >/dev/null 2>&1; then
        echo "ERROR: Docker daemon no esta ejecutandose"
        exit 1
    fi

echo "Herramientas verificadas correctamente"
echo "Node.js version: $(node --version)"
echo "NPM version: $(npm --version)"

# Configurar variables para que frontend-maven-plugin use Node.js del sistema
export NODE_PATH=$(which node)
export NPM_PATH=$(which npm)
export NODE_OPTIONS="--max-old-space-size=4096"

echo "Configuracion Node.js:"
echo "  NODE_PATH: $NODE_PATH"
echo "  NPM_PATH: $NPM_PATH"

# Limpiar construccion anterior
echo "Limpiando construccion anterior"
mvn clean -q
    if [ -d "target" ]; then
        rm -rf target/*
    fi

    # Pre-instalar dependencias npm si existe package.json
    if [ -f "src/main/kanban-board-master/package.json" ]; then
        echo "Pre-instalando dependencias npm"
        cd src/main/kanban-board-master
        
        # Limpiar cache npm y node_modules
        rm -rf node_modules package-lock.json 2>/dev/null || true
        npm cache clean --force 2>/dev/null || true
        
        # Instalar dependencias con configuracion optimizada
        npm install --no-optional --production=false --legacy-peer-deps
        
        cd - > /dev/null
        echo "Dependencias npm pre-instaladas"
    fi

# Construir aplicacion con Maven usando Node.js del sistema
echo "Construyendo aplicacion con Maven"
echo "Comando: mvn clean package spring-boot:repackage -DskipTests -B"

    # Configurar properties para usar Node.js del sistema
    MAVEN_OPTS="-Xmx2g -XX:MaxPermSize=256m"
    MAVEN_OPTS="$MAVEN_OPTS -Dnode.download.skip=true"
    MAVEN_OPTS="$MAVEN_OPTS -Dnpm.download.skip=true"
    MAVEN_OPTS="$MAVEN_OPTS -Dnode.version=$(node --version)"
    MAVEN_OPTS="$MAVEN_OPTS -Dnpm.version=$(npm --version)"

    export MAVEN_OPTS

echo "MAVEN_OPTS: $MAVEN_OPTS"

    # Ejecutar Maven build
    if mvn clean package spring-boot:repackage -DskipTests -B \
    -Dnode.download.skip=true \
    -Dnpm.download.skip=true \
    -Dnode.version=$(node --version) \
    -Dnpm.version=$(npm --version); then
        echo "Maven build completado exitosamente"
    else
        echo "ERROR: Maven build fallo"
        echo "Verificando logs de Maven..."
        
        # Intentar build con debug para mas informacion
        echo "Reintentando con informacion de debug..."
        mvn clean package spring-boot:repackage -DskipTests -B -X \
        -Dnode.download.skip=true \
        -Dnpm.download.skip=true \
        -Dnode.version=$(node --version) \
        -Dnpm.version=$(npm --version) 2>&1 | tail -50
        
        exit 1
    fi

    # Verificar que Maven creo el directorio target
    if [ ! -d "target" ]; then
        echo "ERROR: Maven no creo el directorio target"
        exit 1
    fi

    # Verificar archivos JAR generados
    JAR_FILES=$(find target/ -name "*.jar" 2>/dev/null | wc -l)
    if [ "$JAR_FILES" -eq 0 ]; then
        echo "ERROR: No se generaron archivos JAR"
        echo "Contenido del directorio target:"
        ls -la target/ || echo "Directorio target vacio"
        exit 1
    fi

echo "Maven build completado exitosamente"
echo "Archivos JAR generados ($JAR_FILES):"
find target/ -name "*.jar" -exec ls -lh {} \;

# Construir imagen Docker
echo "Construyendo imagen Docker"
echo "Comando: docker build --no-cache -f $DOCKERFILE --platform $TARGET_PLATFORM -t $TAG ."

    if docker build --no-cache -f "$DOCKERFILE" --platform "$TARGET_PLATFORM" -t "$TAG" .; then
        echo "Imagen Docker construida exitosamente: $TAG"
    else
        echo "ERROR: Construccion de imagen Docker fallo"
        exit 1
    fi

    # Verificar imagen creada
    if docker images "$TAG" --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep -q "$TAG"; then
        echo "Imagen Docker verificada en registry local"
        docker images "$TAG" --format "table {{.Repository}}:{{.Tag}}"
    else
        echo "ERROR: Imagen Docker no encontrada en registry local"
        exit 1
    fi

# Push a registry remoto
echo "Enviando imagen a registry remoto"
echo "Comando: docker push $TAG"

    MAX_RETRIES=3
    RETRY_COUNT=0

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if docker push "$TAG"; then
            echo "Imagen enviada exitosamente: $TAG"
            break
        else
            RETRY_COUNT=$((RETRY_COUNT + 1))
            if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                echo "Intento $RETRY_COUNT fallo, reintentando en 5 segundos..."
                sleep 5
            else
                echo "ERROR: Push fallo despues de $MAX_RETRIES intentos"
                exit 1
            fi
        fi
    done

# Limpiar imagen local para ahorrar espacio
echo "Limpiando imagen local"
    if docker rmi "$TAG" 2>/dev/null; then
        echo "Imagen local removida: $TAG"
    else
        echo "Advertencia: No se pudo remover imagen local"
    fi

echo "Proceso de construccion completado exitosamente"
echo "Imagen final: $TAG"

