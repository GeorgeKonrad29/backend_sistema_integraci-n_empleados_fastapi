from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Request, Security

try:
    from models import PuestoTrabajoAsignacionRequest, PuestoTrabajoResponse
    from utils import get_current_token_payload, require_permission
except ImportError:
    from ...models import PuestoTrabajoAsignacionRequest, PuestoTrabajoResponse
    from ...utils import get_current_token_payload, require_permission

router = APIRouter()

_COORDINATE_RE = re.compile(
    r"^P(?P<piso>[12])-F(?P<fila>0?[1-9]|1\d|20)-C(?P<columna>0?[1-9]|1\d|20)$"
)


def encode_coordinate(piso: int, fila: int, columna: int) -> str:
    return f"P{piso}-F{fila:02d}-C{columna:02d}"


def decode_coordinate(coordenadas: str) -> tuple[int, int, int]:
    match = _COORDINATE_RE.match(coordenadas)
    if not match:
        raise ValueError("Formato de coordenadas inválido")
    return (
        int(match.group("piso")),
        int(match.group("fila")),
        int(match.group("columna")),
    )


async def _ensure_employee_exists(db, id_empleado: int | None) -> None:
    if id_empleado is None:
        return

    employee = (
        await db.prepare("SELECT id FROM USUARIO WHERE id = ? LIMIT 1")
        .bind(id_empleado)
        .first()
    )
    if not employee:
        raise HTTPException(
            status_code=404, detail=f"El empleado con ID {id_empleado} no existe"
        )


async def _ensure_coordinate_available(db, coordenadas: str) -> None:
    occupied = (
        await db.prepare(
            "SELECT id FROM PUESTO_DE_TRABAJO WHERE coordenadas = ? LIMIT 1"
        )
        .bind(coordenadas)
        .first()
    )
    if occupied:
        raise HTTPException(
            status_code=409, detail=f"El puesto {coordenadas} ya está ocupado"
        )


def _workstation_from_row(row) -> dict:
    piso, fila, columna = decode_coordinate(row.coordenadas)
    return {
        "id": row.id,
        "id_empleado": row.id_empleado,
        "nombre_empleado": getattr(row, "nombre_empleado", None),
        "area": getattr(row, "area", None),
        "tipo_puesto": row.tipo_puesto,
        "coordenadas": row.coordenadas,
        "piso": piso,
        "fila": fila,
        "columna": columna,
        "ocupado": True,
    }


