# Diagrama de Arquitectura - Endpoint de Sugerencia

## Flujo General

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENTE                                  │
│                                                                    │
│  GET /puestos-trabajo/sugerencia                                 │
│  Authorization: Bearer JWT_TOKEN                                 │
└─────────────────────────┬──────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              CLOUDFLARE WORKER (FastAPI)                         │
│                                                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ get_workstation_suggestion()                              │  │
│  │                                                            │  │
│  │ 1. Acceder variables de env                              │  │
│  │    ├─ env.CF_AI_TOKEN                                    │  │
│  │    └─ env.CF_ACCOUNT_ID                                  │  │
│  │                                                            │  │
│  │ 2. Conectar a BD (D1 - Cloudflare)                       │  │
│  │    ├─ await db.prepare(SQL)                              │  │
│  │    └─ SELECT puestos ocupados + empleados               │  │
│  │                                                            │  │
│  │ 3. Procesar datos                                        │  │
│  │    ├─ Contar por tipo_puesto                             │  │
│  │    ├─ Contar por area                                    │  │
│  │    └─ Preparar JSON descriptivo                          │  │
│  │                                                            │  │
│  │ 4. Construir Prompt para IA                              │  │
│  │    ├─ Contexto del sistema                               │  │
│  │    ├─ Estadisticas                                        │  │
│  │    ├─ Listado completo                                   │  │
│  │    └─ Instrucciones                                       │  │
│  │                                                            │  │
│  │ 5. Llamar Cloudflare Workers AI                          │  │
│  │    └─ POST a api.cloudflare.com                          │  │
│  │                                                            │  │
│  │ 6. Retornar respuesta                                    │  │
│  │    ├─ sugerencia (string)                                │  │
│  │    ├─ estadisticas (dict)                                │  │
│  │    └─ puestos_ocupados (list)                            │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
   ┌──────────────┐  ┌──────────────────────────┐
   │  D1 (BD)     │  │ Cloudflare Workers AI    │
   │              │  │                          │
   │ Consulta:    │  │ Modelo:                  │
   │ PUESTO_...   │  │ llama-3-8b-instruct     │
   │ USUARIO      │  │                          │
   │ JERARQUIA    │  │ Retorna:                 │
   └──────────────┘  │ Sugerencia JSON          │
                     └──────────────────────────┘
                               │
                               │
                               ▼
                     ┌──────────────────────┐
                     │ Respuesta JSON       │
                     │ {                    │
                     │   sugerencia,        │
                     │   estadisticas,      │
                     │   puestos_ocupados   │
                     │ }                    │
                     └──────────────────────┘
                               │
                               ▼
                     ┌──────────────────────┐
                     │ CLIENTE recibe       │
                     │ respuesta 200 OK     │
                     └──────────────────────┘
```

## Estructura de Datos

### Request
```
GET /puestos-trabajo/sugerencia
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5...
```

### Response Body
```json
{
  "sugerencia": "Recomendacion detallada de donde ir",
  "estadisticas": {
    "total_ocupados": 25,
    "por_tipo": {
      "abierto": 15,
      "privado": 8,
      "compartido": 2
    },
    "por_area": {
      "ingenieria": 12,
      "ventas": 8,
      "administracion": 5
    }
  },
  "puestos_ocupados": [
    {
      "id": 1,
      "id_empleado": 101,
      "nombre_empleado": "Juan Perez",
      "area": "ingenieria",
      "tipo_puesto": "abierto",
      "coordenadas": "P1-F01-C01",
      "piso": 1,
      "fila": 1,
      "columna": 1,
      "ocupado": true
    }
  ]
}
```

## Bases de Datos

### Tablas Consultadas
```
PUESTO_DE_TRABAJO
├─ id (PK)
├─ coordenadas (string: P[1-2]-F[01-20]-C[01-20])
├─ id_empleado (FK → USUARIO)
└─ tipo_puesto (string)
        ↓
USUARIO
├─ id (PK)
├─ nombre (string)
└─ cargo (FK → JERARQUIA)
        ↓
JERARQUIA
├─ id (PK)
└─ area (string)
```

### Query SQL
```sql
SELECT 
  p.id, 
  p.coordenadas, 
  p.id_empleado, 
  p.tipo_puesto, 
  u.nombre AS nombre_empleado, 
  j.area AS area
