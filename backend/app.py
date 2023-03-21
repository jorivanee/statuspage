from pymongo import MongoClient
from flask import Flask, jsonify, request
import os
import json
import logging
from flask_cors import CORS
import argon2
from blueprints.api import api_blueprint


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
app.ph = argon2.PasswordHasher()

logging.info("Loading config file")
app._config = {}
with open("config.json", "r") as jsonfile:
    app._config = json.loads(jsonfile.read())
    logging.info("Config file load complete")


app._debug = app._config['debug']


def init_mongo(cfg):
    host = cfg['host']
    port = cfg['port']
    db = cfg['database']
    app.db_client = MongoClient(host, port)
    app.database = app.db_client[db]


init_mongo(app._config['database'])
app.secret_key = app._config['secret_key']

if app._debug:
    # Allowing cors on develop because the react frontend and flask backend are hosted on separate ports, and it wouldn't allow the react app to access the API
    CORS(app)


@app.errorhandler(404)
def error_404(error):
    if (request.path.startswith("/api")):
        return jsonify(error="Resource not found", route=request.path, code=404)
    # return app.send_static_file('index.html')
    return "test"


app.register_blueprint(api_blueprint, url_prefix="/api")

if __name__ == '__main__':
    app.run(debug=app._debug, port=app._config['port'])
