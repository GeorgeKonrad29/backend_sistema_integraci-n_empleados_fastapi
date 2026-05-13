# Quick Start - Endpoint de Sugerencia

## Inicio Rapido en 5 Minutos

### 1. Obtener Credenciales (2 minutos)

**Account ID:**
1. Ve a https://dash.cloudflare.com/
2. Haz clic en "Workers & Pages"
3. Copia el "Account ID" de la esquina superior derecha

**API Token:**
1. Ve a https://dash.cloudflare.com/profile/api-tokens
2. Haz clic en "Create Token"
3. Selecciona "Edit Cloudflare Workers" como template
4. Haz clic en "Create Token"
5. Copia el token generado

### 2. Configurar el Proyecto (1 minuto)

Abre `wrangler.jsonc` y reemplaza:

```json
"vars": {
	"CF_AI_TOKEN": "TOKEN_AQUI",
	"CF_ACCOUNT_ID": "ACCOUNT_ID_AQUI"
}
```

### 3. Desplegar (2 minutos)

```bash
wrangler deploy
```

### 4. Probar el Endpoint

```bash
curl -X GET https://tu-worker.workers.dev/puestos-trabajo/sugerencia \
  -H "Authorization: Bearer TU_TOKEN_JWT"
```

## Respuesta Esperada

```json
{
  "sugerencia": "Basandote en la distribucion actual...",
  "estadisticas": {
    "total_ocupados": 25,
    "por_tipo": { "abierto": 15, "privado": 10 },
    "por_area": { "ingenieria": 12, "ventas": 8, "admin": 5 }
  },
  "puestos_ocupados": [...]
}
```

## Solucion de Problemas Rapida

| Error | Solucion |
|-------|----------|
| 401 Unauthorized | Verifica tu token JWT |
| Credenciales no configuradas | Actualiza wrangler.jsonc con tus valores |
| Timeout | Espera 2-5 segundos, la IA tarda en procesar |
| Error en BD | Verifica que la tabla PUESTO_DE_TRABAJO existe |

## Archivos Importantes

- `src/api/v1/puesto_trabajo.py` - Implementacion del endpoint
- `wrangler.jsonc` - Variables de entorno
- `docs/CLOUDFLARE_AI_SETUP.md` - Documentacion completa
- `docs/RESUMEN_CAMBIOS.md` - Detalles tecnicos

## Ayuda

Consulta los archivos en la carpeta `docs/` para mas informacion detallada.
