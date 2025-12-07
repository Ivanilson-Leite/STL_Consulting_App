# app/main/routes.py
from flask import Blueprint, render_template, request, jsonify
from app.extensions import db
from app.models import Newsletter

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Caminho atualizado: templates/public/index.html
    return render_template('public/index.html')

@main.route('/about')
def about():
    # Caminho atualizado: templates/public/about_us.html
    return render_template('public/about_us.html')

@main.route('/api/newsletter/subscribe', methods=['POST'])
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
