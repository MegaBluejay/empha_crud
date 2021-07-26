from os import environ

import dataset
from addict import Dict

from util import hash_string

__all__ = ["connect_db", "init_db"]


def connect_db():
    return dataset.connect(row_type=Dict, ensure_schema=False)


def init_db():
    db = connect_db()
    init_values = int(environ.get("INIT_DB", "0"))

    if init_values:
        db.create_table("users", primary_id="user_id")
        USERS = db["users"]
        USERS.create_column("username", db.types.string(150), unique=True)
        USERS.create_column("is_active", db.types.integer)
        USERS.create_column("pass_hash", db.types.string(64))
        USERS.create_column("is_superuser", db.types.boolean)
        USERS.create_column("first_name", db.types.string(30))
        USERS.create_column("last_name", db.types.string(150))
        USERS.create_column("last_login", db.types.datetime)

        USERS.insert(
            {
                "username": "admin",
                "is_active": True,
                "pass_hash": hash_string("admin"),
                "is_superuser": True,
            }
        )
