# app/models.py
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.dialects.mysql import LONGTEXT
from datetime import datetime

# -------------------------------------------------------------------
# MODELO USER (ATUALIZADO)
# -------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='mentee', nullable=False) # 'mentor' ou 'mentee'
    active = db.Column(db.Boolean, default=True, nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    # --------------------

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relacionamentos
    tasks = db.relationship('UserTask', back_populates='user', cascade="all, delete-orphan")
    carometro = db.relationship('Carometro', back_populates='user', uselist=False, cascade="all, delete-orphan")
    appointments = db.relationship('Appointment', back_populates='user', cascade="all, delete-orphan")

    # Auto-relacionamento: Mentor vê seus Mentorados
    mentees = db.relationship('User',
                              backref=db.backref('my_mentor', remote_side=[id]),
                              foreign_keys=[mentor_id])

    # Propriedade auxiliar para verificar se é mentor no HTML
    @property
    def is_mentor(self):
        return self.role == 'mentor'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# -------------------------------------------------------------------
# NOVO: MODELO DE LOCAIS DO MENTOR
# -------------------------------------------------------------------
class MentorLocation(db.Model):
    __tablename__ = 'mentor_locations'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)     # Ex: Escritório, Google Meet
    address = db.Column(db.String(255), nullable=True)   # Endereço físico
    type = db.Column(db.String(20), nullable=False)      # 'presencial' ou 'online'

    mentor = db.relationship('User', backref='locations')

# -------------------------------------------------------------------
# MODELO DISPONIBILIDADE DO MENTOR (ATUALIZADO)
# -------------------------------------------------------------------
class MentorAvailability(db.Model):
    __tablename__ = 'mentor_availability'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # FK para o local escolhido
    location_id = db.Column(db.Integer, db.ForeignKey('mentor_locations.id'), nullable=True)

    datetime_slot = db.Column(db.DateTime, nullable=False)

    # Campo legado (pode manter como backup visual ou remover depois)
    location = db.Column(db.String(255), nullable=True)

    meeting_link = db.Column(db.String(255), nullable=True) # Link específico da reunião
    is_booked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relacionamentos
    mentor = db.relationship('User', foreign_keys=[mentor_id])
    location_rel = db.relationship('MentorLocation') # Para acessar detalhes do local

# -------------------------------------------------------------------
# NOVO: MODELO RECURSOS/MODELOS
# -------------------------------------------------------------------
class ModuleResource(db.Model):
    __tablename__ = 'module_resources'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module_name = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# -------------------------------------------------------------------
# NOVO: MODELO DE DEFINIÇÃO DE TAREFAS
# -------------------------------------------------------------------
class ModuleTask(db.Model):
    __tablename__ = 'module_tasks'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    module_name = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)

    # Modelo para download (Template)
    resource_id = db.Column(db.Integer, db.ForeignKey('module_resources.id'), nullable=True)
    resource = db.relationship('ModuleResource')

    external_link = db.Column(db.String(255), nullable=True)
    allow_upload = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# -------------------------------------------------------------------
# MODELO DE TAREFAS/ATIVIDADES DO USUÁRIO
# -------------------------------------------------------------------
class UserTask(db.Model):
    __tablename__ = 'user_tasks'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Agora vinculamos ao ID da tarefa, não só ao nome
    task_id = db.Column(db.Integer, db.ForeignKey('module_tasks.id'), nullable=True)
    task_definition = db.relationship('ModuleTask') # Para acessar titulo/descrição

    # Mantemos module_name e task_name por compatibilidade legado, mas o ideal é usar task_id
    module_name = db.Column(db.String(50), nullable=False)
    task_name = db.Column(db.String(100), nullable=False)

    status = db.Column(db.String(50), default='Pendente', nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    submitted_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    user = db.relationship('User', back_populates='tasks')

# -------------------------------------------------------------------
# MODELO CARÔMETRO
# -------------------------------------------------------------------
class Carometro(db.Model):
    __tablename__ = 'tbl_carometro'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    current_role = db.Column(db.String(150), nullable=True)
    company = db.Column(db.String(150), nullable=True)
    start_year_company = db.Column(db.SmallInteger, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    linkedin = db.Column(db.String(255), nullable=True)
    experiences_json = db.Column(db.JSON, nullable=True)
    specialties_json = db.Column(db.JSON, nullable=True)
    achievements_json = db.Column(db.JSON, nullable=True)
    leadership_words_json = db.Column(db.JSON, nullable=True)
    values_json = db.Column(db.JSON, nullable=True)
    hobbies_json = db.Column(db.JSON, nullable=True)
    marital_status = db.Column(db.Enum('Solteiro', 'Noivo', 'Casado'), nullable=True)
    spouse_name = db.Column(db.String(150), nullable=True)
    children_number = db.Column(db.SmallInteger, nullable=False, default=0)
    children_names_json = db.Column(db.JSON, nullable=True)
    pet_count = db.Column(db.SmallInteger, nullable=False, default=0)
    pet_species_json = db.Column(db.JSON, nullable=True)
    agree_terms = db.Column(db.Boolean, nullable=False, default=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    user = db.relationship('User', back_populates='carometro')

    def __repr__(self):
        return f'<Carometro para {self.display_name}>'

# -------------------------------------------------------------------
# MODELO AGENDAMENTOS
# -------------------------------------------------------------------
class Appointment(db.Model):
    __tablename__ = 'appointments'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module_name = db.Column(db.String(50), nullable=False)
    schedule_date = db.Column(db.String(50), nullable=False)
    availability_id = db.Column(db.Integer, db.ForeignKey('mentor_availability.id'), nullable=True)
    slot = db.relationship('MentorAvailability')

    # ALTERADO DE 50 PARA 255 PARA CABER ENDEREÇOS LONGOS
    location = db.Column(db.String(255), nullable=False)

    status = db.Column(db.String(50), default='Aguardando confirmação', nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', back_populates='appointments')

    def __repr__(self):
        return f'<Appointment {self.module_name} - {self.user.username}>'

# -------------------------------------------------------------------
# MODELO NEWSLETTER
# -------------------------------------------------------------------
class Newsletter(db.Model):
    __tablename__ = 'newsletter'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Newsletter {self.email}>'

# -------------------------------------------------------------------
# MODELOS DE CONTATO E OUTROS
# -------------------------------------------------------------------
class Contact(db.Model):
    __tablename__ = 'contact'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    message = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Contact {self.name}>'

class Testimonial(db.Model):
    __tablename__ = 'testimonial'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    date_added = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Testimonial {self.name} from {self.company}>'

class Article(db.Model):
    __tablename__ = 'article'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=db.func.current_timestamp())
    tagline = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f'<Article {self.title}>'
