# routes.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from config import Config
# Importar Newsletter aqui
from app.models import db, User, Carometro, Contact, Testimonial, Article, Appointment, Newsletter
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Por favor, faça login para acessar esta área.'

    @app.template_filter('title_except_prepositions')
    def title_except_prepositions(s):
        prepositions = {'da', 'de', 'do', 'dos', 'das'}
        words = s.split()
        processed_words = []
        for word in words:
            if word.lower() in prepositions and len(processed_words) > 0:
                processed_words.append(word.lower())
            else:
                processed_words.append(word.capitalize())
        return ' '.join(processed_words)

    return app, login_manager

app, login_manager = create_app()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

# ... (Outras rotas profile, login, register, logout, mentor_area mantidas iguais) ...
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('mentor_area'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('mentor_area'))
        else:
            flash('Login ou senha inválidos.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('mentor_area'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('As senhas não coincidem.', 'error')
            return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe.', 'error')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'error')
            return render_template('register.html')
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar. Por favor, tente novamente.', 'error')
            print(f"Erro ao salvar usuário: {e}")
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/mentor_area')
@login_required
def mentor_area():
    return render_template('mentor_area.html')

@app.route('/modulo_01')
@login_required
def modulo_01():
    appointment = Appointment.query.filter_by(user_id=current_user.id, module_name="Módulo 1").first()
    available_dates = ["15/11/2025 - 19:00", "18/11/2025 - 20:00", "20/11/2025 - 18:30", "22/11/2025 - 09:00 (Sábado)"]

    # Lista de locais presenciais disponíveis
    presential_locations = [
        "Coworking Boa Viagem - Av. Boa Viagem, 123",
        "Escritório Central - RioMar Trade Center, Torre 1",
        "Auditório Paço Alfândega - Recife Antigo"
    ]

    return render_template('modulo_01.html', appointment=appointment, available_dates=available_dates, presential_locations=presential_locations)

@app.route('/agendar', methods=['POST'])
@login_required
def schedule_appointment():
    if request.method == 'POST':
        module_name = request.form.get('module_name')
        schedule_date = request.form.get('schedule_date')

        # Lógica para definir o local final
        location_type = request.form.get('location_type') # 'Google Meet' ou 'Presencial'

        final_location = "A definir"

        if location_type == 'Google Meet':
            final_location = 'Google Meet'
        elif location_type == 'Presencial':
            # Pega o endereço escolhido no dropdown
            final_location = request.form.get('presential_address')

        notes = request.form.get('notes')

        if not schedule_date or not final_location:
            flash('Por favor, preencha todos os campos obrigatórios.', 'error')
            return redirect(url_for('modulo_01'))

        existing = Appointment.query.filter_by(user_id=current_user.id, module_name=module_name).first()
        if existing:
            existing.schedule_date = schedule_date
            existing.location = final_location
            existing.notes = notes
            existing.status = 'Atualizado - Aguardando confirmação'
            flash('Seu agendamento foi atualizado com sucesso!', 'success')
        else:
            new_appointment = Appointment(user_id=current_user.id, module_name=module_name, schedule_date=schedule_date, location=final_location, notes=notes)
            db.session.add(new_appointment)
            flash('Solicitação de agendamento enviada com sucesso! Aguarde a confirmação.', 'success')
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao realizar agendamento: {str(e)}', 'error')
        return redirect(url_for('modulo_01'))

@app.route('/api/newsletter/subscribe', methods=['POST'])
def subscribe_newsletter():
    data = request.get_json()
    email = data.get('email')

    if not email or '@' not in email:
        return jsonify({'success': False, 'message': 'Email inválido.'}), 400

    existing = Newsletter.query.filter_by(email=email).first()
    if existing:
        return jsonify({'success': True, 'message': 'Você já está inscrito!'}), 200

    try:
        new_sub = Newsletter(email=email)
        db.session.add(new_sub)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Inscrição realizada com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Erro ao salvar.'}), 500

@app.route('/tests')
@login_required
def tests():
    return render_template('tests.html')

@app.route('/test_01')
@login_required
def test_01():
    return render_template('test_01.html')

@app.route('/api/mentores', methods=['POST'])
@login_required
def handle_mentor_form():
    if request.method == 'POST':
        user_id = current_user.id
        profile = Carometro.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = Carometro(user_id=user_id)
        try:
            profile.display_name = request.form.get('display_name')
            # ... lógica mantida ...
            db.session.add(profile)
            db.session.commit()
            flash('Perfil salvo com sucesso!', 'success')
            return redirect(url_for('tests'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar o perfil: {e}', 'error')
            return redirect(url_for('test_01'))

@app.route('/about')
def about():
    return render_template('about_us.html')

@app.cli.command()
def init_db():
    db.create_all()
    print('Banco de dados inicializado.')
    admin_user = User.query.filter_by(email='admin@stlconsulting.com').first()
    if not admin_user:
        admin_user = User(username='admin', email='admin@stlconsulting.com')
        admin_user.set_password('senha_segura_aqui')
        db.session.add(admin_user)
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        os.makedirs(app.instance_path, exist_ok=True)
    # app.run(debug=True)   # debug=True apenas para desenvolvimento!
    app.run(host='0.0.0.0', port=8080) # Rodar localhost + Túnel Cloudfared
    # app.run(host='192.168.0.19', port=5000) # Rodar na mesma rede Wi-Fi
