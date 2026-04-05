from fastapi import APIRouter

router = APIRouter()


def _clean_row_dict(row_dict: dict) -> dict:
    clean_dict = {}
    for key, value in row_dict.items():
        if str(value) == "jsnull" or value is None:
            clean_dict[key] = None
        else:
            clean_dict[key] = value
    return clean_dict


def _row_to_dict(row) -> dict:
    if hasattr(row, "to_py"):
        return row.to_py()

    base = {
        "id": row.id,
    }

    if hasattr(row, "id_empleado"):
        base["id_empleado"] = row.id_empleado
    if hasattr(row, "fecha_creacion"):
        base["fecha_creacion"] = row.fecha_creacion
    if hasattr(row, "fecha_fin"):
        base["fecha_fin"] = row.fecha_fin
    if hasattr(row, "estado"):
        base["estado"] = row.estado
    if hasattr(row, "especificaciones"):
        base["especificaciones"] = row.especificaciones
    if hasattr(row, "destinatario"):
        base["destinatario"] = row.destinatario

    if hasattr(row, "id_solicitud"):
        base["id_solicitud"] = row.id_solicitud
    if hasattr(row, "fecha_cambio"):
        base["fecha_cambio"] = row.fecha_cambio
    if hasattr(row, "tipo_cambio"):
        base["tipo_cambio"] = row.tipo_cambio
    if hasattr(row, "estado_antiguo"):
        base["estado_antiguo"] = row.estado_antiguo
    if hasattr(row, "nuevo_estado"):
        base["nuevo_estado"] = row.nuevo_estado

    return base


def _rows_to_onboarding_response_list(rows) -> list[dict]:
    final_list = []
    for row in rows:
        final_list.append(_clean_row_dict(_row_to_dict(row)))
    return final_list


def _rows_to_history_response_list(rows) -> list[dict]:
    final_list = []
    for row in rows:
        final_list.append(_clean_row_dict(_row_to_dict(row)))
    return final_list


async def _register_history(
    db,
    id_solicitud: int,
    tipo_cambio: str,
    valor_anterior: str | None,
    valor_nuevo: str | None,
):
    await db.prepare(
        """
        INSERT INTO HISTORIAL (
            id_solicitud,
            fecha_cambio,
            tipo_cambio,
            estado_antiguo,
            nuevo_estado
        ) VALUES (?, datetime('now'), ?, ?, ?)
        """
    ).bind(id_solicitud, tipo_cambio, valor_anterior, valor_nuevo).run()
