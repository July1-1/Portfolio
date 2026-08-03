#!/bin/bash
set -e

echo "Actualizando bibliotecas del sistema para compatibilidad"

# Verificar version actual del sistema
echo "Informacion del sistema:"
cat /etc/os-release
echo "Arquitectura: $(uname -m)"

# Verificar versiones actuales de bibliotecas
echo "Versiones actuales de bibliotecas:"
echo "GLIBC: $(ldd --version | head -1)"
echo "GCC: $(gcc --version | head -1)"

# Habilitar repositorios adicionales
echo "Habilitando repositorios adicionales"
yum install -y epel-release centos-release-scl || echo "Algunos repositorios ya disponibles"

# Actualizar bibliotecas del sistema
echo "Actualizando bibliotecas criticas"
yum update -y glibc glibc-common glibc-devel glibc-headers || echo "No se pudieron actualizar todas las bibliotecas GLIBC"
yum update -y libstdc++ libstdc++-devel gcc gcc-c++ || echo "No se pudieron actualizar todas las bibliotecas C++"

# Intentar instalar versiones mas nuevas desde Software Collections
echo "Intentando instalar versiones mas nuevas desde SCL"
yum install -y devtoolset-9-gcc devtoolset-9-gcc-c++ devtoolset-9-libstdc++-devel || echo "DevToolset-9 no disponible"

# Verificar versiones despues de actualizacion
echo "Versiones despues de actualizacion:"
echo "GLIBC: $(ldd --version | head -1)"
    if command -v scl &> /dev/null; then
        echo "DevToolset disponible"
        scl enable devtoolset-9 'gcc --version | head -1' || echo "DevToolset-9 no funcional"
    fi

# Crear enlaces simbolicos si es necesario
echo "Verificando enlaces simbolicos de bibliotecas"
ldconfig

echo "Actualizacion de bibliotecas completada"