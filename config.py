# config.py
import os
from dotenv import load_dotenv

# load_dotenv()

class Config:
    # URI do banco de dados MySQL
    # Adicione ?charset=utf8mb4 ao final do nome do banco
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        # 'mysql+pymysql://root:Est%40020234@localhost:3306/sch_stl?charset=utf8mb4'
        'mysql+pymysql://root:stlbanco@localhost:3306/sch_stl?charset=utf8mb4'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'uma_chave_secreta_muito_forte_para_sessoes')
