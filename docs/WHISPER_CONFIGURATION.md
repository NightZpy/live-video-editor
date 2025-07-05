# Configuración de Whisper: Estándar vs Faster-Whisper

Este proyecto soporta dos implementaciones de Whisper para transcripción de audio:

## 🔧 Implementaciones Disponibles

### 1. **Whisper Estándar** (Original OpenAI)
- ✅ Implementación oficial de OpenAI
- ✅ Máxima compatibilidad
- ⚠️ Velocidad estándar
- ⚠️ Mayor uso de memoria

### 2. **Faster-Whisper** (Optimizado)
- ✅ **4-8x más rápido** que Whisper estándar
- ✅ **Menor uso de memoria** (~50% menos)
- ✅ **Misma precisión** que Whisper estándar
- ✅ Soporte para Voice Activity Detection (VAD)
- ✅ Optimizado para CPU y GPU

## ⚙️ Configuración

### Variables de Entorno (.env)

```bash
# Implementación a usar
USE_FASTER_WHISPER=true    # true = Faster-Whisper, false = Whisper estándar

# Modelo Whisper a usar (recomendado: large-v3)
WHISPER_MODEL=large-v3     # large-v3, large, medium, small, base
```

### Modelos Disponibles (ambas implementaciones)

| Modelo | Tamaño | Velocidad | Precisión | Recomendado para |
|--------|--------|-----------|-----------|------------------|
| `large-v3` | ~3GB | Lento | **Máxima** | **Videos importantes** |
| `large` | ~3GB | Lento | Muy Alta | Videos largos de calidad |
| `medium` | ~1.5GB | Medio | Alta | Balance velocidad/calidad |
| `small` | ~500MB | Rápido | Media | Pruebas rápidas |
| `base` | ~150MB | Muy Rápido | Básica | Solo para testing |

## 🚀 Instalación

### Opción 1: Script Automático (Recomendado)

```bash
# Linux/macOS/WSL
./install-whisper.sh

# Windows
install-whisper.bat
```

### Opción 2: Manual

```bash
# Instalar dependencias base
pip install -r requirements-base.txt

# Instalar Faster-Whisper
pip install faster-whisper>=1.1.0
```

## 📊 Comparación de Rendimiento

| Métrica | Whisper Estándar | Faster-Whisper | Mejora |
|---------|------------------|----------------|---------|
| **Velocidad** | 1x | **4-8x** | 400-800% |
| **Memoria** | 100% | **~50%** | 50% menos |
| **Precisión** | 100% | **100%** | Igual |
| **Calidad** | Excelente | **Excelente** | Igual |

## 🎯 Configuraciones Recomendadas

### Para Máxima Calidad
```bash
USE_FASTER_WHISPER=true
WHISPER_MODEL=large-v3
```

### Para Balance Velocidad/Calidad
```bash
USE_FASTER_WHISPER=true
WHISPER_MODEL=medium
```

### Para Máxima Compatibilidad
```bash
USE_FASTER_WHISPER=false
WHISPER_MODEL=large-v3
```

## 🔍 Verificación de Configuración

El sistema automáticamente detecta y reporta la configuración al iniciar:

```
🔧 Whisper transcriber initialized:
   - Implementation: Faster-Whisper
   - Preferred model: large-v3
   - Device: cuda
```

## 🚨 Resolución de Problemas

### Faster-Whisper no disponible
Si `USE_FASTER_WHISPER=true` pero faster-whisper no está instalado:
- El sistema automáticamente fallback a Whisper estándar
- Instalar: `pip install faster-whisper>=1.1.0`

### Modelo no encontrado
Si el modelo especificado no está disponible:
- El sistema prueba modelos alternativos automáticamente
- Orden de fallback: `large-v3` → `large` → `medium` → `small` → `base`

### Memoria insuficiente
Para problemas de memoria GPU/CPU:
- Usar modelo más pequeño: `WHISPER_MODEL=medium`
- Usar CPU en lugar de GPU
- Usar Faster-Whisper para menor uso de memoria

## 💡 Recomendaciones

1. **Para producción**: `USE_FASTER_WHISPER=true` + `WHISPER_MODEL=large-v3`
2. **Para desarrollo**: `USE_FASTER_WHISPER=true` + `WHISPER_MODEL=medium`  
3. **Para testing**: `USE_FASTER_WHISPER=true` + `WHISPER_MODEL=small`

El resto del pipeline (PyTorch, callbacks, caché, análisis LLM) funciona **exactamente igual** con ambas implementaciones.
