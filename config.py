# config.py
import os
from dotenv import load_dotenv

# load_dotenv()

class Config:
    # URI do banco de dados MySQL
    # Adicione ?charset=utf8mb4 ao final do nome do banco
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:Est%40020234@localhost:3306/sch_stl?charset=utf8mb4'
        # 'mysql+pymysql://root:stlbanco@localhost:3306/sch_stl?charset=utf8mb4'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'uma_chave_secreta_muito_forte_para_sessoes')

    # --- CONFIGURAÇÕES DE E-MAIL ---
    # Exemplo para Gmail (Requer "Senha de App" se usar verificação em 2 etapas)
    # Se usar hospedagem (Hostgator, Locaweb), use o SMTP deles.
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'ivanilsonguga@gmail.com') # O email que autentica
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'luzeoenxzppttixx')         # A senha do email

    # O endereço que vai aparecer para o usuário ("De:")
    MAIL_DEFAULT_SENDER = ('STL Consulting', 'contato@stlconsulting.com.br')
