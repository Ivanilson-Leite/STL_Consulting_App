import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave-padrao-insegura')

    # Monta a URL do banco dinamicamente
    DB_USER = os.getenv('MYSQL_USER', 'root')
    DB_PASS = os.getenv('MYSQL_PASSWORD', '')
    DB_HOST = os.getenv('MYSQL_HOST', 'localhost')
    DB_NAME = os.getenv('MYSQL_DB', 'sch_stl')

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # E-mail
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('STL Consulting', os.getenv('MAIL_USERNAME'))
