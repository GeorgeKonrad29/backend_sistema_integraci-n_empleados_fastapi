# FastAPI + Jinja2 Example

## How to Run

First ensure that `uv` is installed:
https://docs.astral.sh/uv/getting-started/installation/#standalone-installer

Now, if you run `uv run pywrangler dev` within this directory, it should use the config
in `wrangler.jsonc` to run the example.

You can also run `uv run pywrangler deploy` to deploy the example.

## Cloudflare Secret for Password Hash

This API expects a Cloudflare secret named `PASSWORD_PEPPER`.
It is used as a server-side pepper for password hashing/verification.

Set it in your Worker environment:

```bash
npx wrangler secret put PASSWORD_PEPPER
```

If you use `pywrangler`, you can also run:

```bash
uv run pywrangler secret put PASSWORD_PEPPER
```
