from flask import Flask
from flask_sock import Sock

from config import CONFIG

app = Flask(__name__)
app.config.update(
    SECRET_KEY = CONFIG["SECRET_KEY"]
)
DATABASE_PATH = CONFIG["DB_PATH"]
sock = Sock(app)

from app import controller