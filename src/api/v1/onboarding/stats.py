from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from statistics import mean

from fastapi import APIRouter, HTTPException, Query, Request, Security
from pydantic import BaseModel, ConfigDict

try:
    from utils import require_permission
except ImportError:
    from ....utils import require_permission

router = APIRouter()

_TERMINAL_STATES = {"Finalizado", "Rechazado"}
_ALLOWED_STATES = {"Pendiente", "En proceso", "Finalizado", "Rechazado"}


class EstadoRendimientoResponse(BaseModel):
    estado: str
    cantidad_solicitudes: int
    tiempo_promedio_minutos: float | None = None
    tiempo_minimo_minutos: float | None = None
    tiempo_maximo_minutos: float | None = None
    percentil_50_minutos: float | None = None
    percentil_90_minutos: float | None = None


class TopRendimientoItemResponse(BaseModel):
    nombre: str
    cantidad_solicitudes: int
    tiempo_promedio_total_minutos: float | None = None
    percentil_50_minutos: float | None = None
    percentil_90_minutos: float | None = None


class ResumenRendimientoResponse(BaseModel):
    total_solicitudes: int
    solicitudes_finalizadas: int
    solicitudes_rechazadas: int
    solicitudes_activas: int
    tasa_cierre: float
    tiempo_promedio_total_minutos: float | None = None
    percentil_50_total_minutos: float | None = None
    percentil_90_total_minutos: float | None = None
    estado_mas_lento: str | None = None
    por_estado: list[EstadoRendimientoResponse]
    top_destinatarios_lentos: list[TopRendimientoItemResponse]
    top_tipos_solicitud_lentos: list[TopRendimientoItemResponse]


class DesempenioDestinatarioResponse(BaseModel):
    destinatario: str
    cantidad_solicitudes: int
    solicitudes_finalizadas: int
    solicitudes_rechazadas: int
    solicitudes_activas: int
    tasa_cierre: float
    tiempo_promedio_total_minutos: float | None = None
    percentil_50_minutos: float | None = None
    percentil_90_minutos: float | None = None


class DesempenioTipoSolicitudResponse(BaseModel):
    especificacion: str
    cantidad_solicitudes: int
    solicitudes_finalizadas: int
    solicitudes_rechazadas: int
    solicitudes_activas: int
    tasa_cierre: float
    tiempo_promedio_total_minutos: float | None = None
    percentil_50_minutos: float | None = None
    percentil_90_minutos: float | None = None


class EventoTimelineResponse(BaseModel):
    fecha: str
    solicitudes_finalizadas: int
    solicitudes_rechazadas: int
    solicitudes_cerradas: int
    tiempo_promedio_cierre_minutos: float | None = None


class TimelineRendimientoResponse(BaseModel):
    fecha_inicio: str
    fecha_fin: str
    eventos: list[EventoTimelineResponse]

    model_config = ConfigDict(from_attributes=True)


def _row_to_dict(row) -> dict:
    if hasattr(row, "to_py"):
        return row.to_py()

    data = {}
    for key in (
        "id",
        "id_empleado",
        "fecha_creacion",
        "fecha_fin",
        "estado",
        "especificaciones",
        "destinatario",
        "nombre_empleado",
        "cargo_empleado",
        "nombre_cargo",
        "area",
        "id_solicitud",
        "fecha_cambio",
        "tipo_cambio",
        "estado_antiguo",
        "nuevo_estado",
    ):
        if hasattr(row, key):
            data[key] = getattr(row, key)
    return data


def _parse_datetime(value: str | datetime | None, field_name: str) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value

    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"{field_name} debe tener formato ISO-8601") from exc


