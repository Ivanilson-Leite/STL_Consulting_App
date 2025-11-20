# routes.py
from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db, User, Carometro, Contact, Testimonial, Article
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializa o SQLAlchemy com a aplicação
    db.init_app(app)

    # Inicializa o LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login' # Redireciona para a rota 'login' se não autenticado
    login_manager.login_message = 'Por favor, faça login para acessar esta área.'

    # --- Adicionando o filtro personalizado ---
    @app.template_filter('title_except_prepositions')
    def title_except_prepositions(s):
        """
        Converte uma string para o formato de título,
        mas mantém as preposições 'da', 'de', 'do', 'dos', 'das' em minúsculas.
        """
        # Palavras que devem permanecer em minúsculas
        prepositions = {'da', 'de', 'do', 'dos', 'das'}

        # Divide a string em palavras
        words = s.split()

        # Processa cada palavra
        processed_words = []
        for word in words:
            # Se a palavra (em minúsculas) estiver na lista de preposições (e não for a primeira ou última palavra, ou você quiser que a primeira palavra sempre seja maiúscula)
            # Vamos considerar que a primeira palavra sempre deve ser maiúscula.
            if word.lower() in prepositions and len(processed_words) > 0: # A preposição não é a primeira palavra
                processed_words.append(word.lower())
            else:
                processed_words.append(word.capitalize())

        # Junta as palavras processadas de volta em uma string
        return ' '.join(processed_words)
    # --- Fim da adição do filtro ---

    return app, login_manager

app, login_manager = create_app()

# Loader de usuário para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rota principal
@app.route('/')
def index():
    # Você pode passar dados do banco para o template aqui
    # Por exemplo, buscar depoimentos ou artigos
    # testimonials = [] # Ex: Testimonial.query.all() ou Testimonial.query.limit(5).all()
    # articles = [] # Ex: Article.query.all() ou Article.query.limit(3).all()
    # return render_template('index.html', testimonials=testimonials, articles=articles)
    # A variável 'current_user' está disponível automaticamente via Flask-Login
    return render_template('index.html')

# Rota para o Perfil (requer login - futura implementação)
@app.route('/profile')
@login_required
def profile():
    # Aqui futuramente carregará os dados do perfil do usuário logado
    return render_template('profile.html') # Renderiza um template 'profile.html' (crie-o futuramente)

# Rota para a página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('mentor_area')) # Redireciona para a área do mentorado se já estiver logado

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            # Redirecionar para a área do mentorado ou página inicial após login
            next_page = request.args.get('next') # Captura a página que o usuário tentava acessar
            return redirect(next_page) if next_page else redirect(url_for('mentor_area')) # Redireciona para área do mentorado
        else:
            flash('Login ou senha inválidos.', 'error')

    return render_template('login.html')

# Rota para a página de cadastro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('mentor_area')) # Redireciona se já estiver logado

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validação simples
        if password != confirm_password:
            flash('As senhas não coincidem.', 'error')
            return render_template('register.html')

        # Verificar se o usuário ou email já existe
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe.', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'error')
            return render_template('register.html')

        # Criar novo usuário
        new_user = User(username=username, email=email)
        new_user.set_password(password) # Armazena o hash da senha

        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login')) # Redireciona para login após sucesso
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar. Por favor, tente novamente.', 'error')
            print(f"Erro ao salvar usuário: {e}") # Log para debug

    return render_template('register.html')

# Rota para logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Rota para a Área do Mentorado (requer login)
@app.route('/mentor_area')
@login_required
def mentor_area():
    return render_template('mentor_area.html')

# Rota para o Módulo 1 (requer login)
@app.route('/modulo_01')
@login_required
def modulo_01():
    return render_template('modulo_01.html')

# Rota para a página de Testes e Tarefas (requer login)
@app.route('/tests')
@login_required
def tests():
    return render_template('tests.html')

# Rota para o Teste 01 (requer login)
@app.route('/test_01')
@login_required
def test_01():
    return render_template('test_01.html')

