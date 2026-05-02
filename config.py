import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    _db_url = os.getenv("DATABASE_URL", "sqlite:///data/prompts.db")
    # Resolve relative sqlite paths to absolute
    if _db_url.startswith("sqlite:///") and not os.path.isabs(_db_url.replace("sqlite:///", "")):
        _db_url = f"sqlite:///{os.path.join(BASE_DIR, _db_url.replace('sqlite:///', ''))}"
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
    ZHIPU_BASE_URL = os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
    MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
    MIMO_BASE_URL = os.getenv("MIMO_BASE_URL", "https://api.mimo.xiaomi.com/v1")


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
