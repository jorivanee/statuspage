from flask import current_app as app


def format_error(message, cause, props={}):
    if (app._debug):
        return {"error": True, "message": message, "cause": cause, "props": props}
    else:
        return {"error": True, "message": message, "props": props}
