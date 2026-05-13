# Configuracion de Cloudflare Worker AI

## Descripcion del Endpoint `/sugerencia`

El endpoint `POST /puestos-trabajo/sugerencia` utiliza Cloudflare Worker AI para proporcionar recomendaciones inteligentes sobre donde asignar un empleado especifico a un puesto de trabajo, basandose en:

- La informacion del empleado a asignar (nombre, area, tipo de puesto)
- La distribucion actual de empleados
- El balance entre diferentes tipos de puestos
- La distribucion geografica de los puestos (piso, fila, columna)

## Requisitos Previos

Para utilizar este endpoint necesitas:

1. **Cuenta de Cloudflare** con acceso a Workers AI
2. **Token de acceso a la API** de Cloudflare
3. **Account ID** de tu cuenta de Cloudflare

## Pasos de Configuracion

### 1. Obtener tu Account ID

- Inicia sesion en [Cloudflare Dashboard](https://dash.cloudflare.com/)
- Selecciona tu cuenta
- En la barra lateral izquierda, ve a "Workers & Pages"
- En la pagina de resumen, encontraras tu "Account ID" en la seccion de informacion

### 2. Crear un Token de API

- Ve a [API Tokens](https://dash.cloudflare.com/profile/api-tokens)
- Haz clic en "Create Token"
- Usa el template "Edit Cloudflare Workers" o crea uno personalizado
- El token debe tener permiso para acceder a "Workers AI"
- Copia el token generado

### 3. Configurar las Variables de Entorno en el Worker

Las variables se configuran en `wrangler.jsonc` en la seccion `vars`:

```json
{
	"vars": {
		"CF_AI_TOKEN": "tu_token_de_cloudflare_aqui",
		"CF_ACCOUNT_ID": "tu_account_id_aqui"
	}
}
```

**Importante:** En Cloudflare Workers, las variables definidas en `wrangler.jsonc` se pasan al entorno de ejecucion del Worker y son accesibles a traves del objeto `env` que recibe el Worker.

### 4. Desplegar

```bash
wrangler deploy
```

Despues de desplegar, el Worker tendra acceso a las variables definidas en `wrangler.jsonc`.

## Como Funcionan las Variables en el Worker

En el archivo `src/worker.py`, el objeto `env` contiene todas las variables definidas en `wrangler.jsonc`:

```python
class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # El objeto self.env contiene todas las variables
        # Se pasa a FastAPI como: req.scope["env"]
        return await asgi_app.fetch(request, self.env, self.ctx)
```

En los endpoints, accedes a las variables asi:

```python
env = req.scope["env"]
cf_token = getattr(env, "CF_AI_TOKEN", None)
cf_account_id = getattr(env, "CF_ACCOUNT_ID", None)
```

## Uso del Endpoint

### Request

```bash
curl -X POST https://tu-worker.workers.dev/puestos-trabajo/sugerencia \
  -H "Authorization: Bearer tu_token_jwt" \
  -H "Content-Type: application/json" \
  -d '{
    "id_empleado": 10,
    "piso": 1,
    "fila": 5,
    "columna": 8,
    "tipo_puesto": "abierto"
  }'
```

**Parametros del Request:**
- `id_empleado` (int, requerido): ID del empleado a asignar
- `piso` (int, 1-2): Piso donde se sugiere el puesto
- `fila` (int, 1-20): Fila donde se sugiere el puesto
- `columna` (int, 1-20): Columna donde se sugiere el puesto
- `tipo_puesto` (string, opcional): Tipo de puesto (ej: "abierto", "privado")

### Response

```json
{
  "sugerencia": "Basandote en el area de ingenieria donde trabaja Juan Perez, recomiendo asignar el puesto en el Piso 2, Fila 10, Columna 5 para mayor proximidad a colegas del departamento...",
  "estadisticas": {
    "total_ocupados": 25,
    "por_tipo": {
      "abierto": 15,
      "privado": 10
    },
    "por_area": {
      "ingenieria": 12,
      "ventas": 8,
      "administracion": 5
    }
  },
  "empleado": {
    "id": 10,
    "nombre": "Juan Perez",
    "area": "ingenieria"
  },
  "tipo_puesto_solicitado": "abierto",
  "puestos_ocupados": [
    {
      "id": 1,
      "id_empleado": 101,
      "nombre_empleado": "Carlos Gomez",
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

## Modelo de IA Utilizado

- **Modelo**: `@cf/meta/llama-3-8b-instruct`
- **Proveedor**: Meta (a traves de Cloudflare)
- **Caracteristicas**: Modelo de lenguaje especializado en seguir instrucciones

## Flujo de Operacion

1. El cliente envia una solicitud POST con los datos del empleado a asignar
2. El endpoint consulta la BD para obtener info del empleado (nombre, area)
3. Se obtienen todos los puestos ocupados y sus estadisticas
4. Se construye un prompt personalizado con la info del empleado
5. El prompt se envia a Cloudflare Worker AI
6. La IA analiza los datos y proporciona una recomendacion ubicacion
7. La respuesta se retorna con:
   - La sugerencia de la IA
   - Las estadisticas de distribucion
   - La info del empleado
   - El listado de puestos ocupados

## Solución de Problemas

### Error: "Credenciales de Cloudflare AI no configuradas"

Asegúrate de que:
- Las variables `CF_AI_TOKEN` y `CF_ACCOUNT_ID` están configuradas en `wrangler.jsonc`
- Ejecutaste `wrangler deploy` después de actualizar las variables
- El Worker recibió correctamente las variables durante el despliegue

### Error: "El empleado con ID X no existe"

Verifica que:
- El `id_empleado` que enviaste existe en la tabla USUARIO
- El empleado tiene asignado un cargo (FK a JERARQUIA)

### Error: "Error obteniendo informacion del empleado"

Verifica que:
- La tabla USUARIO existe
- La tabla JERARQUIA existe
- El join entre USUARIO y JERARQUIA funciona correctamente

### Error: "Error llamando a Cloudflare AI"

Verifica que:
- Tu cuenta de Cloudflare tiene acceso a Workers AI
- El Account ID es correcto
- El token tiene los permisos necesarios
- El token no ha expirado

### El endpoint tarda mucho en responder

Workers AI puede tardar algunos segundos en procesar la solicitud. Es normal que tarde entre 2-5 segundos.

### La base de datos devuelve error

Verifica que:
- El binding de base de datos `dataBase` está correctamente configurado en `wrangler.jsonc`
- La tabla `PUESTO_DE_TRABAJO` existe
- Las tablas `USUARIO` y `JERARQUIA` existen
- Los joints entre tablas funcionan correctamente

## Variables de Entorno Disponibles

Todas las variables definidas en la seccion `vars` de `wrangler.jsonc` estan disponibles:

| Variable | Descripcion | Requerida |
|----------|-------------|-----------|
| `CF_AI_TOKEN` | Token de API de Cloudflare para Workers AI | Si |
| `CF_ACCOUNT_ID` | ID de la cuenta de Cloudflare | Si |
| `MESSAGE` | Variable de ejemplo (puede eliminarse) | No |

## Notas Adicionales

- El endpoint requiere autenticacion (necesita un token JWT valido)
- La IA proporciona sugerencias basadas en patrones, no garantias de optimalidad
- Puedes usar estas sugerencias como referencia para tomar decisiones finales
- Las recomendaciones se personalizan segun el area del empleado
- El endpoint puede personalizar mas la recomendacion si incluyes el tipo de puesto solicitado