@router.post("/asignar", response_model=PuestoTrabajoResponse)
async def assign_workstation(
    payload: PuestoTrabajoAsignacionRequest,
    req: Request,
    token_payload: dict = Security(require_permission("puestos.asignar")),
):
    env = req.scope["env"]
    db = env.dataBase

    coordenadas = encode_coordinate(payload.piso, payload.fila, payload.columna)

    await _ensure_employee_exists(db, payload.id_empleado)
    await _ensure_coordinate_available(db, coordenadas)

    try:
        created = (
            await db.prepare(
                """
            INSERT INTO PUESTO_DE_TRABAJO (coordenadas, id_empleado, tipo_puesto)
            VALUES (?, ?, ?)
            RETURNING id, coordenadas, id_empleado, tipo_puesto
            """
            )
            .bind(coordenadas, payload.id_empleado, payload.tipo_puesto)
            .first()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al asignar puesto: {e}")

    if not created:
        raise HTTPException(
            status_code=500, detail="No se pudo crear la asignación del puesto"
        )

    return PuestoTrabajoResponse(
        id=created.id,
        id_empleado=created.id_empleado,
        coordenadas=created.coordenadas,
        piso=payload.piso,
        fila=payload.fila,
        columna=payload.columna,
        tipo_puesto=created.tipo_puesto,
    )


@router.get("/mapa")
async def get_workstation_map(
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    env = req.scope["env"]
    db = env.dataBase

    try:
        result = await db.prepare(
            "SELECT id, coordenadas, id_empleado, tipo_puesto FROM PUESTO_DE_TRABAJO"
        ).all()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo el mapa de puestos: {e}"
        )

    occupied = {}
    for row in result.results:
        try:
            piso, fila, columna = decode_coordinate(row.coordenadas)
            occupied[(piso, fila, columna)] = {
                "id": row.id,
                "id_empleado": row.id_empleado,
                "tipo_puesto": row.tipo_puesto,
                "coordenadas": row.coordenadas,
            }
        except Exception:
            continue

    floors = []
    for piso in (1, 2):
        rows = []
        for fila in range(1, 21):
            cols = []
            for columna in range(1, 21):
                seat = occupied.get((piso, fila, columna))
                cols.append(
                    {
                        "piso": piso,
                        "fila": fila,
                        "columna": columna,
                        "coordenadas": encode_coordinate(piso, fila, columna),
                        "ocupado": seat is not None,
                        "id_empleado": seat["id_empleado"] if seat else None,
                        "tipo_puesto": seat["tipo_puesto"] if seat else None,
                    }
                )
            rows.append(cols)
        floors.append({"piso": piso, "grid": rows})

    return {"pisos": floors}


@router.get("/ocupadas")
async def get_occupied_workstations(
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    env = req.scope["env"]
    db = env.dataBase

    try:
        result = await db.prepare(
            """
            SELECT p.id, p.coordenadas, p.id_empleado, p.tipo_puesto, u.nombre AS nombre_empleado, j.area AS area
            FROM PUESTO_DE_TRABAJO p
            INNER JOIN USUARIO u ON u.id = p.id_empleado
            INNER JOIN JERARQUIA j ON j.id = u.cargo
            WHERE p.id_empleado IS NOT NULL
            ORDER BY p.coordenadas
            """
        ).all()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo los puestos ocupados: {e}"
        )

    occupied = []
    for row in result.results:
        try:
            occupied.append(_workstation_from_row(row))
        except Exception:
            continue

    return {"ocupadas": occupied, "count": len(occupied)}


@router.post("/sugerencia")
async def get_workstation_suggestion(
    payload: PuestoTrabajoAsignacionRequest,
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    import json

    env = req.scope["env"]
    db = env.dataBase
    ai = env.AI

    # 1. Obtener informacion del empleado a asignar
    empleado_info = None
    if payload.id_empleado:
        try:
            empleado = (
                await db.prepare(
                    "SELECT u.id, u.nombre, j.area FROM USUARIO u INNER JOIN JERARQUIA j ON j.id = u.cargo WHERE u.id = ? LIMIT 1"
                )
                .bind(payload.id_empleado)
                .first()
            )
            if empleado:
                empleado_info = {
                    "id": empleado.id,
                    "nombre": empleado.nombre,
                    "area": empleado.area,
                }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"[Paso 1 - Consulta de empleado] "
                    f"{type(e).__name__} al buscar empleado con id={payload.id_empleado}: {e}"
                ),
            )

    # 2. Obtener todos los puestos ocupados con informacion de empleados
    try:
        result = await db.prepare(
            """
            SELECT p.id, p.coordenadas, p.id_empleado, p.tipo_puesto, u.nombre AS nombre_empleado, j.area AS area
            FROM PUESTO_DE_TRABAJO p
            INNER JOIN USUARIO u ON u.id = p.id_empleado
            INNER JOIN JERARQUIA j ON j.id = u.cargo
            WHERE p.id_empleado IS NOT NULL
            ORDER BY p.coordenadas
            """
        ).all()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"[Paso 2 - Consulta de puestos ocupados] "
                f"{type(e).__name__} al ejecutar SELECT en PUESTO_DE_TRABAJO: {e}"
            ),
        )

    # 3. Procesar los datos de puestos ocupados
    ocupados = []
    filas_invalidas = []
    for row in result.results:
        try:
            ocupado_info = _workstation_from_row(row)
            ocupados.append(ocupado_info)
        except Exception as e:
            filas_invalidas.append(
                {"coordenadas": getattr(row, "coordenadas", "?"), "error": f"{type(e).__name__}: {e}"}
            )
            continue

    # 4. Contar puestos ocupados por tipo y area
    estadisticas = {
        "total_ocupados": len(ocupados),
        "por_tipo": {},
        "por_area": {},
    }

    for ocupado in ocupados:
        tipo = ocupado.get("tipo_puesto", "desconocido")
        area = ocupado.get("area", "desconocido")

        if tipo not in estadisticas["por_tipo"]:
            estadisticas["por_tipo"][tipo] = 0
        estadisticas["por_tipo"][tipo] += 1

        if area not in estadisticas["por_area"]:
            estadisticas["por_area"][area] = 0
        estadisticas["por_area"][area] += 1

    # 5. Preparar el prompt para la IA con informacion del empleado a asignar
    empleado_context = ""
    if empleado_info:
        empleado_context = f"""
Empleado a asignar:
- ID: {empleado_info["id"]}
- Nombre: {empleado_info["nombre"]}
- Area: {empleado_info["area"]}
- Tipo de puesto solicitado: {payload.tipo_puesto or "No especificado"}
"""


    prompt = f"""Eres un asistente especializado en optimizacion de distribucion de espacios de trabajo en una oficina.
{empleado_context}
Datos actuales de puestos de trabajo asignados:
- Total de puestos ocupados: {estadisticas["total_ocupados"]}
- Distribucion por tipo de puesto: {json.dumps(estadisticas["por_tipo"])}
- Distribucion por area: {json.dumps(estadisticas["por_area"])}

Listado completo de puestos ocupados:
{json.dumps(ocupados, ensure_ascii=False, indent=2)}

Basandote en esta informacion, proporciona una lista de EXACTAMENTE 5 mejores posiciones para asignar el puesto de trabajo.

Para cada posicion, proporciona:
1. La ubicacion (formato: Piso X, Fila Y, Columna Z)
2. Una puntuacion de 1-5 estrellas
3. Una breve explicacion de por que es recomendada (máximo 2 lineas)

Ordenarlas de mejor a peor (5 estrellas primero).

Formato de respuesta:
Posicion 1: Piso X, Fila Y, Columna Z | Puntuacion: X/5
Razon: [explicacion]

Posicion 2: Piso X, Fila Y, Columna Z | Puntuacion: X/5
Razon: [explicacion]

(continua para posiciones 3, 4 y 5)

Ten en cuenta:
1. La distribucion actual de empleados en su area
2. El balance entre diferentes tipos de puestos
3. La distribucion geografica (piso, fila, columna)
4. Proximidad a colegas del mismo area
5. el output final es estricto, una lista del 1 al 5 con las coordenadas, la puntuacion y la razon en una frase pequeña
, sin transicion, sin texto de inicio o final, simplemente la lista de la forma indicada"""


    _AI_MODEL = "@cf/meta/llama-3.1-8b-instruct"
    try:
        ai_response_raw = await ai.run(_AI_MODEL, {"prompt": prompt})
        ai_response = ai_response_raw.to_py()  # JsProxy → dict Python
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"[Paso 6 - Llamada a Workers AI] {type(e).__name__}: {e}",
        )

    # 7. Extraer campos del esquema: { "response": str, "usage": { ... } }
    suggestion_text = ai_response.get("response", "") if isinstance(ai_response, dict) else str(ai_response)
    usage = ai_response.get("usage") if isinstance(ai_response, dict) else None
    if not suggestion_text:
        raise HTTPException(
            status_code=500,
            detail=f"[Paso 7] La IA retornó una respuesta vacía. Tipo recibido: {type(ai_response).__name__}",
        )

    # 8. Parsear las posiciones recomendadas de la respuesta de la IA
    try:
        posiciones = _parse_ai_suggestions(suggestion_text)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"[Paso 8 - Parsing de sugerencias IA] {type(e).__name__}: {e}",
        )

    return {
        "posiciones_recomendadas": posiciones,
        "respuesta_ia_completa": suggestion_text,
        "estadisticas": estadisticas,
        "puestos_ocupados": ocupados,
        "empleado": empleado_info,
        "tipo_puesto_solicitado": payload.tipo_puesto,
        "uso_tokens": usage,
        "advertencias": (
            [{"tipo": "filas_invalidas", "detalle": filas_invalidas}]
            if filas_invalidas
            else []
        ),
    }


