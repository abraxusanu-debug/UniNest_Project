import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _database_uri():
    uri = os.environ.get("UNINEST_DB_URI") or os.environ.get("DATABASE_URL")
    if not uri:
        return "sqlite:///" + os.path.join(BASE_DIR, "uninest.db")
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    if uri.startswith("postgresql://") and "+psycopg" not in uri:
        uri = uri.replace("postgresql://", "postgresql+psycopg://", 1)
    return uri


class Config:
    SECRET_KEY = os.environ.get("UNINEST_SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("UNINEST_JWT_KEY", "dev-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 12
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PUBLIC_BASE_URL = os.environ.get("UNINEST_PUBLIC_BASE_URL", "")


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    TESTING = True
