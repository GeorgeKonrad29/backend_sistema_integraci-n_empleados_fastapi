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
        # 1. Obtener todas las solicitudes del usuario para eliminar historiales
        solicitudes = await db.prepare(
            "SELECT id FROM SOLICITUDES WHERE id_empleado = ?"
        ).bind(user_id).all()

        # 2. Eliminar historiales de las solicitudes
        for solicitud_row in solicitudes.results:
            await db.prepare(
                "DELETE FROM HISTORIAL WHERE id_solicitud = ?"
            ).bind(solicitud_row.id).run()

        # 3. Eliminar solicitudes del usuario
        await db.prepare(
            "DELETE FROM SOLICITUDES WHERE id_empleado = ?"
        ).bind(user_id).run()

        # 4. Desasignar puesto de trabajo
        await db.prepare(
            "UPDATE PUESTO_DE_TRABAJO SET id_empleado = NULL WHERE id_empleado = ?"
        ).bind(user_id).run()

        # 5. Eliminar registro de activación/confirmación de contraseña
        await db.prepare(
            "DELETE FROM ACTIVACION_USUARIO WHERE user_id = ?"
        ).bind(user_id).run()

        # 6. Eliminar usuario
        await db.prepare(
            "DELETE FROM USUARIO WHERE id = ?"
        ).bind(user_id).run()

        return {
            "status": "ok",
            "message": f"Usuario '{user.nombre}' (ID: {user_id}) eliminado correctamente",
            "deleted_user": {
                "id": user.id,
                "nombre": user.nombre,
                "correo": user.correo,
            }
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando usuario: {str(e)}"
        )
