import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── Application ──────────────────────────────────────────
    SECRET_KEY          = os.getenv('SECRET_KEY', 'enredd-green-campus-secret-2024')
    DEBUG               = os.getenv('DEBUG', 'False') == 'True'
    TESTING             = False

    # ── Database ─────────────────────────────────────────────
    DB_USER             = os.getenv('DB_USER', 'root')
    DB_PASSWORD         = os.getenv('DB_PASSWORD', '')
    DB_HOST             = os.getenv('DB_HOST', 'localhost')
    DB_PORT             = os.getenv('DB_PORT', '3306')
    DB_NAME             = os.getenv('DB_NAME', 'green_campus_db')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }

    # ── JWT ───────────────────────────────────────────────────
    JWT_SECRET_KEY          = os.getenv('JWT_SECRET_KEY', 'jwt-enredd-secret-2024')
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # ── File Upload ───────────────────────────────────────────
    UPLOAD_FOLDER       = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH  = 16 * 1024 * 1024          # 16 MB
    ALLOWED_EXTENSIONS  = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # ── Supabase Storage ──────────────────────────────────────
    SUPABASE_URL        = os.getenv('SUPABASE_URL')
    SUPABASE_KEY        = os.getenv('SUPABASE_KEY')
    STORAGE_BUCKET      = os.getenv('SUPABASE_STORAGE_BUCKET', 'Map-files')
    SIGNED_URL_EXPIRY   = 3600  # 1 hour

    # ── Logging ───────────────────────────────────────────────
    LOG_FOLDER          = os.path.join(os.path.dirname(__file__), 'logs')

    # ── Campus Location (ENREDD Batna) ────────────────────────
    CAMPUS_LAT          = 35.5641
    CAMPUS_LNG          = 6.1845
    CAMPUS_NAME         = "ENREDD - Batna, Algeria"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}