@echo off
REM Script de instalación y configuración de Whisper para Windows
REM Este script instala tanto Whisper estándar como Faster-Whisper

echo 🚀 Instalando dependencias de Whisper...

REM Verificar si estamos en un entorno virtual
if "%VIRTUAL_ENV%"=="" (
    echo ⚠️ AVISO: No se detectó un entorno virtual activo.
    echo    Se recomienda usar un entorno virtual para evitar conflictos.
    echo    Crear entorno virtual: python -m venv .venv
    echo    Activar entorno virtual: .venv\Scripts\activate
    echo.
    set /p continue="¿Continuar sin entorno virtual? (y/N): "
    if /i not "%continue%"=="y" (
        echo ❌ Instalación cancelada.
        exit /b 1
    )
)

echo 📦 Actualizando pip...
python -m pip install --upgrade pip

echo 📦 Instalando dependencias base...
pip install -r requirements-base.txt

echo 🚀 Instalando Faster-Whisper...
pip install faster-whisper>=1.1.0

echo 🔧 Verificando instalación...

REM Verificar Whisper estándar
echo|set /p="✓ Whisper estándar: "
python -c "import whisper; print('✅ Instalado')" 2>nul || echo ❌ Error

REM Verificar Faster-Whisper  
echo|set /p="✓ Faster-Whisper: "
python -c "import faster_whisper; print('✅ Instalado')" 2>nul || echo ❌ Error

REM Verificar PyTorch
echo|set /p="✓ PyTorch: "
python -c "import torch; print('✅ Instalado')" 2>nul || echo ❌ Error

echo.
echo 🎯 Configuración de variables de entorno:
echo    USE_FASTER_WHISPER=true  # Usar Faster-Whisper (recomendado)
echo    WHISPER_MODEL=large-v3   # Usar modelo large-v3 (mejor calidad)
echo.
echo 📝 Para cambiar la configuración, edita el archivo .env:
echo    USE_FASTER_WHISPER=false  # Para usar Whisper estándar
echo    WHISPER_MODEL=large       # Para usar modelo large estándar
echo.
echo ✅ ¡Instalación completada!
echo 🔧 Configuración actual en .env:
if exist ".env" (
    findstr /R "USE_FASTER_WHISPER WHISPER_MODEL" .env 2>nul || echo    (Variables no encontradas en .env)
) else (
    echo    (Archivo .env no encontrado - usando valores por defecto)
)

pause