async def _fetch_source_data(db) -> tuple[list[dict], dict[int, list[dict]]]:
    solicitudes_result = await db.prepare(
        """
        SELECT s.id, s.id_empleado, s.fecha_creacion, s.fecha_fin, s.estado, s.especificaciones, s.destinatario,
               u.nombre AS nombre_empleado, u.cargo AS cargo_empleado,
               j.nombre_cargo, j.area
        FROM SOLICITUDES s
        JOIN USUARIO u ON u.id = s.id_empleado
        JOIN JERARQUIA j ON j.id = u.cargo
        ORDER BY s.id
        """
    ).all()

    historial_result = await db.prepare(
        """
        SELECT id, id_solicitud, fecha_cambio, tipo_cambio, estado_antiguo, nuevo_estado
        FROM HISTORIAL
        ORDER BY id_solicitud, fecha_cambio ASC, id ASC
        """
    ).all()

    solicitudes = [_row_to_dict(row) for row in solicitudes_result.results]
    historial_por_solicitud: dict[int, list[dict]] = defaultdict(list)
    for row in historial_result.results:
        hist = _row_to_dict(row)
        solicitud_id = hist.get("id_solicitud")
        if solicitud_id is not None:
            historial_por_solicitud[int(solicitud_id)].append(hist)

    return solicitudes, historial_por_solicitud


def _filter_by_date_range(records: list[dict], fecha_desde: datetime | None, fecha_hasta: datetime | None) -> list[dict]:
    if fecha_desde is None and fecha_hasta is None:
        return records

    filtered: list[dict] = []
    for record in records:
        created_at = _parse_datetime(record.get("fecha_creacion"), "fecha_creacion")
        if created_at is None:
            continue
        if fecha_desde is not None and created_at < fecha_desde:
            continue
        if fecha_hasta is not None and created_at > fecha_hasta:
            continue
        filtered.append(record)
    return filtered


def _state_key(value: str | None) -> str:
    text = str(value or "").strip()
    return text or "Sin estado"


def _text_key(value: str | None, default: str) -> str:
    text = str(value or "").strip()
    return text or default


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]

    sorted_values = sorted(values)
    rank = (len(sorted_values) - 1) * percentile
    low_index = int(rank)
    high_index = min(low_index + 1, len(sorted_values) - 1)
    weight = rank - low_index
    return sorted_values[low_index] * (1 - weight) + sorted_values[high_index] * weight


def _compute_request_metrics(solicitud: dict, historial: list[dict]) -> dict:
    created_at = _parse_datetime(solicitud.get("fecha_creacion"), "fecha_creacion")
    if created_at is None:
        raise ValueError("Solicitud sin fecha de creacion valida")

    now = datetime.now(created_at.tzinfo) if created_at.tzinfo is not None else datetime.now()

    state_events: list[tuple[datetime, str]] = []
    initial_state = _state_key(solicitud.get("estado"))
    for item in historial:
        if str(item.get("tipo_cambio") or "") == "CREACION":
            initial_state = _state_key(item.get("nuevo_estado") or initial_state)
            continue
        if str(item.get("tipo_cambio") or "") != "CAMBIO_ESTADO":
            continue
        event_time = _parse_datetime(item.get("fecha_cambio"), "fecha_cambio")
        if event_time is None:
            continue
        next_state = _state_key(item.get("nuevo_estado"))
        state_events.append((event_time, next_state))

    state_events.sort(key=lambda item: item[0])

    elapsed_by_state: dict[str, float] = defaultdict(float)
    previous_time = created_at
    previous_state = initial_state
    terminal_time: datetime | None = None

    for event_time, next_state in state_events:
        if event_time < previous_time:
            continue
        delta_minutes = (event_time - previous_time).total_seconds() / 60.0
        if delta_minutes >= 0:
            elapsed_by_state[previous_state] += delta_minutes
        previous_time = event_time
        previous_state = next_state
        if previous_state in _TERMINAL_STATES and terminal_time is None:
            terminal_time = event_time

    if previous_state not in _TERMINAL_STATES:
        delta_minutes = (now - previous_time).total_seconds() / 60.0
        if delta_minutes >= 0:
            elapsed_by_state[previous_state] += delta_minutes

    total_elapsed = (terminal_time or now) - created_at
    total_minutes = max(total_elapsed.total_seconds() / 60.0, 0.0)

    return {
        "id": solicitud.get("id"),
        "destinatario": _text_key(solicitud.get("destinatario"), "Sin destinatario"),
        "especificacion": _text_key(solicitud.get("especificaciones"), "Sin especificacion"),
        "estado_actual": _state_key(solicitud.get("estado")),
        "total_minutes": total_minutes,
        "elapsed_by_state": elapsed_by_state,
        "finalized_at": terminal_time,
    }


