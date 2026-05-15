# 📋 Resumen Ejecutivo de Errores

## Función: `get_workstation_suggestion()` 

**Ubicación:** `src/api/v1/puesto_trabajo.py` (líneas 214-480)

---

## 🎯 Hallazgos Principales

### 🔴 CRÍTICOS (Resolver esta semana)

| Error | Línea | Impacto |
|-------|-------|---------|
| **Prompt Injection** | 306-332 | Usuario malicioso puede manipular instrucciones de IA |
| **Información Sensible Expuesta** | 356 | Datos de todos los empleados visibles para cualquier usuario |

### 🔴 ALTOS (Este sprint)

| Error | Línea | Impacto |
|-------|-------|---------|
| **Excepciones Silenciadas** | 245-255 | Puestos válidos ignorados, IA recibe datos incompletos |
| **Sin Resilencia AI** | 343 | Endpoint falla si Cloudflare AI no responde |

### 🟡 MEDIOS (Próximos sprints)

| Error | Línea | Impacto |
|-------|-------|---------|
| Parsing frágil | 424-445 | Sugerencias incompletas si IA varía formato |
| Sin validación entrada | 217 | Coordenadas inválidas llegan al prompt |
| Sin logging | Toda | Imposible depurar en producción |
| Query N+1 | 226-247 | Latencia innecesaria bajo carga |
| Overflow contexto | 332 | Fallo si hay muchos puestos |
| Valores por defecto débiles | 459-460 | Sugerencias genéricas sin contexto real |
| Manejo inconsistente errores | 226-343 | API impredecible |

---

## 🚀 Plan de Acción Recomendado

### **AHORA - Fase 1 (Esta semana)**

```python
# 1. Sanitizar datos antes de incluir en prompt
def sanitize_prompt_text(text: str) -> str:
    if not isinstance(text, str):
        return str(text)
    text = text.replace("\n", " ").replace("```", "")
    return text[:100]

# 2. Validar permisos antes de retornar info sensible
if payload.id_empleado and payload.id_empleado != token_payload.get("id"):
    require_permission(token_payload, "workstations:view_others")

# 3. Filtrar respuesta
return {
    "posiciones_recomendadas": posiciones,
    # NO retornar puestos_ocupados ni respuesta_ia_completa
}
```

### **SPRINT 1 - Fase 2 (Próximas 2 semanas)**

```python
# 1. Agregar logging
logger = logging.getLogger(__name__)
logger.info(f"[SUGERENCIA] Iniciando para empleado={payload.id_empleado}")

# 2. Hacer resiliente la llamada a AI
async def get_ai_with_fallback(ai, prompt):
    try:
        return await asyncio.wait_for(ai.run(...), timeout=10.0)
    except TimeoutError:
        return _generate_default_suggestions()

# 3. No silenciar excepciones
for row in result.results:
    try:
        ocupados.append(_workstation_from_row(row))
    except ValueError as e:
        logger.warning(f"Invalid coordinates for workstation {row.id}: {e}")
    except Exception as e:
        logger.error(f"Error processing workstation {row.id}: {e}")
```

### **SPRINT 2+ - Fase 3 (Mejoras)**

- Cambiar parsing de regex a JSON estructurado
- Agregar validators Pydantic en el modelo
- Limitar datos en prompt (max 50 puestos)
- Mejorar manejo de errores (clases específicas)

---

## 📊 Matriz de Riesgo

```
SEVERIDAD
   ▲
5  │  2️⃣  12️⃣
   │   CRÍTICOS
4  │  1️⃣  3️⃣
   │   ALTOS
3  │  5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 10️⃣ 11️⃣
   │   MEDIOS
2  │
   │
1  │
   └────────────────────────► PROBABILIDAD

2️⃣ = Prompt Injection (CRÍTICA - Alta probabilidad)
12️⃣ = Info sensible (CRÍTICA - Garantizado si se accede)
1️⃣ = Excepciones silenciadas (ALTA - Alta probabilidad)
3️⃣ = Sin fallback AI (ALTA - Media probabilidad)
...
```

---

## 📝 Checklist de Corrección

- [ ] **Sanitizar entrada en prompts** (Línea 306-332)
- [ ] **Validar permisos** antes de retornar datos sensibles (Línea 356)
- [ ] **Agregar logging** en pasos clave
- [ ] **Hacer resiliente llamada a AI** con timeout (Línea 343)
- [ ] **No silenciar excepciones** (Línea 246)
- [ ] **Validar estructura de respuesta** de AI (Línea 348)
- [ ] **Loguear errores** en parsing de IA
- [ ] **Agregar validators** en Pydantic model
- [ ] **Limitar contexto** en prompt si hay muchos puestos
- [ ] **Considerar JSON** en lugar de regex para parsing

---

## 📖 Documentación Completa

Ver archivo: `docs/analisis_errores/ERRORES_get_workstation_suggestion.md`

Para cada error encontrarás:
- ✅ Ubicación exacta en el código
- 🔍 Causa raíz
- ⚠️ Síntomas observables
- 💥 Impacto potencial
- 💡 Soluciones recomendadas con código
