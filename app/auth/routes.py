from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
# A CORREÇÃO ESTÁ AQUI: Adicionamos login_user, logout_user e login_required de volta
from flask_login import login_user, logout_user, current_user, login_required
from app.extensions import db, mail
from app.models import User
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('mentor.mentor_area'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('mentor.mentor_area'))
        else:
            flash('Login ou senha inválidos.', 'error')

    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('mentor.mentor_area'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('As senhas não coincidem.', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe.', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'error')
            return render_template('auth/register.html')

        new_user = User(username=username, email=email)
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar. Por favor, tente novamente.', 'error')
            print(f"Erro ao salvar usuário: {e}")

    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# --- RECUPERAÇÃO DE SENHA ---

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('mentor.mentor_area'))

    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        flash('Se o e-mail estiver cadastrado, você receberá um link para redefinir sua senha.', 'info')

        if user:
            # Gera token válido por 30 min
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = s.dumps(user.email, salt='recover-key')

            link = url_for('auth.reset_password', token=token, _external=True)

            # Envio de E-mail Real
            msg = Message(
                subject='Redefinição de Senha - STL Consulting',
                recipients=[email],
                html=f"""
                <h3>Olá, {user.username}!</h3>
                <p>Recebemos uma solicitação para redefinir a senha da sua conta.</p>
                <p>Clique no botão abaixo para criar uma nova senha:</p>
                <p>
                    <a href="{link}" style="background-color: #be5108; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Redefinir Senha</a>
                </p>
                <p><small>Ou copie: {link}</small></p>
                <p>Se você não solicitou isso, ignore este e-mail.</p>
                """
            )

            try:
                mail.send(msg)
            except Exception as e:
                print(f"Erro ao enviar e-mail: {e}")
                # Em produção, você pode logar o erro, mas não mostre ao usuário por segurança

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('mentor.mentor_area'))

    try:
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        email = s.loads(token, salt='recover-key', max_age=1800)
    except:
        flash('O link de recuperação é inválido ou expirou.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            flash('As senhas não conferem.', 'error')
            return render_template('auth/reset_password.html', token=token)

        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(password)
            db.session.commit()
            flash('Sua senha foi atualizada com sucesso! Faça login.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)
