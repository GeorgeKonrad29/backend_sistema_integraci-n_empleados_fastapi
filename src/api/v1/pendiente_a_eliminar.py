"""
ARCHIVO TEMPORAL - ELIMINAR UNA VEZ QUE EL FRONTEND ESTÉ EN PRODUCCIÓN

Este archivo contiene el formulario HTML que se sirve en el endpoint GET /activate-password.
Cuando el frontend esté en producción y maneje su propio formulario de activación,
este archivo y el endpoint GET en auth.py pueden ser eliminados.

El endpoint POST /activate-password en auth.py debe permanecer para recibir solicitudes del API.
"""

import json


def get_activation_form_html(token: str) -> str:
    """
    Retorna el HTML del formulario de activación de contraseña.
    Este formulario es temporal y debe ser reemplazado por uno en el frontend.
    """
    if not token:
        return "<h3>Token inválido</h3><p>Falta el token de activación.</p>"

    return f"""
    <!doctype html>
    <html>
      <head>
        <meta charset=\"utf-8\" />
        <title>Activar contraseña</title>
      </head>
      <body style=\"font-family: Arial, sans-serif; max-width: 480px; margin: 40px auto;\">
        <h2>Activa tu cuenta</h2>
        <p>Define tu nueva contraseña:</p>
        <form id=\"activate-form\">
          <input type=\"password\" id=\"password\" placeholder=\"Nueva contraseña\" required style=\"width:100%;padding:10px;margin:8px 0;\" />
          <button type=\"submit\" style=\"padding:10px 16px;\">Activar</button>
        </form>
        <p id=\"msg\" style=\"margin-top:16px;\"></p>

        <script>
          const form = document.getElementById('activate-form');
          const msg = document.getElementById('msg');
          const token = {json.dumps(token)};

          form.addEventListener('submit', async (e) => {{
            e.preventDefault();
            const contrasena = document.getElementById('password').value;

            const res = await fetch('/v1/auth/activate-password', {{
              method: 'POST',
              headers: {{ 'Content-Type': 'application/json' }},
              body: JSON.stringify({{ token, contrasena }})
            }});

            const data = await res.json();
            if (res.ok) {{
              msg.style.color = 'green';
              msg.textContent = data.message || 'Cuenta activada correctamente';
            }} else {{
              msg.style.color = 'red';
              msg.textContent = data.detail || 'No se pudo activar la cuenta';
            }}
          }});
        </script>
      </body>
    </html>
    """
