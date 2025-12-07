# app/admin/decorators.py
from functools import wraps
from flask import abort
from flask_login import current_user

def mentor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica se está logado e se o papel é 'mentor'
        if not current_user.is_authenticated or current_user.role != 'mentor':
            abort(403) # Erro Proibido
        return f(*args, **kwargs)
    return decorated_function
