"""Endpoint para eliminar usuario."""
from fastapi import APIRouter, HTTPException, Request, Security

try:
    from utils import require_permission
except ImportError:
    from ....utils import require_permission

router = APIRouter()


@router.delete("/usuarios/{user_id}")
async def delete_user(
    user_id: int,
    req: Request,
    token_payload: dict = Security(require_permission("usuarios.eliminar")),
):
    """
    Elimina un usuario por su ID.
    Acceso permitido solo para Root o Administrador (usuarios.eliminar).
    
    Notas de integridad:
    - Se eliminarán en cascada las solicitudes asociadas (SOLICITUDES)
    - Se eliminarán los historiales de las solicitudes (HISTORIAL)
    - Se desasignará el puesto de trabajo si lo tiene (PUESTO_DE_TRABAJO)
    """
    env = req.scope["env"]
    db = env.dataBase

    # Verificar que el usuario existe y su estado de inducción
    try:
        user = await db.prepare(
            "SELECT id, nombre, correo, estado_onboarding FROM USUARIO WHERE id = ? LIMIT 1"
        ).bind(user_id).first()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error consultando usuario: {str(e)}"
        )

    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"Usuario con ID {user_id} no encontrado"
        )

    # Prevenir eliminación del usuario actual
    current_user_id = int(token_payload.get("sub", 0))
    if user_id == current_user_id:
        raise HTTPException(
            status_code=400,
            detail="No puede eliminar su propia cuenta"
        )

    if str(getattr(user, "estado_onboarding", "")).strip().lower() == "finalizado":
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar un usuario con la inducción completada"
        )

    try:
        # 1. Obtener todas las solicitudes del usuario para marcarlas como eliminadas
        solicitudes = await db.prepare(
            "SELECT id, estado FROM SOLICITUDES WHERE id_empleado = ?"
        ).bind(user_id).all()

        # 2. Marcar cada solicitud como eliminada y registrar historial
        for solicitud_row in solicitudes.results:
            sid = solicitud_row.id
            previous_estado = getattr(solicitud_row, "estado", None)
            await db.prepare(
                "UPDATE SOLICITUDES SET estado = 'Eliminada' WHERE id = ?"
            ).bind(sid).run()

            # Registrar evento de eliminación en HISTORIAL
            old_value = "" if previous_estado is None else str(previous_estado)
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
            ).bind(sid, "ELIMINACION", old_value, "Eliminada").run()

        # 3. Marcar usuario como eliminado mediante estado_onboarding
        await db.prepare(
            "UPDATE USUARIO SET estado_onboarding = 'Eliminada' WHERE id = ?"
        ).bind(user_id).run()

        return {
            "status": "ok",
            "message": f"Usuario '{user.nombre}' (ID: {user_id}) marcado como eliminado",
            "deleted_user": {
                "id": user.id,
                "nombre": user.nombre,
                "correo": user.correo,
                "estado_onboarding": "Eliminada",
            }
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando usuario: {str(e)}"
        )