def _build_estado_summary(computed_requests: list[dict]) -> list[EstadoRendimientoResponse]:
    by_state: dict[str, list[float]] = defaultdict(list)
    for item in computed_requests:
        for state_name, minutes in item["elapsed_by_state"].items():
            by_state[state_name].append(minutes)

    summary: list[EstadoRendimientoResponse] = []
    for state_name in sorted(by_state.keys()):
        values = by_state[state_name]
        summary.append(
            EstadoRendimientoResponse(
                estado=state_name,
                cantidad_solicitudes=len(values),
                tiempo_promedio_minutos=round(mean(values), 2) if values else None,
                tiempo_minimo_minutos=round(min(values), 2) if values else None,
                tiempo_maximo_minutos=round(max(values), 2) if values else None,
                percentil_50_minutos=round(_percentile(values, 0.5), 2) if values else None,
                percentil_90_minutos=round(_percentile(values, 0.9), 2) if values else None,
            )
        )
    return summary


def _build_group_summary(computed_requests: list[dict], group_key: str, field_name: str) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in computed_requests:
        grouped[item[group_key]].append(item)

    summary: list[dict] = []
    for key_name in sorted(grouped.keys()):
        items = grouped[key_name]
        finished = sum(1 for item in items if item["estado_actual"] == "Finalizado")
        rejected = sum(1 for item in items if item["estado_actual"] == "Rechazado")
        active = len(items) - finished - rejected
        total_minutes = [item["total_minutes"] for item in items]
        closure_rate = ((finished + rejected) / len(items) * 100.0) if items else 0.0
        summary.append(
            {
                field_name: key_name,
                "cantidad_solicitudes": len(items),
                "solicitudes_finalizadas": finished,
                "solicitudes_rechazadas": rejected,
                "solicitudes_activas": active,
                "tasa_cierre": round(closure_rate, 2),
                "tiempo_promedio_total_minutos": round(mean(total_minutes), 2) if total_minutes else None,
                "percentil_50_minutos": round(_percentile(total_minutes, 0.5), 2) if total_minutes else None,
                "percentil_90_minutos": round(_percentile(total_minutes, 0.9), 2) if total_minutes else None,
            }
        )

    summary.sort(key=lambda item: item.get("tiempo_promedio_total_minutos") or 0.0, reverse=True)
    return summary


def _build_top_items(grouped_summary: list[dict], field_name: str, top_n: int = 5) -> list[TopRendimientoItemResponse]:
    tops: list[TopRendimientoItemResponse] = []
    for item in grouped_summary[: max(top_n, 0)]:
        tops.append(
            TopRendimientoItemResponse(
                nombre=str(item.get(field_name) or "Sin nombre"),
                cantidad_solicitudes=int(item.get("cantidad_solicitudes") or 0),
                tiempo_promedio_total_minutos=item.get("tiempo_promedio_total_minutos"),
                percentil_50_minutos=item.get("percentil_50_minutos"),
                percentil_90_minutos=item.get("percentil_90_minutos"),
            )
        )
    return tops


def _build_timeline(computed_requests: list[dict], fecha_inicio: datetime, fecha_fin: datetime) -> list[EventoTimelineResponse]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in computed_requests:
        finalized_at = item["finalized_at"]
        if finalized_at is None:
            continue
        day_key = finalized_at.date().isoformat()
        grouped[day_key].append(item)

    events: list[EventoTimelineResponse] = []
    current_day = fecha_inicio.date()
    end_day = fecha_fin.date()
    while current_day <= end_day:
        day_key = current_day.isoformat()
        items = grouped.get(day_key, [])
        finished = sum(1 for item in items if item["estado_actual"] == "Finalizado")
        rejected = sum(1 for item in items if item["estado_actual"] == "Rechazado")
        closed = finished + rejected
        total_minutes = [item["total_minutes"] for item in items]
        events.append(
            EventoTimelineResponse(
                fecha=day_key,
                solicitudes_finalizadas=finished,
                solicitudes_rechazadas=rejected,
                solicitudes_cerradas=closed,
                tiempo_promedio_cierre_minutos=round(mean(total_minutes), 2) if total_minutes else None,
            )
        )
        current_day = current_day + timedelta(days=1)

    return events


