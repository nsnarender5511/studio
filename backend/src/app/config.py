import os
import tempfile
from pathlib import Path
from pydantic import Field, PostgresDsn, computed_field, AnyUrl
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Define DOTENV_PATH for use in model_config
DOTENV_PATH = Path(__file__).resolve().parent.parent.parent / '.env'

# --- Flattened Config Class --- 
class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=DOTENV_PATH if DOTENV_PATH.exists() else None,
        env_file_encoding='utf-8',
        extra='ignore', # Ignore extra environment variables
        case_sensitive=False, # Match env vars case-insensitively
        env_nested_delimiter='__' # Keep in case needed later
    )

    # Database Configuration
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{Path(__file__).parent.parent.parent.resolve() / 'instance' / 'app.db'}"

    # Celery Configuration
    CELERY_BROKER_URL: AnyUrl = Field(default="redis://localhost:6379/0", validation_alias='REDIS_URL')
    CELERY_RESULT_BACKEND: AnyUrl = Field(default="redis://localhost:6379/1", validation_alias='REDIS_URL')

    # Job File Paths
    CLONE_BASE_DIR: Path = Path(tempfile.gettempdir()) / 'gitdocu_clones'
    OUTPUT_BASE_DIR: Path = Path(__file__).parent.parent.parent.resolve() / 'output'

    # ADK / Google API Configuration
    GOOGLE_API_KEY: str = Field(...)
    SESSION_SERVICE_TYPE: str = 'memory'
    ARTIFACT_SERVICE_TYPE: str = 'memory'
    MEMORY_SERVICE_TYPE: str = 'memory'
    GCP_PROJECT_ID: Optional[str] = None
    GCP_LOCATION: str = "us-central1"

    # Flask Application Configuration
    FLASK_HOST: str = "127.0.0.1"
    FLASK_PORT: int = 5001
    INSTANCE_FOLDER_PATH: Path = Path(__file__).parent.parent.parent.resolve() / 'instance'

# --- Instantiate the flattened config --- 
config = Config()

# --- Directory creation logic removed from here --- 