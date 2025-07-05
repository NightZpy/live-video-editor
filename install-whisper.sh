#!/bin/bash

# Script de instalación y configuración de Whisper
# Este script instala tanto Whisper estándar como Faster-Whisper

echo "🚀 Instalando dependencias de Whisper..."

# Verificar si estamos en un entorno virtual
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️ AVISO: No se detectó un entorno virtual activo."
    echo "   Se recomienda usar un entorno virtual para evitar conflictos."
    echo "   Crear entorno virtual: python -m venv .venv"
    echo "   Activar entorno virtual: source .venv/bin/activate (Linux/macOS) o .venv\\Scripts\\activate (Windows)"
    echo ""
    read -p "¿Continuar sin entorno virtual? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Instalación cancelada."
        exit 1
    fi
fi

echo "📦 Actualizando pip..."
python -m pip install --upgrade pip

echo "📦 Instalando dependencias base..."
pip install -r requirements-base.txt

echo "🚀 Instalando Faster-Whisper..."
pip install faster-whisper>=1.1.0

echo "🔧 Verificando instalación..."

# Verificar Whisper estándar
echo -n "✓ Whisper estándar: "
python -c "import whisper; print('✅ Instalado')" 2>/dev/null || echo "❌ Error"

# Verificar Faster-Whisper
echo -n "✓ Faster-Whisper: "
python -c "import faster_whisper; print('✅ Instalado')" 2>/dev/null || echo "❌ Error"

# Verificar PyTorch
echo -n "✓ PyTorch: "
python -c "import torch; print('✅ Instalado')" 2>/dev/null || echo "❌ Error"

echo ""
echo "🎯 Configuración de variables de entorno:"
echo "   USE_FASTER_WHISPER=true  # Usar Faster-Whisper (recomendado)"
echo "   WHISPER_MODEL=large-v3   # Usar modelo large-v3 (mejor calidad)"
echo ""
echo "📝 Para cambiar la configuración, edita el archivo .env:"
echo "   USE_FASTER_WHISPER=false  # Para usar Whisper estándar"
echo "   WHISPER_MODEL=large       # Para usar modelo large estándar"
echo ""
echo "✅ ¡Instalación completada!"
echo "🔧 Configuración actual en .env:"
if [ -f ".env" ]; then
    grep -E "USE_FASTER_WHISPER|WHISPER_MODEL" .env || echo "   (Variables no encontradas en .env)"
else
    echo "   (Archivo .env no encontrado - usando valores por defecto)"
fi