async def _collect_computed_requests(
    db,
    fecha_desde: datetime | None,
    fecha_hasta: datetime | None,
) -> tuple[list[dict], list[dict]]:
    solicitudes, historial_por_solicitud = await _fetch_source_data(db)
    solicitudes = _filter_by_date_range(solicitudes, fecha_desde, fecha_hasta)

    computed: list[dict] = []
    for solicitud in solicitudes:
        solicitud_id = solicitud.get("id")
        history_rows = historial_por_solicitud.get(int(solicitud_id), []) if solicitud_id is not None else []
        try:
            computed.append(_compute_request_metrics(solicitud, history_rows))
        except ValueError:
            continue

    return solicitudes, computed


@router.get("/estadisticas/resumen-general", response_model=ResumenRendimientoResponse)
async def get_resumen_general_rendimiento(
    req: Request,
    token_payload: dict = Security(require_permission("onboarding.estadisticas")),
    fecha_desde: str | None = Query(default=None),
    fecha_hasta: str | None = Query(default=None),
):
    env = req.scope["env"]
    db = env.dataBase

    fecha_desde_dt = _parse_datetime(fecha_desde, "fecha_desde")
    fecha_hasta_dt = _parse_datetime(fecha_hasta, "fecha_hasta")

    if fecha_desde_dt and fecha_hasta_dt and fecha_desde_dt > fecha_hasta_dt:
        raise HTTPException(status_code=400, detail="fecha_desde no puede ser mayor que fecha_hasta")

    solicitudes, computed = await _collect_computed_requests(db, fecha_desde_dt, fecha_hasta_dt)
    if not solicitudes:
        return ResumenRendimientoResponse(
            total_solicitudes=0,
            solicitudes_finalizadas=0,
            solicitudes_rechazadas=0,
            solicitudes_activas=0,
            tasa_cierre=0.0,
            tiempo_promedio_total_minutos=None,
            percentil_50_total_minutos=None,
            percentil_90_total_minutos=None,
            estado_mas_lento=None,
            por_estado=[],
            top_destinatarios_lentos=[],
            top_tipos_solicitud_lentos=[],
        )

    finished = sum(1 for item in computed if item["estado_actual"] == "Finalizado")
    rejected = sum(1 for item in computed if item["estado_actual"] == "Rechazado")
    active = len(computed) - finished - rejected
    total_minutes = [item["total_minutes"] for item in computed]
    estado_summary = _build_estado_summary(computed)
    estado_mas_lento = None
    if estado_summary:
        estado_mas_lento = max(
            estado_summary,
            key=lambda item: item.tiempo_promedio_minutos or 0.0,
        ).estado

    closure_rate = ((finished + rejected) / len(computed) * 100.0) if computed else 0.0
    top_destinatarios = _build_top_items(
        _build_group_summary(computed, "destinatario", "destinatario"),
        "destinatario",
        top_n=5,
    )
    top_tipos = _build_top_items(
        _build_group_summary(computed, "especificacion", "especificacion"),
        "especificacion",
        top_n=5,
    )

    return ResumenRendimientoResponse(
        total_solicitudes=len(computed),
        solicitudes_finalizadas=finished,
        solicitudes_rechazadas=rejected,
        solicitudes_activas=active,
        tasa_cierre=round(closure_rate, 2),
        tiempo_promedio_total_minutos=round(mean(total_minutes), 2) if total_minutes else None,
        percentil_50_total_minutos=round(_percentile(total_minutes, 0.5), 2) if total_minutes else None,
        percentil_90_total_minutos=round(_percentile(total_minutes, 0.9), 2) if total_minutes else None,
        estado_mas_lento=estado_mas_lento,
        por_estado=estado_summary,
        top_destinatarios_lentos=top_destinatarios,
        top_tipos_solicitud_lentos=top_tipos,
    )


