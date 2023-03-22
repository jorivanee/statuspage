from bson import ObjectId
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, current_user, logout_user
from utils.user import User


admin_blueprint = Blueprint(
    "admin", __name__)


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


def _get_incidents():
    incidents = []
    for incident in app.database.incidents.find():
        incident["id"] = str(incident.pop("_id"))
        incident['active'] = "closed_at" not in incident
        incidents.append(incident)
    return {
        "data": incidents,
        "metadata": {
            "amount": len(incidents),
            "active": len([x for x in incidents if x['active']])
        }
    }


def _get_components():
    components = []
    for component in app.database.components.find():
        status = {"status": "operational",
                  "name": "Operational"}
        component["id"] = str(component.pop("_id"))
        components.append(component)
        active_incidents = get_incidents_by_id(component['id'])
        statuses = [incident['severity']
                    for incident in active_incidents]
        if "issues" in statuses or "partial" in statuses:
            status = {"status": "issues",
                      "name": "Partial Outage"}
        if "major" in statuses:
            status = {"status": "major", "name": "Major Outage"}
        component['status'] = status
        component['incidents'] = {"metadata": {
            "amount": len(active_incidents)}, "data": active_incidents}
    return {
        "data": components,
        "metadata": {
            "amount": len(components)
        }
    }


@admin_blueprint.route("/")
@login_required
def homepage():
    return render_template("index.html", incidents=_get_incidents(), components=_get_components())


@admin_blueprint.route("/components")
@login_required
def get_components():
    return render_template("components/list.html", components=_get_components())


@admin_blueprint.route("/components/create", methods=['GET'])
@login_required
def get_create_component():
    return render_template("/components/create.html")


@admin_blueprint.route("/components/<component>/delete", methods=['POST'])
@login_required
def post_delete_component(component):
    if ObjectId.is_valid(component):
        app.database.components.delete_one({"_id": ObjectId(component)})
    return redirect(url_for("admin.get_components"))


@admin_blueprint.route("/components/<component>/delete", methods=['get'])
@login_required
def get_delete_component(component):
    if not ObjectId.is_valid(component):
        return redirect(url_for("admin.get_components"))
    component_object = app.database.components.find_one(
        {"_id": ObjectId(component)})
    if not component_object:
        return redirect(url_for("admin.get_components"))
    component_object['id'] = str(component_object.pop("_id"))
    return render_template("/components/delete_confirm.html", component=component_object)


@admin_blueprint.route("/components/create", methods=['POST'])
@login_required
def post_create_component():
    name = request.form['name'].strip()
    if not name:
        flash("Please enter a component name", "danger")
        return render_template("/components/create.html")
    component = app.database.components.find_one({"name": name})
    if component:
        flash("A component with that name already exists", "danger")
        return render_template("/components/create.html")
    component_id = app.database.components.insert_one(
        {"name": name}).inserted_id
    return redirect(url_for("admin.get_component_by_id", component=str(component_id)))


@admin_blueprint.route("/components/<component>")
@login_required
def get_component_by_id(component):
    if not ObjectId.is_valid(component):
        return redirect(url_for("admin.get_components"))
    component_object = app.database.components.find_one(
        {"_id": ObjectId(component)})
    if not component_object:
        return redirect(url_for("admin.get_components"))
    component_object['id'] = str(component_object.pop("_id"))
    return render_template("components/view.html", component=component_object)


@admin_blueprint.route("/components/<component>", methods=['POST'])
@login_required
def post_component_by_id(component):
    if not ObjectId.is_valid(component):
        return redirect(url_for("admin.get_components"))
    component_object = app.database.components.find_one(
        {"_id": ObjectId(component)})
    if not component_object:
        return redirect(url_for("admin.get_components"))
    component_object['name'] = request.form['name']
    return render_template("components/view.html", component=component_object)


@admin_blueprint.route("/incidents")
@login_required
def get_incidents():
    return render_template("incidents.html")


@admin_blueprint.route("/users")
@login_required
def get_users():
    return render_template("incidents.html")


@admin_blueprint.route("/login", methods=['GET'])
def login():
    users = app.database.users.count_documents({})
    if users < 1:
        return redirect(url_for("admin.signup_page"))
    return render_template("login.html")


@admin_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You were successfully logged out", "success")
    return redirect(url_for('admin.login'))


@admin_blueprint.route("/login", methods=['POST'])
def post_login_page():
    email = request.form.get('email')
    password = request.form.get('password')
    user = app.database.users.find_one({"email": email})
    if not user or not check_password_hash(user['password'], password):
        flash('Please check your login details and try again.', "danger")
        return render_template("login.html")
    login_user(User(user))
    return redirect(request.args.get('next') or url_for('admin.homepage'))


@ admin_blueprint.route("/signup", methods=['GET'])
def signup_page():
    users = app.database.users.count_documents({})
    if users > 0:
        return render_template("signup_blocked.html")
    return render_template("signup.html")


@ admin_blueprint.route("/signup", methods=['POST'])
def post_signup_page():
    users = app.database.users.count_documents({})
    if users > 0:
        return render_template("signup_blocked.html")
    email = request.form.get('email')
    password = request.form.get('password')
    password = generate_password_hash(password, method='sha256')
    app.database.users.insert_one({"password": password, "email": email})
    return redirect(url_for("admin.homepage"))
