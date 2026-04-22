"""
Script para crear el archivo .env si no existe
"""

import os
import secrets


def generate_secret_key():
    """Genera una secret key aleatoria"""
    return secrets.token_urlsafe(32)


def create_env_file():
    """Crea el archivo .env con valores por defecto"""
    env_file = ".env"

    if os.path.exists(env_file):
        print(f"[INFO] El archivo {env_file} ya existe. No se sobrescribirá.")
        return False

    # Generar secret key
    secret_key = generate_secret_key()

    env_content = f"""# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5435/nougram_db

# JWT Configuration
SECRET_KEY={secret_key}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google API Configuration (valores dummy para desarrollo)
GOOGLE_CLIENT_ID=dummy-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=dummy-client-secret
GOOGLE_SERVICE_ACCOUNT_PATH=./config/google-service-account.json

# Google Sheets Configuration
GOOGLE_SHEETS_ID=dummy-sheet-id

# AI Configuration (opcional por ahora)
OPENAI_API_KEY=
GOOGLE_AI_API_KEY=

# CORS Configuration
CORS_ORIGINS=http://localhost:3000

# Environment
ENVIRONMENT=development
"""

    with open(env_file, "w") as f:
        f.write(env_content)

    print(f"[OK] Archivo {env_file} creado exitosamente.")
    print(f"[OK] SECRET_KEY generado: {secret_key[:20]}...")
    return True


if __name__ == "__main__":
    create_env_file()