FROM PUESTO_DE_TRABAJO p
INNER JOIN USUARIO u ON u.id = p.id_empleado
INNER JOIN JERARQUIA j ON j.id = u.cargo
WHERE p.id_empleado IS NOT NULL
ORDER BY p.coordenadas
```

## Componentes del Sistema

```
┌──────────────────────────────────────────────────────┐
│              CLOUDFLARE WORKERS PLATFORM             │
├──────────────────────────────────────────────────────┤
│                                                       │
│  ┌────────────────┐  ┌────────────────────────────┐ │
│  │  FastAPI App   │  │  Cloudflare Services       │ │
│  │  (Python)      │  │  ┌──────────────────────┐  │ │
│  │                │  │  │ D1 Database          │  │ │
│  │  Router:       │  │  │ (SQL Database)       │  │ │
│  │  GET /puestos- │  │  └──────────────────────┘  │ │
│  │      trabajo/  │  │                            │ │
│  │      sugerencia│  │  ┌──────────────────────┐  │ │
│  │                │  │  │ Workers AI           │  │ │
│  │  Función:      │  │  │ (Modelos IA)         │  │ │
│  │  get_workstat- │  │  │ llama-3-8b-instruct  │  │ │
│  │  ion_suggesti- │  │  └──────────────────────┘  │ │
│  │  on()          │  │                            │ │
│  │                │  │  ┌──────────────────────┐  │ │
│  │  Dependencias: │  │  │ Environment Vars     │  │ │
│  │  - httpx       │  │  │ CF_AI_TOKEN          │  │ │
│  │  - fastapi     │  │  │ CF_ACCOUNT_ID        │  │ │
│  │  - json        │  │  └──────────────────────┘  │ │
│  └────────────────┘  └────────────────────────────┘ │
│                                                       │
└──────────────────────────────────────────────────────┘
```

## Librerias Utilizadas

```
┌──────────────────────────────────────────┐
│         DEPENDENCIAS DEL PROYECTO        │
├──────────────────────────────────────────┤
│                                          │
│  ✓ fastapi          - Framework web     │
│  ✓ httpx            - Cliente HTTP async│
│  ✓ json             - Serialización     │
│  ✓ webtypy          - Bindings de C++   │
│  ✓ jinja2           - Templates         │
│  ✓ markupsafe       - HTML escaping     │
│  ✓ workers-py       - SDK de Cloudflare │
│                                          │
└──────────────────────────────────────────┘
```

## Seguridad

```
┌─────────────────────────────────────────────────────┐
│           CAPAS DE SEGURIDAD                         │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. Autenticación JWT                              │
│     └─ Token requerido en header Authorization    │
│                                                      │
│  2. Validación de Permisos                         │
│     └─ get_current_token_payload                   │
│                                                      │
│  3. Variables de Entorno Protegidas                │
│     └─ CF_AI_TOKEN (no en código)                  │
│     └─ CF_ACCOUNT_ID (no en código)                │
│                                                      │
│  4. HTTPS Obligatorio                              │
│     └─ api.cloudflare.com usa SSL/TLS             │
│                                                      │
│  5. Manejo de Errores                              │
│     └─ Errores sin exponer detalles internos      │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Tiempos de Respuesta

```
┌──────────────────────────────────────────────────────┐
│            DESGLOSE DE TIEMPOS                        │
├──────────────────────────────────────────────────────┤
│                                                       │
│  1. Autenticación JWT          ~50ms                │
│  2. Conexión a BD              ~100ms               │
│  3. Consulta SQL               ~200ms               │
│  4. Procesamiento de datos     ~50ms                │
│  5. Llamada a Cloudflare AI    ~2-5s ⭐            │
│  6. Procesamiento de respuesta ~50ms                │
│                                                       │
│  ────────────────────────────────────────────────    │
│  TOTAL APROXIMADO:             2-6 segundos         │
│                                                       │
│  ⭐ = Tiempo dominante (procesamiento de IA)        │
│                                                       │
└──────────────────────────────────────────────────────┘
```

## Error Handling

```
┌─────────────────────────────────────────────────┐
│        MANEJO DE EXCEPCIONES                     │
├─────────────────────────────────────────────────┤
│                                                  │
│  try:                                           │
│    ├─ [Consultar BD]                           │
│    ├─ [Procesar datos]                         │
│    ├─ [Llamar IA]                              │
│    └─ return respuesta_ok                      │
│                                                  │
│  except Exception as e:                        │
│    └─ raise HTTPException(500, detail)         │
│                                                  │
└─────────────────────────────────────────────────┘
```

## Proxima Evolucion

```
ACTUAL                          POSIBLE FUTURO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                
GET /sugerencia       ──────→   GET /sugerencia?filtros=...
  └─ Analiza todo               ├─ Por area
                                ├─ Por tipo
                                ├─ Por piso
                                └─ Personalizado

  └─ Sin cache       ──────→   CON CACHE
                                ├─ Redis
                                ├─ TTL: 5 minutos
                                └─ Invalidacion

  └─ Sin logging     ──────→   CON LOGGING
                                ├─ Analytics
                                ├─ Metricas
                                └─ Monitoring
```

---

**Nota**: Este diagrama es una representacion visual del flujo.
Para mas detalles tecnicos, ver `RESUMEN_CAMBIOS.md` y `IMPLEMENTACION_SUGERENCIA.md`
