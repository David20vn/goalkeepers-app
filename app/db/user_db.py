import json
import uuid
from datetime import datetime, timezone

# TEMP: reemplazar por conexión a base de datos real
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

async def get_user_by_id(user_id: str):
    users = _load() # TEMP: carga desde archivo
    return next((u for u in users if u["id"] == user_id), None)

async def update_user(user_id: str, fields: dict):
    users = _load() # TEMP: carga desde archivo
    for user in users:
        if user["id"] == user_id:
            user.update(fields)
            _save(users) # TEMP: guarda en archivo
            return user
    return None