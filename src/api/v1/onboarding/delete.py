"""Endpoints para eliminar solicitudes de onboarding."""
from fastapi import APIRouter, HTTPException, Request, Security

from .common import _clean_row_dict, _register_history, _row_to_dict

try:
    from utils import (
        can_delete_onboarding_request,
        get_current_token_payload,
        get_payload_cargo,
    )
except ImportError:
    from ....utils import (
        can_delete_onboarding_request,
        get_current_token_payload,
        get_payload_cargo,
    )

router = APIRouter()


@router.delete("/solicitudes/{solicitud_id}")
async def delete_onboarding_request(
    solicitud_id: int,
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    """
    Elimina una solicitud de onboarding por su ID.
    Acceso permitido para:
    - RRHH (Administrador o Gerente Talento Humano)
    - El jefe inmediato del empleado que creó la solicitud
    
    Eliminará también:
    - El historial de cambios asociado a la solicitud
    """
    env = req.scope["env"]
    db = env.dataBase

    # Verificar que la solicitud existe
    try:
        solicitud = await db.prepare(
            """
            SELECT s.id, s.id_empleado, s.fecha_creacion, s.estado, 
                   u.cargo, u.nombre as nombre_empleado
            FROM SOLICITUDES s
            JOIN USUARIO u ON u.id = s.id_empleado
            WHERE s.id = ? LIMIT 1
            """
        ).bind(solicitud_id).first()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error consultando solicitud: {str(e)}"
        )

    if not solicitud:
        raise HTTPException(
            status_code=404,
            detail=f"Solicitud con ID {solicitud_id} no encontrada"
        )

    # Verificar estado: no se puede eliminar si está en proceso
    estado_solicitud = getattr(solicitud, "estado", "").strip()
    if estado_solicitud.lower() == "en proceso":
        raise HTTPException(
            status_code=409,
            detail="No puede eliminar una solicitud que fue aceptada (En proceso). Solo el jefe puede rechazarla."
        )

    # Verificar permisos
    try:
        creator_cargo = get_payload_cargo(token_payload)
        empleado_cargo = getattr(solicitud, "cargo", None)
        
        can_delete = await can_delete_onboarding_request(
            db, creator_cargo, empleado_cargo
        )

        if not can_delete:
            raise HTTPException(
                status_code=403,
                detail="No tiene permisos para eliminar esta solicitud. Solo RRHH o el jefe inmediato pueden hacerlo."
            )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validando permisos: {str(e)}"
        )

    try:
        # 1. Eliminar historial de la solicitud
        await db.prepare(
            "DELETE FROM HISTORIAL WHERE id_solicitud = ?"
        ).bind(solicitud_id).run()

        # 2. Eliminar la solicitud
        await db.prepare(
            "DELETE FROM SOLICITUDES WHERE id = ?"
        ).bind(solicitud_id).run()

        return {
            "status": "ok",
            "message": f"Solicitud de onboarding (ID: {solicitud_id}) eliminada correctamente",
            "deleted_request": {
                "id": solicitud.id,
                "id_empleado": solicitud.id_empleado,
                "nombre_empleado": solicitud.nombre_empleado,
                "fecha_creacion": solicitud.fecha_creacion,
                "estado": solicitud.estado,
            }
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando solicitud: {str(e)}"
        )


@router.delete("/solicitudes")
async def delete_my_onboarding_requests(
    req: Request,
    token_payload: dict = Security(get_current_token_payload),
):
    """
    Elimina todas las solicitudes pendientes del usuario actual.
    Solo elimina solicitudes cuyo estado es 'Pendiente'.
    """
    env = req.scope["env"]
    db = env.dataBase

    user_id = int(token_payload.get("sub", 0))

    try:
        # Obtener todas las solicitudes pendientes del usuario
        solicitudes = await db.prepare(
            "SELECT id FROM SOLICITUDES WHERE id_empleado = ? AND estado = 'Pendiente'"
        ).bind(user_id).all()

        if not solicitudes.results:
            return {
                "status": "ok",
                "message": "No hay solicitudes pendientes para eliminar",
                "deleted_count": 0,
            }

        deleted_ids = []
        
        # Eliminar cada solicitud y su historial
        for solicitud_row in solicitudes.results:
            sid = solicitud_row.id
            
            # Eliminar historial
            await db.prepare(
                "DELETE FROM HISTORIAL WHERE id_solicitud = ?"
            ).bind(sid).run()

            # Eliminar solicitud
            await db.prepare(
                "DELETE FROM SOLICITUDES WHERE id = ?"
            ).bind(sid).run()

            deleted_ids.append(sid)

        return {
            "status": "ok",
            "message": f"{len(deleted_ids)} solicitud(es) pendiente(s) eliminada(s)",
            "deleted_count": len(deleted_ids),
            "deleted_ids": deleted_ids,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando solicitudes: {str(e)}"
        )
