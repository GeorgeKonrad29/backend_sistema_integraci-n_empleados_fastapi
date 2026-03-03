# FastAPI + Jinja2 Example

## How to Run

First ensure that `uv` is installed:
https://docs.astral.sh/uv/getting-started/installation/#standalone-installer

Now, if you run `uv run pywrangler dev` within this directory, it should use the config
in `wrangler.jsonc` to run the example.

You can also run `uv run pywrangler deploy` to deploy the example.

## Signup con Email (sin secrets)

El envío de correo para activación está en `src/api/v1/auth.py`.

Debes reemplazar estas constantes directamente en código:

```python
RESEND_API_KEY = "REEMPLAZA_CON_TU_API_KEY_DE_RESEND"
RESEND_FROM_EMAIL = "onboarding@resend.dev"
```

Luego despliega:

```bash
uv run pywrangler deploy
```

Endpoints:
- `POST /v1/auth/signup` (crea usuario y manda correo de activación)
- `POST /v1/auth/activate-password` (activa contraseña con token)
