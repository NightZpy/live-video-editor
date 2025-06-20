# Configuración de Variables de Entorno

Este proyecto utiliza variables de entorno para una configuración segura y flexible. Aquí te explicamos cómo configurarlas.

## 🔧 Configuración Rápida

### 1. Crear archivo .env

Copia el archivo de ejemplo y renómbralo:
```bash
cp .env.example .env
```

### 2. Editar el archivo .env

Abre `.env` en tu editor y completa los valores:

```env
# OpenAI API Key - OBLIGATORIO
OPENAI_API_KEY=sk-tu-api-key-real-aqui

# Configuración opcional del modelo por defecto
DEFAULT_MODEL=gpt-4o-mini

# Configuración de tokens máximos
MAX_COMPLETION_TOKENS=8192
```

### 3. Obtener tu API Key de OpenAI

1. Ve a [OpenAI Platform](https://platform.openai.com/api-keys)
2. Inicia sesión en tu cuenta
3. Haz clic en "Create new secret key"
4. Copia la clave y pégala en tu archivo `.env`

## 🛡️ Seguridad

- **NUNCA** subas el archivo `.env` a Git (ya está en `.gitignore`)
- **NUNCA** compartas tu API key públicamente
- **NUNCA** hardcodees la API key en el código

## 📋 Variables Disponibles

| Variable | Descripción | Valor por defecto | Requerida |
|----------|-------------|-------------------|-----------|
| `OPENAI_API_KEY` | Tu clave de API de OpenAI | - | ✅ Sí |
| `DEFAULT_MODEL` | Modelo principal a usar | `gpt-4o-mini` | ❌ No |
| `MAX_COMPLETION_TOKENS` | Límite de tokens por respuesta | `8192` | ❌ No |

## 💻 Uso en el Código

### Opción 1: Solo con variables de entorno
```python
from src.core.llm_cuts_processor import LLMCutsProcessor

# Usa automáticamente OPENAI_API_KEY del .env
processor = LLMCutsProcessor()
```

### Opción 2: API key manual (sobrescribe .env)
```python
# Sobrescribe la variable de entorno
processor = LLMCutsProcessor(api_key="sk-tu-api-key-manual")
```

### Opción 3: Configuración personalizada
```python
import os

# Cambiar configuración temporalmente
os.environ['DEFAULT_MODEL'] = 'gpt-4.1'
os.environ['MAX_COMPLETION_TOKENS'] = '12000'

processor = LLMCutsProcessor()
```

## 🔧 Modelos Soportados

El sistema usa una estrategia de fallback automática con estos modelos:

1. **Modelo principal** (configurado en `DEFAULT_MODEL`)
2. **gpt-4o-mini** (fallback rápido y económico)
3. **gpt-4.1-mini** (fallback balanceado)
4. **gpt-4.1** (fallback más capaz)

Si el primer modelo falla, automáticamente prueba con el siguiente.

## 🚨 Solución de Problemas

### Error: "No OpenAI API key provided"
- ✅ Verifica que el archivo `.env` existe
- ✅ Verifica que `OPENAI_API_KEY` está definida en `.env`
- ✅ Verifica que no hay espacios extras en el valor

### Error: "Invalid API key"
- ✅ Verifica que la API key es correcta
- ✅ Verifica que tienes créditos en tu cuenta de OpenAI
- ✅ Verifica que la clave no ha expirado

### Error: "Model not found"
- ✅ Verifica que el modelo está disponible en tu cuenta
- ✅ Usa un modelo estándar como `gpt-4o-mini`

## 📝 Ejemplo Completo

```bash
# 1. Crear .env
cp .env.example .env

# 2. Editar .env con tu API key
echo "OPENAI_API_KEY=sk-tu-api-key-aqui" > .env

# 3. Probar configuración
python ejemplo_env_usage.py
```

## 🔄 Migración desde Versiones Anteriores

Si estabas pasando la API key manualmente, ahora puedes:

**Antes:**
```python
processor = LLMCutsProcessor(api_key="sk-hardcoded-key")
```

**Ahora (recomendado):**
```python
# Configurar en .env: OPENAI_API_KEY=sk-tu-key
processor = LLMCutsProcessor()
```

**Compatibilidad:**
```python
# Sigue funcionando, pero no es recomendado
processor = LLMCutsProcessor(api_key="sk-manual-key")
```
