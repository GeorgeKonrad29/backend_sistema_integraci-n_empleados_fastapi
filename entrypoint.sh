#!/bin/bash
set -e

# Inicia el servidor de Ollama en segundo plano
ollama serve &
SERVER_PID=$!

# Espera a que el servidor esté listo para recibir comandos
echo "⏳ Esperando a que el servidor de Ollama esté listo..."
MAX_RETRIES=30
RETRY_COUNT=0
until ollama list > /dev/null 2>&1; do
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "Error: El servidor de Ollama no se inició a tiempo."
        exit 1
    fi
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "Reintentando conexión... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo "✅ Servidor de Ollama listo."

# Verifica si la variable de entorno MODEL está definida y descarga el modelo
if [ -n "$MODEL" ]; then
    echo "📥 Descargando el modelo '$MODEL'..."
    ollama pull "$MODEL"
    echo "✅ Modelo '$MODEL' descargado."
else
    echo "ℹ️ No se especificó ningún modelo (variable MODEL no definida)."
fi

# Espera a que el proceso del servidor termine (o maneja la señal de parada)
wait $SERVER_PID