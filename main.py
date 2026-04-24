import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)

try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM tb_vendas'))
        count = result.scalar()
        print(f'Conexão OK! tb_vendas tem {count} registros.')
except Exception as e:
    print(f'Erro na conexão: {e}')
