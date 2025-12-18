# wsgi.py

# Importa a função create_app do seu pacote 'app' (que é a pasta)
from app import create_app

# Cria a instância da aplicação Flask. Esta variável 'app' será usada
# pelo Gunicorn e pela execução local.
app = create_app()

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=8002)
    app.run(debug=True)   # debug=True apenas para desenvolvimento!
