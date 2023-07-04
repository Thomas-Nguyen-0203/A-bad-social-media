import os

_base_dir = os.path.dirname(__name__)
_db = "app.db"

CONFIG = {
    "SECRET_KEY": "MomosuzuNeneIsMyOshi",
    "DB_PATH": f"{os.path.join(_base_dir, _db)}"
}