from flask import jsonify, request
from functools import wraps
from flask import current_app as app
from utils.generic import format_error


def require_json_params(*params):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            json = request.json
            if not json:
                return jsonify(format_error("Bad Request", "Expected JSON body"))
            data = {}
            for param in params:
                if not param in json:
                    return jsonify(format_error("Must supply " + param, param + " not supplied but required", {"body": json, "required_params": params}))

                data[param] = json[param]
            kwargs.update(data)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def api_route():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return jsonify(f(*args, **kwargs))
        return decorated_function
    return decorator
