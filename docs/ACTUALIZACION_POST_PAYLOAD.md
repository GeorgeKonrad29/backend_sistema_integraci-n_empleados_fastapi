# Actualizacion: Endpoint de Sugerencia con Payload

## Cambios Realizados

### ✅ Endpoint Actualizado a POST con Payload

**Antes:**
```
GET /puestos-trabajo/sugerencia
```

**Ahora:**
```
POST /puestos-trabajo/sugerencia
Content-Type: application/json

{
  "id_empleado": 10,
  "piso": 1,
  "fila": 5,
  "columna": 8,
  "tipo_puesto": "abierto"
}
```

### 📝 Cambios en el Código

**Archivo**: `src/api/v1/puesto_trabajo.py`

#### Antes (linea 214)
```python
@router.get("/sugerencia")
async def get_workstation_suggestion(
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
```

#### Ahora (linea 214)
```python
@router.post("/sugerencia")
async def get_workstation_suggestion(
    payload: PuestoTrabajoAsignacionRequest,
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
```

### 🎯 Nuevas Funcionalidades

1. **Recibe Payload Personalizado**
   - `id_empleado`: Identificador del empleado a asignar
   - `piso`, `fila`, `columna`: Ubicacion sugerida
   - `tipo_puesto`: Tipo de puesto solicitado

2. **Obtiene Info del Empleado**
   - Consulta nombre del empleado
   - Obtiene area/departamento
   - Personaliza el prompt segun el empleado

3. **Respuesta Mejorada**
   - Incluye `empleado`: Datos del empleado a asignar
   - Incluye `tipo_puesto_solicitado`: Tipo de puesto
   - Sugerencia personalizada segun el empleado

### 📊 Respuesta del Endpoint

```json
{
  "sugerencia": "Basandote en el area de ingenieria donde trabaja Juan Perez...",
  "estadisticas": {
    "total_ocupados": 25,
    "por_tipo": {"abierto": 15, "privado": 10},
    "por_area": {"ingenieria": 12, "ventas": 8, "admin": 5}
  },
  "empleado": {
    "id": 10,
    "nombre": "Juan Perez",
    "area": "ingenieria"
  },
  "tipo_puesto_solicitado": "abierto",
  "puestos_ocupados": [...]
}
```

## Comparacion de Funcionalidades

| Caracteristica | Antes | Ahora |
|---|---|---|
| Metodo HTTP | GET | POST |
| Payload | No | Si (PuestoTrabajoAsignacionRequest) |
| Personalizacion | Generica | Por empleado |
| Info del empleado | No incluida | Incluida en respuesta |
| Contexto IA | Global | Especifico del empleado |
| Sugerencia | General | Personalizada |

## Ejemplo de Uso

### Request
```bash
curl -X POST https://tu-worker.workers.dev/puestos-trabajo/sugerencia \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "id_empleado": 10,
    "piso": 1,
    "fila": 5,
    "columna": 8,
    "tipo_puesto": "abierto"
  }'
```

### Response (200 OK)
```json
{
  "sugerencia": "Considerando que Juan Perez trabaja en el area de ingenieria con 12 ingenieros actualmente, recomiendo asignarle un puesto en el Piso 2, Fila 10, Columna 5. Esta ubicacion esta cerca de otros colegas de su departamento y proporciona buen balance entre diferentes tipos de puestos.",
  "empleado": {
    "id": 10,
    "nombre": "Juan Perez",
    "area": "ingenieria"
  },
  "tipo_puesto_solicitado": "abierto",
  "estadisticas": {...},
  "puestos_ocupados": [...]
}
```

## Ventajas de la Nueva Implementacion

✅ **Personalizacion**: Las sugerencias se adaptan al empleado especifico
✅ **Contexto Mejorado**: La IA conoce el area y nombre del empleado
✅ **Informacion Completa**: Devuelve info del empleado junto con la sugerencia
✅ **Reutilizable**: El mismo modelo de request se usa en assign_workstation

## Lineas de Codigo

| Archivo | Antes | Ahora | Cambio |
|---------|-------|-------|--------|
| puesto_trabajo.py | 338 | 375 | +37 lineas |

## Compatibilidad

- ✅ Compatible con `PuestoTrabajoAsignacionRequest`
- ✅ Compatible con autenticacion JWT
- ✅ Compatible con Cloudflare Workers
- ✅ Compatible con D1 Database

## Proximos Pasos

1. Actualizar cliente para enviar POST con payload
2. Probar endpoint con datos reales de empleados
3. Ajustar el prompt segun resultados de IA
4. Monitorear tiempos de respuesta

## Referencia Tecnica

**Query para obtener empleado:**
```sql
SELECT u.id, u.nombre, j.area 
FROM USUARIO u 
INNER JOIN JERARQUIA j ON j.id = u.cargo 
WHERE u.id = ? LIMIT 1
```

**Endpoint del Worker:**
```
Metodo: POST
Ruta: /puestos-trabajo/sugerencia
Autenticacion: JWT
Payload: PuestoTrabajoAsignacionRequest
Timeout: 2-6 segundos
```

---

**Nota**: Toda la documentacion ha sido actualizada. Consulta `docs/` para mas detalles.
