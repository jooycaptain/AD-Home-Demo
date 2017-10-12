from threading import Thread
from functools import wraps
from flask import request, abort

def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper

def require_apikey(view_function):
    @wraps(view_function)
    # the new, post-decoration function. Note *args and **kwargs here.....
    def decorated_function(*args, **kwargs):
        if request.args.get('api_key') and request.args.get('api_key') == 'Jo3y1SAW3S0M3':
            return view_function(*args, **kwargs)
        else:
            abort(401)
    return decorated_function