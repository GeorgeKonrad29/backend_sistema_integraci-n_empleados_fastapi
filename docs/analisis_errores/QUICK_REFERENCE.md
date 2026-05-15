---
title: "Errores en get_workstation_suggestion() - Referencia Rápida"
author: "Code Review Automated"
date: 2024
---

# 🚨 ERRORES DETECTADOS - QUICK REFERENCE

## Ubicación
`src/api/v1/puesto_trabajo.py` - Función `get_workstation_suggestion()` (líneas 214-480)

---

## CRÍTICOS 🔴 (Resolver YA)

### 1️⃣ PROMPT INJECTION - Línea 306-332
```python
# ❌ VULNERABLE:
empleado_context = f"""
- Nombre: {empleado_info["nombre"]}  # Sin sanitizar
"""

# ✅ CORREGIR:
from html import escape

def sanitize(text):
    text = text.replace("\n", " ").replace("```", "")
    return text[:100]

empleado_context = f"""
- Nombre: {sanitize(empleado_info["nombre"])}
"""
```

### 2️⃣ INFORMACIÓN SENSIBLE EXPUESTA - Línea 356
```python
# ❌ RETORNA DATOS DE TODOS LOS EMPLEADOS:
return {
    "puestos_ocupados": ocupados,  # Nombres + ubicaciones de TODOS
    "respuesta_ia_completa": suggestion_text,  # Expone lógica
}

# ✅ CORREGIR:
# Solo para admin o si tiene permiso
return {
    "posiciones_recomendadas": posiciones,
    "estadisticas": {
        "total_ocupados": estadisticas["total_ocupados"],
    }
}
```

---

## ALTOS 🔴 (Este sprint)

### 3️⃣ EXCEPCIONES SILENCIADAS - Línea 246
```python
# ❌ PROBLEMA:
try:
    ocupado_info = _workstation_from_row(row)
except Exception:
    continue  # Silencia errores

# ✅ SOLUCIÓN:
try:
    ocupado_info = _workstation_from_row(row)
    ocupados.append(ocupado_info)
except ValueError as e:
    logger.warning(f"Invalid coords for {row.id}: {e}")
except Exception as e:
    logger.error(f"Error processing {row.id}: {e}")
    continue
```

### 4️⃣ SIN RESILENCIA EN AI - Línea 343
```python
# ❌ CUELGA INDEFINIDAMENTE:
ai_response = await ai.run(...)  # Sin timeout

# ✅ AGREGAR TIMEOUT:
try:
    ai_response = await asyncio.wait_for(
        ai.run("@cf/meta/llama-3.1-8b-instruct", {"prompt": prompt}),
        timeout=10.0  # Máximo 10 segundos
    )
except asyncio.TimeoutError:
    logger.warning("AI timeout")
    return generate_default_suggestions()
```

---

## MEDIOS 🟡 (Próximas 2-3 semanas)

| # | Error | Línea | Acción |
|---|-------|-------|--------|
| 5 | Parsing frágil | 424-445 | Cambiar a JSON en lugar de regex |
| 6 | Valores por defecto débiles | 459-460 | Validar que parsing encontró datos |
| 7 | Sin validación entrada | 217 | Agregar validators Pydantic |
| 8 | Query N+1 | 226-247 | Optimizar queries (baja prioridad) |
| 9 | Overflow contexto | 332 | Limitar a 50 puestos en prompt |
| 10 | Sin logging | Todo | Agregar logging en cada paso |
| 11 | Errores inconsistentes | 226-343 | Definir estrategia uniforme |

---

## 🔧 QUICK FIXES

### Agregar Logging Básico
```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"[SUGERENCIA] Iniciando para empleado={payload.id_empleado}")
# ... en cada paso ...
logger.info(f"[SUGERENCIA] {len(ocupados)} puestos procesados")
```

### Validar Permisos
```python
# En utils.py, si no existe:
def require_permission(token_payload, permission: str):
    if token_payload.get("role") != "admin" and permission not in token_payload.get("permissions", []):
        raise HTTPException(status_code=403, detail="Permiso denegado")

# En función:
if payload.id_empleado and payload.id_empleado != token_payload.get("id"):
    require_permission(token_payload, "workstations:view_others")
```

### Limitar Contexto
```python
MAX_PUESTOS = 50
if len(ocupados) > MAX_PUESTOS:
    import random
    ocupados_sample = random.sample(ocupados, MAX_PUESTOS)
    logger.info(f"Sampling {MAX_PUESTOS}/{len(ocupados)} workstations")
else:
    ocupados_sample = ocupados
```

---

## 📋 CHECKLIST CORRECCIÓN

**Semana 1:**
- [ ] Sanitizar input en prompts (línea 306-332)
- [ ] Validar permisos y filtrar respuesta (línea 356)
- [ ] Agregar logging básico

**Semana 2-3:**
- [ ] Hacer resiliente AI con timeout
- [ ] Loguear excepciones en procesamiento de puestos
- [ ] Validar estructura de respuesta de AI

**Semana 4+:**
- [ ] Cambiar regex por JSON
- [ ] Agregar validators Pydantic
- [ ] Limitar contexto si hay muchos puestos

---

## 📚 REFERENCIAS

- **Análisis Completo:** `docs/analisis_errores/ERRORES_get_workstation_suggestion.md`
- **Resumen Ejecutivo:** `docs/analisis_errores/RESUMEN_EJECUTIVO.md`
- **Documentación en código:** Docstring de la función (en el mismo archivo)

---

## 🔗 EJEMPLOS DE CÓDIGO ADICIONALES

### Estructura Segura de Prompt
```python
def build_safe_prompt(empleado_info, ocupados, payload):
    """Construye prompt con entrada sanitizada"""
    
    def safe(text, max_len=100):
        if not isinstance(text, str):
            text = str(text)
        return text.replace("\n", " ")[:max_len]
    
    empleado_block = ""
    if empleado_info:
        empleado_block = f"""
Empleado a asignar:
- ID: {empleado_info["id"]}
- Nombre: {safe(empleado_info["nombre"])}
- Area: {safe(empleado_info["area"])}
"""
    
    ubicacion_block = ""
    if payload.piso:
        ubicacion_block = f"""
Ubicación solicitada:
- Piso: {payload.piso}
- Fila: {payload.fila}
- Columna: {payload.columna}
"""
    
    return f"""Eres un asistente especializado en distribución de espacios.
{empleado_block}{ubicacion_block}
Datos: {len(ocupados)} puestos ocupados...
"""
```

### Response Filtering
```python
def build_response(token_payload, posiciones, empleado_info, estadisticas, ocupados):
    """Construye respuesta según permisos"""
    
    response = {
        "posiciones_recomendadas": posiciones,
    }
    
    is_admin = token_payload.get("role") == "admin"
    has_view_all = "workstations:view_all" in token_payload.get("permissions", [])
    
    # Solo mostrar datos sensibles a admin
    if is_admin or has_view_all:
        response["estadisticas"] = estadisticas
    else:
        response["estadisticas"] = {
            "total_ocupados": estadisticas["total_ocupados"]
        }
    
    # Nunca exponer lista completa de puestos a usuario regular
    if not (is_admin or has_view_all):
        response.pop("puestos_ocupados", None)
        response.pop("respuesta_ia_completa", None)
    
    return response
```

---

**Última actualización:** 2024
**Severidad General:** 🔴 CRÍTICA (2 errores críticos + 2 altos)
