import json
import uuid
from datetime import datetime, timezone

# ALMACENAMIENTO TEMPORAL - reemplazar por conexión a base de datos real

DB_FILE = "data/users.json"

def _load():
    # TEMP: lee todos los usuarios desde un archivo JSON local
    try:
        with open(DB_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        _save([])
        return []

def _save(users):
    # TEMP: sobreescribe el archivo JSON con la lista actualizada de usuarios
    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=2)

# Funciones permanentes - migrar a ORM/DB manteniendo la misma firma

async def create_user(data: dict):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_user = {
        "id": str(uuid.uuid4()),
        "name": data["name"],
        "email": data["email"],
        "password_hash": data["hashed_password"],
        "role": data["role"],
        "created_at": now,
        "updated_at": now,
    }
    users = _load() # TEMP: carga desde archivo
    users.append(new_user)
    _save(users) # TEMP: guarda en archivo
    return new_user

async def get_user_by_email(email: str):
    users = _load()  # TEMP: carga desde archivo
    return next((u for u in users if u["email"] == email), None)