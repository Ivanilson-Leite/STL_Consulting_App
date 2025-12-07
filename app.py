# run.py
import os
from app import create_app, db
from app.models import User

app = create_app()

# Comando CLI personalizado para criar DB e Admin
@app.cli.command("init-db")
def init_db_command():
    """Cria as tabelas do banco de dados e o usuário admin."""
    with app.app_context():
        db.create_all()
        print('Banco de dados inicializado.')

        admin_user = User.query.filter_by(email='admin@stlconsulting.com').first()
        if not admin_user:
            admin_user = User(username='admin', email='admin@stlconsulting.com')
            admin_user.set_password('senha_segura_aqui')
            db.session.add(admin_user)
            db.session.commit()
            print('Usuário Admin criado.')
        else:
            print('Admin já existente.')

if __name__ == '__main__':
  with app.app_context():

      os.makedirs(app.instance_path, exist_ok=True)
      # app.run(debug=True)   # debug=True apenas para desenvolvimento!
      app.run(host='0.0.0.0', port=8080) # Rodar localhost + Túnel Cloudfared
      # app.run(host='192.168.0.19', port=5000) # Rodar na mesma rede Wi-Fi
