import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError(
            "❌ DATABASE_URL n'est pas définie dans les variables d'environnement.\n"
            "   Sur Railway : Settings → Variables → ajouter DATABASE_URL\n"
            "   En local : fichier .env avec DATABASE_URL=..."
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 5,
        'max_overflow': 10,
        'connect_args': {
            'connect_timeout': 10,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5,
        }
    }
    SITE_NAME = "LCE - Leader Chiffre Entreprise"
    SITE_DESCRIPTION = "Centre professionnel de formation en conduite d'engins de manutention, logistique et transport."
    # Resend Email API
    RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
    RESEND_FROM = os.getenv('RESEND_FROM', 'LCE <contact@lcetg.com>')
    RESEND_DOMAIN = os.getenv('RESEND_DOMAIN', 'lcetg.com')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
    # Web Push VAPID Keys
    VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', '')
    VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', '')
    VAPID_CLAIMS_EMAIL = os.getenv('VAPID_CLAIMS_EMAIL', 'contact@lcetg.com')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}