def _parse_ai_suggestions(response_text: str) -> list[dict]:
    """
    Parsea la respuesta de la IA para extraer las 5 posiciones recomendadas.
    Retorna una lista de diccionarios con: posicion, piso, fila, columna, puntuacion, razon
    """
    import re

    posiciones = []
    lines = response_text.split("\n")

    posicion_actual = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Buscar linea de posicion (ej: "Posicion 1: Piso 1, Fila 5, Columna 10 | Puntuacion: 5/5")
        posicion_match = re.search(
            r"Posicion\s+(\d+):\s*Piso\s+(\d+),\s*Fila\s+(\d+),\s*Columna\s+(\d+).*Puntuacion:\s*(\d+)/5",
            line,
            re.IGNORECASE,
        )

        if posicion_match:
            # Si habia una posicion anterior, guardarla
            if posicion_actual:
                posiciones.append(posicion_actual)

            # Crear nueva posicion
            posicion_actual = {
                "numero": int(posicion_match.group(1)),
                "piso": int(posicion_match.group(2)),
                "fila": int(posicion_match.group(3)),
                "columna": int(posicion_match.group(4)),
                "coordenadas": f"P{posicion_match.group(2)}-F{int(posicion_match.group(3)):02d}-C{int(posicion_match.group(4)):02d}",
                "puntuacion": int(posicion_match.group(5)),
                "razon": "",
            }

        # Buscar linea de razon (ej: "Razon: ...")
        razon_match = re.search(r"Razon:\s*(.+)", line, re.IGNORECASE)
        if razon_match and posicion_actual:
            posicion_actual["razon"] = razon_match.group(1).strip()

    # Agregar la ultima posicion si existe
    if posicion_actual:
        posiciones.append(posicion_actual)

    # Si no se encontraron posiciones con el patron, intentar un parsing mas flexible
    if not posiciones:
        posiciones = _parse_ai_suggestions_flexible(response_text)

    # Ordenar por puntuacion descendente (mejor primero)
    posiciones.sort(key=lambda x: x.get("puntuacion", 0), reverse=True)

    # Limitar a 5 posiciones
    return posiciones[:5]


