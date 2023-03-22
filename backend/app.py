from bson import ObjectId
from pymongo import MongoClient
from flask import Flask, jsonify, request, render_template
import os
import json
import logging
from flask_cors import CORS
from blueprints.api import api_blueprint
from blueprints.admin import admin_blueprint
from flask_login import LoginManager
from utils.user import User

isExist = os.path.exists("logs")
if not isExist:
    os.makedirs("logs")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/info.log"),
        logging.StreamHandler()
    ]
)


logging.info("Creating application")
app = Flask(__name__)

logging.info("Loading config file")
app._config = {}
with open("config.json", "r") as jsonfile:
    app._config = json.loads(jsonfile.read())
    logging.info("Config file load complete")


app._debug = app._config['debug']
login_manager = LoginManager()
login_manager.login_view = 'admin.login'
login_manager.init_app(app)
login_manager.login_message_category = "danger"


@login_manager.user_loader
def load_user(id):
    user = app.database.users.find_one({"_id": ObjectId(id)})
    if user:
        return User(user)
    return None


def init_mongo(cfg):
    host = cfg['host']
    port = cfg['port']
    db = cfg['database']
    app.db_client = MongoClient(host, port)
    app.database = app.db_client[db]


init_mongo(app._config['database'])
app.config['SECRET_KEY'] = app._config['secret_key']

if app._debug:
    # Allowing cors on develop because the react frontend and flask backend are hosted on separate ports, and it wouldn't allow the react app to access the API
    CORS(app)


@app.errorhandler(404)
def error_404(error):
    if (request.path.startswith("/api")):
        return jsonify(error="Resource not found", route=request.path, code=404)
    return render_template("error404.html")


app.register_blueprint(api_blueprint, url_prefix="/api")
app.register_blueprint(admin_blueprint, url_prefix="/admin")

if __name__ == '__main__':
    app.run(debug=app._debug, port=app._config['port'])
