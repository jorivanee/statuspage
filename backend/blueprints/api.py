from flask import Blueprint, jsonify
from flask import current_app as app

api_blueprint = Blueprint("api", __name__)


def allEqual(iterable):
    iterator = iter(iterable)

    try:
        firstItem = next(iterator)
    except StopIteration:
        return True

    for x in iterator:
        if x != firstItem:
            return False
    return True


def get_components():
    components = []
    for component in app.database.components.find():
        status = {"status": "operational",
                  "name": app._config['phrases']['operational']['component']}
        component["id"] = str(component.pop("_id"))
        components.append(component)
        active_incidents = get_incidents_by_id(component['id'])
        statuses = [incident['severity']
                    for incident in active_incidents]
        if "partial" in statuses:
            status = {"status": "partial",
                      "name": app._config['phrases']['partial']['component']}
        if "major" in statuses:
            status = {"status": "major",
                      "name": app._config['phrases']['major']['component']}
        component['status'] = status
        component['incidents'] = {"metadata": {
            "amount": len(active_incidents)}, "data": active_incidents}
    return {
        "data": components,
        "metadata": {
            "amount": len(components)
        }
    }


def get_incidents_by_id(component_id):
    component_id = str(component_id)
    incidents = app.database.incidents.find(
        {"affected_services": component_id})
    result = []
    for incident in incidents:
        if 'closed_at' in incident:
            continue
        incident["id"] = str(incident.pop("_id"))
        incident.pop("affected_services")
        result.append(incident)
    return result


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
    status = {"status": "operational",
              "text": app._config['phrases']['operational']['all'], "timeago": "Reload"}
    statuses = [component['status']['status']
                for component in get_components()['data']]
    if "partial" in statuses:
        status['status'] = 'partial'
        status['text'] = app._config['phrases']['partial']['some']
        if (allEqual(statuses)):
            status['text'] = app._config['phrases']['partial']['all']
    if "major" in statuses:
        status['status'] = 'major'
        status['text'] = app._config['phrases']['major']['some']
        if (allEqual(statuses)):
            status['text'] = app._config['phrases']['major']['all']
    return status


@ api_blueprint.route("/components")
def components():
    return jsonify(get_components())


@ api_blueprint.route("/incidents")
def incidents():
    return jsonify(get_incidents())


@ api_blueprint.route("/status")
def status():
    return jsonify({
        "incidents": get_incidents(),
        "components": get_components(),
        "status": get_status()
    })


@ api_blueprint.route("/status/raw")
def status_raw():
    return jsonify({
        "incidents": get_incidents()['data'],
        "components": get_components()['data'],
        "status": get_status()
    })
