from app import create_app

# Cria a instância da aplicação que o Gunicorn vai usar
app = create_app()

if __name__ == "__main__":
    app.run()
