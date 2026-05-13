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


@router.get("/sugerencia")
async def get_workstation_suggestion(
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    import json

    import httpx

    env = req.scope["env"]
    db = env.dataBase

    # 1. Obtener todos los puestos ocupados con informacion de empleados
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

    # 2. Procesar los datos de puestos ocupados
    ocupados = []
    for row in result.results:
        try:
            ocupado_info = _workstation_from_row(row)
            ocupados.append(ocupado_info)
        except Exception:
            continue

    # 3. Contar puestos ocupados por tipo y area
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

    # 4. Preparar el prompt para la IA
    prompt = f"""Eres un asistente especializado en optimizacion de distribucion de espacios de trabajo en una oficina.

Datos actuales de puestos de trabajo asignados:
- Total de puestos ocupados: {estadisticas["total_ocupados"]}
- Distribucion por tipo de puesto: {json.dumps(estadisticas["por_tipo"])}
- Distribucion por area: {json.dumps(estadisticas["por_area"])}

Listado completo de puestos ocupados:
{json.dumps(ocupados, ensure_ascii=False, indent=2)}

Basandote en esta informacion, proporciona una sugerencia sobre donde deberia ir un nuevo empleado a asignar su puesto de trabajo.
Ten en cuenta:
1. La distribucion actual de empleados por area
2. El balance entre diferentes tipos de puestos
3. La distribucion geografica (piso, fila, columna)

Proporciona una recomendacion clara y concisa sobre donde deberia ser asignado el nuevo puesto (piso, fila, columna aproximados) y por que."""

    # 5. Llamar a Cloudflare Worker AI
    try:
        # En Cloudflare Workers, las variables se acceden como atributos del objeto env
        cf_token = getattr(env, "CF_AI_TOKEN", None)
        cf_account_id = getattr(env, "CF_ACCOUNT_ID", None)

        if not cf_token or not cf_account_id:
            raise HTTPException(
                status_code=500,
                detail="Credenciales de Cloudflare AI no configuradas. Verifica CF_AI_TOKEN y CF_ACCOUNT_ID en wrangler.jsonc",
            )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/ai/run/@cf/meta/llama-3-8b-instruct",
                headers={"Authorization": f"Bearer {cf_token}"},
                json={
                    "messages": [
                        {
                            "role": "system",
                            "content": "Eres un asistente especializado en optimizacion de espacios de trabajo",
                        },
                        {"role": "user", "content": prompt},
                    ]
                },
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Error llamando a Cloudflare AI: {response.text}",
            )

        ai_response = response.json()
        suggestion = ai_response.get("result", {}).get("response", "")

        return {
            "sugerencia": suggestion,
            "estadisticas": estadisticas,
            "puestos_ocupados": ocupados,
        }
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500, detail=f"Error en la solicitud HTTP: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo sugerencia: {str(e)}"
        )
