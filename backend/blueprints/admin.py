import time
from urllib.parse import urlparse, urljoin
from bson import ObjectId
from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, current_user, logout_user
from utils.user import User


admin_blueprint = Blueprint(
    "admin", __name__)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


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
        services = []
        for service in incident['affected_services']:
            s = app.database.components.find_one({"_id": ObjectId(service)})
            if s:
                services.append({"id": service, "name": s['name']})
        if len(services) != len(incident['affected_services']):
            app.database.components.update_one({"_id": ObjectId(service)}, {
                                               "$set": {"affected_services": [x['id'] for x in services]}})
        incident['services'] = services
        severity = incident['severity']
        status = {"status": "operational", "name": "Operational"}
        if severity in ['partial']:
            status = {"status": "partial",
                      "name": "Partial Outage"}
        if severity in ['major']:
            status = {"status": "major", "name": "Major Outage"}
        incident['status'] = status
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
        if "partial" in statuses:
            status = {"status": "partial",
                      "name": "Partial Outage"}
        if "major" in statuses:
            status = {"status": "major", "name": "Major Outage"}
        component['status'] = status
        component['incidents'] = {"metadata": {
            "amount": len(active_incidents)}, "data": active_incidents}
    return {
        "data": components,
        "metadata": {
            "amount": len(components),
            "active": len([x for x in components if x['status']['status'] != "operational"])
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


@admin_blueprint.route("/incidents/<incident>/delete", methods=['POST'])
@login_required
def post_delete_incident(incident):
    if ObjectId.is_valid(incident):
        app.database.incidents.delete_one({"_id": ObjectId(incident)})
    return redirect(url_for("admin.get_incidents"))


@admin_blueprint.route("/incidents/<incident>/delete", methods=['get'])
@login_required
def get_delete_incident(incident):
    if not ObjectId.is_valid(incident):
        return redirect(url_for("admin.get_incidents"))
    incident_object = app.database.incidents.find_one(
        {"_id": ObjectId(incident)})
    if not incident_object:
        return redirect(url_for("admin.get_incidents"))
    incident_object['id'] = str(incident_object.pop("_id"))
    return render_template("/incidents/delete_confirm.html", incident=incident_object)


@admin_blueprint.route("/components/create", methods=['POST'])
@login_required
def post_create_component():
    name = request.form['name'].strip()
    if not name:
        flash("Name must not be blank", "danger")
        return render_template("/components/create.html")
    component = app.database.components.find_one({"name": name})
    if component:
        flash("A component with that name already exists", "danger")
        return render_template("/components/create.html")
    component_id = app.database.components.insert_one(
        {"name": name}).inserted_id
    return redirect(url_for("admin.get_component_by_id", component=str(component_id)))


def get_components_basic():
    components = []
    for component in app.database.components.find():
        components.append(
            {"name": component['name'], 'id': str(component['_id'])})
    return components


@admin_blueprint.route("/incidents/create", methods=['GET'])
@login_required
def get_create_incident():
    return render_template("/incidents/create.html", components=get_components_basic())


@admin_blueprint.route("/incidents/create", methods=['POST'])
@login_required
def post_create_incident():
    components = [arg.split(
        ".")[1] for arg in request.form if arg.startswith("components.")]
    if request.form['title'] == "":
        flash("Name must not be blank", "danger")
        return redirect(url_for('admin.get_create_incident'))
    if len(components) < 1:
        flash("You must select at least one component", "danger")
        return redirect(url_for('admin.get_create_incident'))
    data = {"affected_services": components,
            "title": request.form['title'], "severity": request.form['severity'], "created_at": int(time.time(
            ))*1000}

    incident_id = app.database.incidents.insert_one(
        data).inserted_id
    return redirect(url_for("admin.get_incident_by_id", incident=str(incident_id)))


@admin_blueprint.route("/incidents/<incident>")
@login_required
def get_incident_by_id(incident):
    if not ObjectId.is_valid(incident):
        return redirect(url_for("admin.get_incidents"))
    incident_object = app.database.incidents.find_one(
        {"_id": ObjectId(incident)})
    if not incident_object:
        return redirect(url_for("admin.get_incidents"))
    incident_object['id'] = str(incident_object.pop("_id"))
    return render_template("incidents/view.html", incident=incident_object, components=get_components_basic())


@admin_blueprint.route("/incidents/<incident>/open")
@login_required
def open_incident_by_id(incident):
    if not ObjectId.is_valid(incident):
        return redirect(url_for("admin.get_incidents"))
    incident_object = app.database.incidents.find_one(
        {"_id": ObjectId(incident)})
    if not incident_object:
        return redirect(url_for("admin.get_incidents"))
    app.database.incidents.update_one({"_id": ObjectId(incident)}, {
        "$unset": {"closed_at": None}})
    flash("The incident has been reopened", "success")
    return redirect(url_for('admin.get_incident_by_id', incident=incident))


@admin_blueprint.route("/incidents/<incident>/close")
@login_required
def close_incident_by_id(incident):
    if not ObjectId.is_valid(incident):
        return redirect(url_for("admin.get_incidents"))
    incident_object = app.database.incidents.find_one(
        {"_id": ObjectId(incident)})
    if not incident_object:
        return redirect(url_for("admin.get_incidents"))
    app.database.incidents.update_one({"_id": ObjectId(incident)}, {
        "$set": {"closed_at": int(time.time(
        ))*1000}})
    flash("The incident has been closed", "success")
    return redirect(url_for('admin.get_incident_by_id', incident=incident))


@admin_blueprint.route("/users/<user>/delete", methods=['POST'])
@login_required
def post_delete_user(user):
    if ObjectId.is_valid(user):
        app.database.users.delete_one({"_id": ObjectId(user)})
    return redirect(url_for("admin.get_users"))


@admin_blueprint.route("/users/<user>/delete", methods=['get'])
@login_required
def get_delete_user(user):
    if not ObjectId.is_valid(user):
        return redirect(url_for("admin.get_users"))
    user_object = app.database.users.find_one(
        {"_id": ObjectId(user)})
    if not user_object:
        return redirect(url_for("admin.get_users"))
    user_object['id'] = str(user_object.pop("_id"))
    return render_template("/users/delete_confirm.html", user=user_object)


@admin_blueprint.route("/incidents/<incident>", methods=['POST'])
@login_required
def post_incident_by_id(incident):
    if not ObjectId.is_valid(incident):
        return redirect(url_for("admin.get_incidents"))
    incident_object = app.database.incidents.find_one(
        {"_id": ObjectId(incident)})
    if not incident_object:
        return redirect(url_for("admin.get_components"))
    components = [arg.split(
        ".")[1] for arg in request.form if arg.startswith("components.")]
    if request.form['title'] == "":
        flash("Name must not be blank", "danger")
        return redirect(url_for('admin.get_incident_by_id', incident=incident))
    if len(components) < 1:
        flash("You must select at least one component", "danger")
        return redirect(url_for('admin.get_incident_by_id', incident=incident))
    data = {"affected_services": components,
            "title": request.form['title'], "severity": request.form['severity']}

    app.database.incidents.update_one({"_id": ObjectId(incident)}, {
        "$set": data})
    flash("The incident has been updated", "success")
    return redirect(url_for('admin.get_incident_by_id', incident=incident))


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
    app.database.components.update_one({"_id": ObjectId(component)}, {
                                       "$set": {"name": request.form['name']}})
    return redirect(url_for('admin.get_component_by_id', component=component))


@admin_blueprint.route("/incidents")
@login_required
def get_incidents():
    return render_template("incidents/list.html", incidents=_get_incidents())


@admin_blueprint.route("/users")
@login_required
def get_users():
    users = []
    for user in app.database.users.find():
        users.append({'id': str(user['_id']), 'email': user['email']})
    return render_template("users/list.html", users=users)


@admin_blueprint.route("/users/<user>")
@login_required
def get_user_by_id(user):
    if not ObjectId.is_valid(user):
        return redirect(url_for("admin.get_users"))
    user_object = app.database.users.find_one(
        {"_id": ObjectId(user)})
    if not user_object:
        return redirect(url_for("admin.get_users"))
    user_object['id'] = str(user_object.pop("_id"))
    user_object.pop('password')
    return render_template("users/view.html", user=user_object)


@admin_blueprint.route("/users/<user>", methods=['POST'])
@login_required
def post_user_by_id(user):
    if not ObjectId.is_valid(user):
        return redirect(url_for("admin.get_users"))
    user_object = app.database.users.find_one(
        {"_id": ObjectId(user)})
    if not user_object:
        return redirect(url_for("admin.get_users"))
    user_object['id'] = str(user_object.pop("_id"))
    user_object.pop('password')
    email = request.form['email']
    password = request.form['password']
    update = {}
    if not email:
        flash("Email cannot be empty", 'danger')
        return redirect(url_for('admin.get_user_by_id', user=user))
    if email != user_object['email']:
        update['email'] = email
    if password:
        update['password'] = generate_password_hash(password, method='sha256')
    if len(update) < 1:
        return redirect(url_for('admin.get_user_by_id', user=user))
    app.database.users.update_one({"_id": ObjectId(user)}, {
        "$set": update})
    flash("The user has been updated", "success")
    return redirect(url_for('admin.get_user_by_id', user=user))


@admin_blueprint.route("/users/create")
@login_required
def get_create_user():
    return render_template("users/create.html")


@admin_blueprint.route("/users/create", methods=['POST'])
@login_required
def post_create_user():
    email = request.form.get('email')
    user = app.database.users.find_one({"email": email})
    if not email:
        flash("Email must not be empty", "danger")
        return render_template("users/create.html")
    if user:
        flash("A user with this email address already exists", "danger")
        return render_template("users/create.html")
    password = request.form.get('password')
    password = generate_password_hash(password, method='sha256')
    record = app.database.users.insert_one(
        {"password": password, "email": email}).inserted_id
    return redirect(url_for("admin.get_user_by_id", user=str(record)))


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
    if not is_safe_url(request.args.get('next')):
        return redirect(url_for("admin.homepage"))
    return redirect(request.args.get('next') or url_for('admin.homepage'))


@admin_blueprint.route("/signup", methods=['GET'])
def signup_page():
    session.pop('_flashes', None)
    users = app.database.users.count_documents({})
    if users > 0:
        return render_template("signup_blocked.html")
    return render_template("signup.html")

@admin_blueprint.route("/settings/global")
def get_settings_global():
    return render_template("settings/global.html")


@admin_blueprint.route("/settings/global", methods=['POST'])
def post_settings_global():
    form = request.form
    keys = ['image_url','image_link','footer_link','footer_text','title']
    changed_keys = []
    for key in keys:
        setting = app.database.settings.find_one({"key": key})['value']
        if key in form:
            if setting != form[key]:
                app.database.settings.update_one(
                    {"key": key}, {"$set": {"value": form[key]}})
                changed_keys.append(key)
        else:
            app.database.settings.update_one(
                    {"key": key}, {"$set": {"value": None}})
            changed_keys.append(key)
    if len(changed_keys) < 1:
        return redirect(url_for('admin.get_settings_global'))

    app.update_config()
    flash("The settings have been updated", "success")
    return redirect(url_for('admin.get_settings_global'))



@admin_blueprint.route("/signup", methods=['POST'])
def post_signup_page():
    users = app.database.users.count_documents({})
    if users > 0:
        return render_template("signup_blocked.html")
    email = request.form.get('email')
    password = request.form.get('password')
    password = generate_password_hash(password, method='sha256')
    inserted_id = app.database.users.insert_one(
        {"password": password, "email": email}).inserted_id
    user = app.database.users.find_one({"_id": inserted_id})
    login_user(User(user))
    return redirect(url_for("admin.homepage"))


@admin_blueprint.route("/settings")
def account_settings():
    return render_template("edit_account.html")


@admin_blueprint.route("/settings", methods=['POST'])
def post_account_settings():
    password = request.form['password']
    newpassword = request.form['password.new']
    data = {}
    if "dark_theme" in request.form and request.form['dark_theme'] == "on":
        if not current_user.dark_theme:
            data['dark_theme'] = True
    else:
        if current_user.dark_theme:
            data['dark_theme'] = False
    if "email" in request.form:
        email = request.form['email']
        if email != current_user.email:
            if not email:
                flash("Email can not be empty", "danger")
                return render_template("edit_account.html")
            data['email'] = email
    if newpassword:
        if not check_password_hash(current_user.password, password):
            flash("Invalid Password", "danger")
            return render_template("edit_account.html")
        data['password'] = generate_password_hash(newpassword, method="sha256")
    if len(data) < 1:
        return redirect(url_for("admin.account_settings"))
    app.database.users.update_one(
        {"_id": ObjectId(current_user.id)}, {"$set": data})
    flash("Your account has been updated", "success")
    return redirect(url_for("admin.account_settings"))