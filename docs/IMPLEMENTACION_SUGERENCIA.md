# Guía de Implementacion: Endpoint de Sugerencia de Puestos

## Resumen

Se ha implementado un nuevo endpoint `GET /puestos-trabajo/sugerencia` que utiliza Cloudflare Worker AI para proporcionar recomendaciones inteligentes sobre donde asignar nuevos puestos de trabajo basandose en la distribucion actual de empleados.

## Archivos Modificados

### 1. `src/api/v1/puesto_trabajo.py`
- **Cambio**: Agregada la funcion `get_workstation_suggestion()` (lineas 214-347)
- **Funcionalidad**: 
  - Consulta la base de datos para obtener todos los puestos ocupados
  - Procesa estadisticas por tipo de puesto y area
  - Envia los datos a Cloudflare Worker AI
  - Retorna una sugerencia inteligente junto con estadisticas

### 2. `wrangler.jsonc`
- **Cambio**: Agregadas nuevas variables de entorno
  - `CF_AI_TOKEN`: Token de API de Cloudflare
  - `CF_ACCOUNT_ID`: ID de la cuenta de Cloudflare

### 3. `pyproject.toml`
- **Cambio**: Agregada dependencia `httpx` para solicitudes HTTP asincronas

### 4. `docs/CLOUDFLARE_AI_SETUP.md`
- **Cambio**: Creado archivo de documentacion con instrucciones de configuracion

## Flujo de Funcionamiento

```
[Cliente] 
    |
    v
[GET /puestos-trabajo/sugerencia]
    |
    v
[Endpoint get_workstation_suggestion()]
    |
    +---> [Consultar BD: Puestos ocupados]
    |
    +---> [Procesar estadisticas]
    |
    +---> [Construir prompt para IA]
    |
    +---> [Llamar Cloudflare Worker AI]
    |
    v
[Retornar: Sugerencia + Estadisticas + Puestos]
    |
    v
[Cliente recibe respuesta JSON]
```

## Configuracion Requerida

### Paso 1: Obtener Credenciales de Cloudflare

1. Ve a https://dash.cloudflare.com/
2. Selecciona tu cuenta
3. Ve a Workers & Pages
4. Copia tu **Account ID** (aparece en la pagina de resumen)
5. Ve a API Tokens y crea un nuevo token con permisos para Workers AI
6. Copia el **Token generado**

### Paso 2: Configurar Variables en wrangler.jsonc

Abre `wrangler.jsonc` y reemplaza los valores:

```json
{
	"vars": {
		"CF_AI_TOKEN": "tu_token_aqui",
		"CF_ACCOUNT_ID": "tu_account_id_aqui"
	}
}
```

### Paso 3: Desplegar

```bash
wrangler deploy
```

## Uso del Endpoint

### Request

```bash
curl -X GET https://tu-worker.workers.dev/puestos-trabajo/sugerencia \
  -H "Authorization: Bearer tu_token_jwt"
```

### Response Exitosa (200)

```json
{
	"sugerencia": "Basandote en la distribucion actual con 25 puestos ocupados, recomiendo asignar el nuevo puesto en el Piso 2, Fila 15, Columna 10...",
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
			"id_empleado": 10,
			"nombre_empleado": "Juan Perez",
			"area": "ingenieria",
			"tipo_puesto": "abierto",
			"coordenadas": "P1-F01-C01",
			"piso": 1,
			"fila": 1,
			"columna": 1,
			"ocupado": true
		}
		// ... mas puestos
	]
}
```

### Errores Posibles

| Codigo | Descripcion | Causa |
|--------|-------------|-------|
| 401 | No autorizado | Token JWT invalido o expirado |
| 500 | Credenciales no configuradas | CF_AI_TOKEN o CF_ACCOUNT_ID no estan configurados |
| 500 | Error en BD | Problema al consultar la base de datos |
| 500 | Error llamando a Cloudflare AI | Problema con la conexion a Cloudflare o token invalido |

## Datos Utilizados por la IA

El prompt enviado a la IA incluye:

1. **Contexto**: "Eres un asistente especializado en optimizacion de espacios de trabajo"
2. **Estadisticas Actuales**:
   - Total de puestos ocupados
   - Distribucion por tipo de puesto
   - Distribucion por area/departamento
3. **Datos Detallados**: Listado completo de todos los puestos con:
   - ID del empleado
   - Nombre del empleado
   - Area/Departamento
   - Tipo de puesto
   - Ubicacion (Piso, Fila, Columna)
4. **Instrucciones**: Criterios a considerar para la recomendacion

## Seguridad

- El endpoint requiere autenticacion con token JWT
- Las credenciales de Cloudflare se almacenan en variables de entorno
- No se exponem las credenciales en el codigo
- Las solicitudes HTTP son sobre HTTPS

## Limitaciones y Consideraciones

1. **Tiempo de respuesta**: Puede tardar 2-5 segundos debido al procesamiento de IA
2. **Datos**: La sugerencia se basa en los datos actuales, no en predicciones futuras
3. **No deterministica**: Las respuestas pueden variar ligeramente entre llamadas
4. **Dependencia de Cloudflare**: Requiere conexion activa a Cloudflare Worker AI

## Proximos Pasos Opcionales

1. **Mejorar el Prompt**: Ajustar las instrucciones para la IA segun necesidades especificas
2. **Cachear Resultados**: Implementar cache para respuestas recientes
3. **Agregar Parametros**: Permitir filtrar por area, tipo de puesto, etc.
4. **Metricas**: Implementar logging y monitoreo de uso del endpoint
5. **Validacion de IA**: Agregar validacion de la respuesta antes de retornarla

## Referencia Rapida

| Archivo | Cambio | Descripcion |
|---------|--------|-------------|
| `src/api/v1/puesto_trabajo.py` | +125 lineas | Nueva funcion get_workstation_suggestion() |
| `wrangler.jsonc` | +2 vars | CF_AI_TOKEN, CF_ACCOUNT_ID |
| `pyproject.toml` | +1 dep | httpx |
| `docs/CLOUDFLARE_AI_SETUP.md` | +nuevo | Documentacion detallada |

## Soporte

Para mas informacion sobre Cloudflare Worker AI, visita:
- https://developers.cloudflare.com/workers-ai/
- https://developers.cloudflare.com/workers/platform/environment-variables/
