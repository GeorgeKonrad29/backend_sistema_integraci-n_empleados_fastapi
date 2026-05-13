# Configuracion de Cloudflare Worker AI

## Descripcion del Endpoint `/sugerencia`

El endpoint `GET /puestos-trabajo/sugerencia` utiliza Cloudflare Worker AI para proporcionar recomendaciones inteligentes sobre donde asignar nuevos puestos de trabajo basandose en:

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
curl -X GET https://tu-worker.workers.dev/puestos-trabajo/sugerencia \
  -H "Authorization: Bearer tu_token_jwt"
```

### Response

```json
{
  "sugerencia": "Basandote en la distribucion actual, recomiendo asignar el nuevo puesto en el Piso 2, Fila 10, Columna 5...",
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
  ]
}
```

## Modelo de IA Utilizado

- **Modelo**: `@cf/meta/llama-3-8b-instruct`
- **Proveedor**: Meta (a traves de Cloudflare)
- **Caracteristicas**: Modelo de lenguaje especializado en seguir instrucciones

## Flujo de Operacion

1. El usuario hace una solicitud GET a `/puestos-trabajo/sugerencia`
2. El endpoint consulta la base de datos para obtener todos los puestos ocupados
3. Se procesan los datos para generar estadisticas por tipo y area
4. Se construye un prompt descriptivo con esta informacion
5. Se envia el prompt a Cloudflare Worker AI a traves de la API
6. La IA analiza los datos y proporciona una recomendacion de ubicacion
7. La respuesta se retorna al cliente con:
   - La sugerencia de la IA
   - Las estadisticas calculadas
   - El listado completo de puestos ocupados

## Solución de Problemas

### Error: "Credenciales de Cloudflare AI no configuradas"

Asegúrate de que:
- Las variables `CF_AI_TOKEN` y `CF_ACCOUNT_ID` están configuradas en `wrangler.jsonc`
- Ejecutaste `wrangler deploy` después de actualizar las variables
- El Worker recibió correctamente las variables durante el despliegue

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
- Las recomendaciones se basan en la distribucion geográfica y por departamento