def _parse_ai_suggestions_flexible(response_text: str) -> list[dict]:
    """
    Parsing mas flexible si el formato no es exacto.
    Intenta extraer posiciones usando patrones mas generales.
    """
    import re

    posiciones = []

    # Buscar todos los bloques que contengan "Piso", "Fila", "Columna"
    pattern = r"(?:Posicion\s+\d+:|\d+\.)\s*(?:Piso|P)\s+(\d+),?\s*(?:Fila|F)\s+(\d+),?\s*(?:Columna|C)\s+(\d+)"
    matches = re.finditer(pattern, response_text, re.IGNORECASE)

    posicion_num = 1
    for match in matches:
        piso = int(match.group(1))
        fila = int(match.group(2))
        columna = int(match.group(3))

        # Buscar puntuacion cercana
        context_start = max(0, match.start() - 100)
        context_end = min(len(response_text), match.end() + 100)
        context = response_text[context_start:context_end]

        puntuacion_match = re.search(r"(\d+)/5", context)
        puntuacion = int(puntuacion_match.group(1)) if puntuacion_match else 3

        # Buscar razon
        razon_match = re.search(
            r"Razon[:]?\s*(.+?)(?:\n|Posicion|$)", context, re.IGNORECASE
        )
        razon = razon_match.group(1).strip() if razon_match else "Ubicacion recomendada"

        posiciones.append(
            {
                "numero": posicion_num,
                "piso": piso,
                "fila": fila,
                "columna": columna,
                "coordenadas": f"P{piso}-F{fila:02d}-C{columna:02d}",
                "puntuacion": puntuacion,
                "razon": razon,
            }
        )

        posicion_num += 1

    return posiciones