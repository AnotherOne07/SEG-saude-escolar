import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "bd_Plat_Saude"),
    "user": os.getenv("DB_USER", "platSaude"),
    "password": os.getenv("DB_PASSWORD", "engsoft2"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432"))
}
