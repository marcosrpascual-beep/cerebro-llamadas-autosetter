"""
One-shot local: obtiene un refresh_token de OAuth para que el servidor
pueda crear Google Docs en TU Drive personal.

Cómo usarlo:
1. Crear OAuth Client tipo "Desktop app" en Google Cloud Console.
2. Copiar client_id y client_secret en las variables de abajo (o usar env vars).
3. python3 scripts/get_refresh_token.py
4. Se abre el navegador, autorizas con tu cuenta Google.
5. La terminal te imprime el REFRESH_TOKEN — cópialo a tu .env y a Railway.

Requiere: pip install google-auth-oauthlib
"""
import os
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID") or "PEGA_TU_CLIENT_ID_AQUI"
CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET") or "PEGA_TU_CLIENT_SECRET_AQUI"

CLIENT_CONFIG = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"],
    }
}

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]


def main():
    if "PEGA_TU" in CLIENT_ID or "PEGA_TU" in CLIENT_SECRET:
        raise SystemExit(
            "❌ Edita este archivo o define GOOGLE_OAUTH_CLIENT_ID y "
            "GOOGLE_OAUTH_CLIENT_SECRET antes de correrlo."
        )

    flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
    creds = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
        open_browser=True,
    )

    print("\n" + "=" * 60)
    print("REFRESH TOKEN obtenido. Guárdalo en .env y Railway como")
    print("GOOGLE_OAUTH_REFRESH_TOKEN:\n")
    print(creds.refresh_token)
    print("=" * 60)


if __name__ == "__main__":
    main()