@router.get("/estadisticas/desempenio-por-destinatario", response_model=list[DesempenioDestinatarioResponse])
async def get_desempenio_por_destinatario(
    req: Request,
    token_payload: dict = Security(require_permission("onboarding.estadisticas")),
    fecha_desde: str | None = Query(default=None),
    fecha_hasta: str | None = Query(default=None),
    top_n: int | None = Query(default=None, ge=1, le=100),
):
    env = req.scope["env"]
    db = env.dataBase

    fecha_desde_dt = _parse_datetime(fecha_desde, "fecha_desde")
    fecha_hasta_dt = _parse_datetime(fecha_hasta, "fecha_hasta")

    if fecha_desde_dt and fecha_hasta_dt and fecha_desde_dt > fecha_hasta_dt:
        raise HTTPException(status_code=400, detail="fecha_desde no puede ser mayor que fecha_hasta")

    solicitudes, computed = await _collect_computed_requests(db, fecha_desde_dt, fecha_hasta_dt)
    if not solicitudes:
        return []

    grouped = _build_group_summary(computed, "destinatario", "destinatario")
    if top_n is not None:
        grouped = grouped[:top_n]
    return [DesempenioDestinatarioResponse.model_validate(item) for item in grouped]


@router.get("/estadisticas/desempenio-por-solicitud", response_model=list[DesempenioTipoSolicitudResponse])
async def get_desempenio_por_tipo_solicitud(
    req: Request,
    token_payload: dict = Security(require_permission("onboarding.estadisticas")),
    fecha_desde: str | None = Query(default=None),
    fecha_hasta: str | None = Query(default=None),
    top_n: int | None = Query(default=None, ge=1, le=100),
):
    env = req.scope["env"]
    db = env.dataBase

    fecha_desde_dt = _parse_datetime(fecha_desde, "fecha_desde")
    fecha_hasta_dt = _parse_datetime(fecha_hasta, "fecha_hasta")

    if fecha_desde_dt and fecha_hasta_dt and fecha_desde_dt > fecha_hasta_dt:
        raise HTTPException(status_code=400, detail="fecha_desde no puede ser mayor que fecha_hasta")

    solicitudes, computed = await _collect_computed_requests(db, fecha_desde_dt, fecha_hasta_dt)
    if not solicitudes:
        return []

    grouped = _build_group_summary(computed, "especificacion", "especificacion")
    if top_n is not None:
        grouped = grouped[:top_n]
    return [DesempenioTipoSolicitudResponse.model_validate(item) for item in grouped]


@router.get("/estadisticas/timeline", response_model=TimelineRendimientoResponse)
async def get_timeline_rendimiento(
    req: Request,
    token_payload: dict = Security(require_permission("onboarding.estadisticas")),
    fecha_desde: str | None = Query(default=None),
    fecha_hasta: str | None = Query(default=None),
):
    env = req.scope["env"]
    db = env.dataBase

    fecha_desde_dt = _parse_datetime(fecha_desde, "fecha_desde")
    fecha_hasta_dt = _parse_datetime(fecha_hasta, "fecha_hasta")

    if fecha_desde_dt and fecha_hasta_dt and fecha_desde_dt > fecha_hasta_dt:
        raise HTTPException(status_code=400, detail="fecha_desde no puede ser mayor que fecha_hasta")

    now = datetime.now()
    if fecha_hasta_dt is None:
        fecha_hasta_dt = now
    if fecha_desde_dt is None:
        fecha_desde_dt = fecha_hasta_dt - timedelta(days=30)

    if fecha_desde_dt > fecha_hasta_dt:
        raise HTTPException(status_code=400, detail="fecha_desde no puede ser mayor que fecha_hasta")

    _, computed = await _collect_computed_requests(db, fecha_desde_dt, fecha_hasta_dt)
    events = _build_timeline(computed, fecha_desde_dt, fecha_hasta_dt)

    return TimelineRendimientoResponse(
        fecha_inicio=fecha_desde_dt.date().isoformat(),
        fecha_fin=fecha_hasta_dt.date().isoformat(),
        eventos=events,
    )
