#!/bin/bash

# Inicia el servidor Ollama
ollama serve &

# Espera a que el servidor esté disponible
echo "Esperando a que el servidor Ollama esté listo..."
until curl -s -f http://localhost:11434 > /dev/null 2>&1; do
  echo "Esperando conexión al servidor Ollama..."
  sleep 2
done

# Descarga el modelo
echo "Descargando modelo deepseek-coder:7b-instruct"
ollama pull deepseek-coder:7b-instruct

# Mantén el contenedor vivo
echo "Modelo descargado. Manteniendo el servidor activo..."
wait