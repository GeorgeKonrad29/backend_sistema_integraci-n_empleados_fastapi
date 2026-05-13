# Documentacion - Endpoint de Sugerencia de Puestos

## Archivos de Documentacion

### 📋 [QUICK_START.md](QUICK_START.md)
**Para iniciar rapido (5 minutos)**
- Pasos para configurar credenciales
- Comando para desplegar
- Como probar el endpoint
- Solucion rapida de problemas

👉 **Comienza aqui si quieres usar el endpoint rapidamente**

---

### 📖 [RESUMEN_CAMBIOS.md](RESUMEN_CAMBIOS.md)
**Resumen de los cambios implementados**
- Archivos modificados
- Funcionalidad agregada
- Detalles tecnicos
- Manejo de errores
- Seguridad

👉 **Lee esto para entender que se hizo**

---

### 🔧 [CLOUDFLARE_AI_SETUP.md](CLOUDFLARE_AI_SETUP.md)
**Guia completa de configuracion**
- Como obtener Account ID
- Como crear un API Token
- Configuracion de variables de entorno
- Como funcionan las variables en el Worker
- Uso del endpoint con ejemplos
- Solución de problemas detallada

👉 **Consulta esto para detalles de configuracion**

---

### 🚀 [IMPLEMENTACION_SUGERENCIA.md](IMPLEMENTACION_SUGERENCIA.md)
**Detalles de la implementacion**
- Archivos modificados con lineas especificas
- Flujo de funcionamiento
- Datos utilizados por la IA
- Limitaciones y consideraciones
- Proximos pasos opcionales

👉 **Lee esto para entender la arquitectura**

---

## Navegacion Rapida

| Necesidad | Archivo | Seccion |
|-----------|---------|---------|
| Empezar rapido | QUICK_START.md | Inicio Rapido en 5 Minutos |
| Entender cambios | RESUMEN_CAMBIOS.md | Cambios Implementados |
| Configurar credenciales | CLOUDFLARE_AI_SETUP.md | Pasos de Configuracion |
| Ver ejemplo de respuesta | RESUMEN_CAMBIOS.md | Response |
| Solucionar problemas | CLOUDFLARE_AI_SETUP.md | Solución de Problemas |
| Entender arquitectura | IMPLEMENTACION_SUGERENCIA.md | Flujo de Funcionamiento |
| Ver SQL utilizado | RESUMEN_CAMBIOS.md | Querys SQL Utilizados |

## Puntos Clave

### Endpoint
```
GET /puestos-trabajo/sugerencia
```

### Autenticacion
Requiere token JWT valido en header:
```
Authorization: Bearer TOKEN_JWT
```

### Variables Requeridas
Deben configurarse en `wrangler.jsonc`:
- `CF_AI_TOKEN` - Token de API de Cloudflare
- `CF_ACCOUNT_ID` - ID de tu cuenta de Cloudflare

### Modelo IA Utilizado
- Proveedor: Cloudflare Workers AI
- Modelo: `@cf/meta/llama-3-8b-instruct`
- Tiempo: 2-5 segundos

### Respuesta
```json
{
  "sugerencia": "...recomendacion de la IA...",
  "estadisticas": {...},
  "puestos_ocupados": [...]
}
```

## Archivos del Proyecto Modificados

| Archivo | Cambio |
|---------|--------|
| `src/api/v1/puesto_trabajo.py` | +125 lineas (nueva funcion) |
| `wrangler.jsonc` | +2 variables (CF_AI_TOKEN, CF_ACCOUNT_ID) |
| `pyproject.toml` | +1 dependencia (httpx) |

## Pasos Basicos

1. **Obtener credenciales** → Ver QUICK_START.md (paso 1)
2. **Configurar variables** → Ver QUICK_START.md (paso 2)
3. **Desplegar** → Ver QUICK_START.md (paso 3)
4. **Probar endpoint** → Ver QUICK_START.md (paso 4)

## Contacto y Soporte

Para mas informacion:
- Documentacion de Cloudflare: https://developers.cloudflare.com/workers-ai/
- API Reference: https://developers.cloudflare.com/api/

## Proximo Paso

👉 **Comienza con [QUICK_START.md](QUICK_START.md)**
