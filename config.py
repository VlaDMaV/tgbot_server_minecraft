from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    bot_token: SecretStr
    admin_id: int
    mc_host: SecretStr
    mc_port: int
    rcon_port: int
    rcon_pass: SecretStr
    ssh_user: SecretStr
    ssh_pass: SecretStr
    ssh_port: int
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


config = Settings()