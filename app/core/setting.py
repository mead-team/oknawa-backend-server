from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings


class EnvSettings(BaseSettings):
    APP_ENV: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    DEBUG: bool
    ALLOWED_ORIGINS: str
    KAKAO_REST_API_KEY: str
    REDIS_HOST: str
    REDIS_PORT: str
    REDIS_DATABASE: str
    OPEN_DATA_API_URL: str
    TMAP_REST_API_KEY: str
    TMAP_API_URL: str
    GOOGLE_API_KEY: str
    GOOGLE_API_URL: str

    @field_validator("ALLOWED_ORIGINS")
    def parsing_allowed_origins(cls, value):
        if isinstance(value, str):
            return [i.strip() for i in value.split(",")]
        return value


class GlobalSettings(BaseSettings):
    ENV_STATE: str = "dev"

    model_config = ConfigDict(env_file="env/base.env")


class DevSettings(EnvSettings):
    model_config = ConfigDict(env_file="env/dev.env")


class ProdSettings(EnvSettings):
    model_config = ConfigDict(env_file="env/prod.env")


class FactorySettings:
    @staticmethod
    def load():
        env_state = GlobalSettings().ENV_STATE
        if env_state == "dev":
            return DevSettings()
        elif env_state == "prod":
            return ProdSettings()


settings = FactorySettings.load()
