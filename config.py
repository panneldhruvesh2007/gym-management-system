import os

class Config:
    # ── Secrets from environment ──────────────────────────────────────────
    SECRET_KEY      = os.environ.get('SECRET_KEY', 'change-me-in-production')
    SUPABASE_URL    = os.environ.get('SUPABASE_URL', '')
    SUPABASE_KEY    = os.environ.get('SUPABASE_KEY', '')

    # ── File uploads ──────────────────────────────────────────────────────
    UPLOAD_FOLDER       = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH  = 5 * 1024 * 1024          # 5 MB max upload
    ALLOWED_EXTENSIONS  = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # ── Pagination ────────────────────────────────────────────────────────
    MEMBERS_PER_PAGE = 10
    APP_NAME         = 'PowerFit Gym Management'

    # ── Session / Cookie security ─────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY  = True
    SESSION_COOKIE_SAMESITE  = 'Lax'
    SESSION_COOKIE_SECURE    = False   # set True behind HTTPS in production
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    # ── CSRF ──────────────────────────────────────────────────────────────
    WTF_CSRF_ENABLED     = True
    WTF_CSRF_TIME_LIMIT  = 3600

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
