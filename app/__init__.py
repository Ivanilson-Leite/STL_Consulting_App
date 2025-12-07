# app/__init__.py
from flask import Flask
from config import Config
from app.admin.routes import admin
from app.extensions import db, login_manager, mail

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializa as extensões
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    login_manager.login_view = 'auth.login' # Redireciona para o blueprint 'auth'
    login_manager.login_message = 'Por favor, faça login para acessar esta área.'

    # --- Filtro de Template (Movido do antigo app.py) ---
    @app.template_filter('title_except_prepositions')
    def title_except_prepositions(s):
        if not s: return ""
        prepositions = {'da', 'de', 'do', 'dos', 'das'}
        words = s.split()
        processed_words = []
        for word in words:
            if word.lower() in prepositions and len(processed_words) > 0:
                processed_words.append(word.lower())
            else:
                processed_words.append(word.capitalize())
        return ' '.join(processed_words)

    # --- Registro dos Blueprints ---
    from app.main.routes import main
    from app.auth.routes import auth
    from app.mentor.routes import mentor

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(mentor)
    app.register_blueprint(admin)

    return app

# --- User Loader (Necessário para o Flask-Login) ---
@login_manager.user_loader
def load_user(user_id):
    from app.models import User # Importação local para evitar ciclo
    return User.query.get(int(user_id))
