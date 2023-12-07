from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class GlobalSettings(BaseSettings):
    ENV_STATE: str = "dev"
    APP_ENV: str = "dev"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    DEBUG: bool
    ALLOWED_ORIGINS: str
    KAKAO_REST_API_KEY: str
    TMAP_REST_API_KEY: str
    REDIS_HOST: str
    REDIS_PORT: str
    REDIS_DATABASE: str
    OPEN_DATA_API_URL: str

    model_config = ConfigDict(env_file="env/base.env")


class DevSettings(GlobalSettings):
    model_config = ConfigDict(env_file="env/dev.env")


class ProdSettings(GlobalSettings):
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
