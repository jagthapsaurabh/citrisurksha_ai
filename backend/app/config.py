import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent

def running_in_docker() -> bool:
    return Path('/.dockerenv').exists() or os.getenv('RUNNING_IN_DOCKER', '').lower() in {'1', 'true', 'yes'}

class Settings(BaseSettings):
    # Absolute env file paths work whether you run from project root or directly from backend folder.
    # Environment variables still override these files.
    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / '.env', BACKEND_DIR / '.env'),
        env_file_encoding='utf-8',
        extra='ignore',
    )

    app_env: str = 'development'
    api_secret_key: str = 'change-me'

    # Either set DATABASE_URL directly, or set DB_* fields below.
    database_url: str | None = None
    db_driver: str = 'postgresql+psycopg2'
    db_host: str = 'localhost'
    db_port: int = 5432
    db_name: str = 'citrisurksha'
    db_user: str = 'postgres'
    db_password: str = ''
    auto_localhost_db_fallback: bool = True

    redis_url: str = 'redis://localhost:6379/0'
    ai_service_url: str = 'http://localhost:8100'
    upload_dir: str = '/app/uploads'
    access_token_minutes: int = 60 * 24 * 7

    def build_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.db_driver.startswith('sqlite'):
            return 'sqlite:///./citrisurksha.db'
        auth = self.db_user
        if self.db_password:
            auth += f':{self.db_password}'
        return f'{self.db_driver}://{auth}@{self.db_host}:{self.db_port}/{self.db_name}'

settings = Settings()

# Normalize database URL after env loading.
settings.database_url = settings.build_database_url()

# If someone runs backend without Docker but kept Docker Compose hostname `postgres`,
# transparently use localhost so Windows/no-Docker works without editing code.
if settings.auto_localhost_db_fallback and not running_in_docker() and settings.database_url:
    parsed = urlsplit(settings.database_url)
    if parsed.hostname == 'postgres':
        netloc = parsed.netloc.replace('@postgres', '@localhost')
        if parsed.netloc == 'postgres' or parsed.netloc.startswith('postgres:'):
            netloc = parsed.netloc.replace('postgres', 'localhost', 1)
        settings.database_url = urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))

# Same convenience fallback for Redis/AI service hostnames when not running Docker.
if not running_in_docker():
    settings.redis_url = settings.redis_url.replace('redis://redis:', 'redis://localhost:')
    settings.ai_service_url = settings.ai_service_url.replace('http://ai-service:', 'http://localhost:')
    if settings.upload_dir == '/app/uploads':
        settings.upload_dir = str(PROJECT_ROOT / 'storage' / 'uploads')

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
