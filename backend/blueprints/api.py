from flask import Blueprint, jsonify
from flask import current_app as app
import time

api_blueprint = Blueprint("api", __name__)


def get_components():
    components = []
    for component in app.database.components.find():
        component["id"] = str(component.pop("_id"))
        components.append(component)
    return {
        "data": components,
        "metadata": {
            "amount": len(components)
        }
    }


def get_incidents():
    incidents = []
    for incident in app.database.incidents.find():
        incident["id"] = str(incident.pop("_id"))
        incidents.append(incident)
    return {
        "data": incidents,
        "metadata": {
            "amount": len(incidents)
        }
    }


def get_status():
    return app.database.settings.find_one({"type": "status"})['value']

# Debug Route to insert an incident
@api_blueprint.route("/put")
def put():
    app.database.incidents.insert_one({"affected_services": ["6419a760bd28c329260ea6d8"], "created_at": int(time.time(
    ))*1000, "title": "Novuss Vast Storing", "description": "Novuss Vast is tijdelijk onbereikbaar", "severity": "major"})
    return jsonify({"success": True})


@api_blueprint.route("/components")
def components():
    return jsonify(get_components())


@api_blueprint.route("/incidents")
def incidents():
    return jsonify(get_incidents)


@api_blueprint.route("/status")
def status():
    return jsonify({
        "incidents": get_incidents(),
        "components": get_components(),
        "status": get_status()
    })


@api_blueprint.route("/status/raw")
def status_raw():
    return jsonify({
        "incidents": get_incidents()['data'],
        "components": get_components()['data'],
        "status": get_status()
    })