# NOVA ROTA PARA RECEBER O POST DO FORMULÁRIO
@app.route('/api/mentores', methods=['POST'])
@login_required
def handle_mentor_form():
    """
    Recebe os dados do formulário do Carômetro  e salva/atualiza o perfil.
    """
    if request.method == 'POST':
        user_id = current_user.id

        # Verifica se o usuário já tem um perfil (para atualizar) ou se é novo
        profile = Carometro.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = Carometro(user_id=user_id)

        try:
            # 1. Dados Pessoais
            profile.display_name = request.form.get('display_name')
            profile.current_role = request.form.get('current_role')
            profile.company = request.form.get('company')
            profile.start_year_company = request.form.get('start_year_company', type=int)
            profile.city = request.form.get('city')
            profile.linkedin = request.form.get('linkedin')

            # 2. Experiências (Listas complexas)
            # O JS envia listas paralelas[cite: 63]. Usamos zip() para agrupá-las.
            exp_descs = request.form.getlist('experiences[][description]')
            exp_comps = request.form.getlist('experiences[][company]')
            exp_starts = request.form.getlist('experiences[][start_year]')
            exp_ends = request.form.getlist('experiences[][end_year]')

            experiences_list = []
            for desc, comp, start, end in zip(exp_descs, exp_comps, exp_starts, exp_ends):
                experiences_list.append({
                    'description': desc,
                    'company': comp,
                    'start_year': start,
                    'end_year': end
                })
            profile.experiences_json = experiences_list

            # 3. Especialidades
            spec_names = request.form.getlist('specialties[][name]') # [cite: 67]
            spec_insts = request.form.getlist('specialties[][institution]') # [cite: 67]

            specialties_list = []
            for name, inst in zip(spec_names, spec_insts):
                specialties_list.append({'name': name, 'institution': inst})
            profile.specialties_json = specialties_list

            # 4. Conquistas
            ach_descs = request.form.getlist('achievements[][description]') # [cite: 70]
            ach_comps = request.form.getlist('achievements[][company]') # [cite: 70]
            ach_years = request.form.getlist('achievements[][year]') # [cite: 70]

            achievements_list = []
            for desc, comp, year in zip(ach_descs, ach_comps, ach_years):
                achievements_list.append({'description': desc, 'company': comp, 'year': year})
            profile.achievements_json = achievements_list

            # 5. Liderança, Valores e Hobbies (Listas simples)
            profile.leadership_words_json = request.form.getlist('leadership_words[]') # [cite: 72]
            profile.values_json = request.form.getlist('values[]') # [cite: 34]
            profile.hobbies_json = request.form.getlist('hobbies[]') # [cite: 46]

            # 6. Vida Pessoal
            profile.marital_status = request.form.get('marital_status')
            profile.spouse_name = request.form.get('spouse_name') if profile.marital_status in ['Noivo', 'Casado'] else None

            # Filhos (o JS cria inputs child_name_1, child_name_2...) [cite: 83-84]
            children_count = request.form.get('children_number', 0, type=int)
            profile.children_number = children_count
            children_names = []
            if children_count > 0:
                for i in range(1, children_count + 1):
                    name = request.form.get(f'child_name_{i}')
                    if name:
                        children_names.append(name)
            profile.children_names_json = children_names

            # Pets
            profile.pet_count = request.form.get('pet_count', 0, type=int)
            pet_species_str = request.form.get('pet_species_list', '') # [cite: 45]
            # Converte a string "Cachorro, Gato" em uma lista ["Cachorro", "Gato"]
            profile.pet_species_json = [s.strip() for s in pet_species_str.split(',') if s.strip()]

            # 7. Concordância
            profile.agree_terms = request.form.get('agree_terms') == 'on' # [cite: 50]

            # Salvar no banco
            db.session.add(profile)
            db.session.commit()

            flash('Perfil salvo com sucesso!', 'success')
            # Redireciona para a página de 'testes' (onde está o botão 'Voltar' [cite: 51])
            return redirect(url_for('tests'))

        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar Carômetro: {e}") # Log para debug
            flash(f'Erro ao salvar o perfil: {e}', 'error')
            return redirect(url_for('test_01'))

@app.route('/about')
def about():
    return render_template('about_us.html')

# Rota para inicializar o banco de dados (execute uma vez)
@app.cli.command()
def init_db():
    """Inicializa o banco de dados e cria tabelas."""
    db.create_all()
    print('Banco de dados inicializado e tabelas criadas.')
    # Exemplo de criação de um usuário administrador (opcional)
    admin_user = User.query.filter_by(email='admin@stlconsulting.com').first()
    if not admin_user:
        admin_user = User(username='admin', email='admin@stlconsulting.com')
        admin_user.set_password('senha_segura_aqui') # Substitua por uma senha segura
        db.session.add(admin_user)
        db.session.commit()
        print('Usuário administrador criado.')

if __name__ == '__main__':
    # Certifique-se de que a pasta instance existe
    with app.app_context():
        os.makedirs(app.instance_path, exist_ok=True)
    app.run(debug=True)   # debug=True apenas para desenvolvimento!
    # app.run(host='0.0.0.0', port=5000) # Rodar localhost + Túnel Cloudfared
    # app.run(host='192.168.0.19', port=5000) # Rodar na mesma rede Wi-Fi
