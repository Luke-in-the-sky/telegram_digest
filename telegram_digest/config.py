from pydantic import BaseSettings

class AppConfig(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_API: str = 'https://api.telegram.org'
    TELEGRAM_API_HASH: str
    TELEGRAM_API_ID: str
    TELEGRAM_SESSION_STRING: str
    POE_PB_TOKEN: str
    POE_CHAT_CODE: str

    class Config:
        """
        This will try to load form the env_file, 
        and if none is found, will load from the environment variables
        """
        env_file = ".env"
        env_file_encoding = 'utf-8'

Config = AppConfig()