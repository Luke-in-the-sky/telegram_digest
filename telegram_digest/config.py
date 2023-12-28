from pydantic_settings import BaseSettings
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

class AppConfig(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_API: str = 'https://api.telegram.org'
    TELEGRAM_API_HASH: str
    TELEGRAM_API_ID: str
    TELEGRAM_SESSION_STRING: str
    POE_PB_TOKEN: str
    POE_CHAT_CODE: str

    END_DATE: datetime = datetime.now(ZoneInfo('America/Los_Angeles'))
    START_DATE: datetime = END_DATE - timedelta(days=1)

    class Config:
        """
        This will try to load form the env_file, 
        and if none is found, will load from the environment variables
        """
        env_file = ".env"
        env_file_encoding = 'utf-8'

Config = AppConfig()