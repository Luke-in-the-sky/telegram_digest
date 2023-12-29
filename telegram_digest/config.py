from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

class AppConfig(BaseSettings):

    # Telegram
    TELEGRAM_API: str = 'https://api.telegram.org'
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_API_HASH: str
    TELEGRAM_API_ID: str
    TELEGRAM_SESSION_STRING: str

    # Poe
    POE_PB_TOKEN: str
    POE_CHAT_CODE: str

    # Other settings
    TARGET_CHAT_NAME: str = "Gemini Earn Users"
    END_DATE: datetime = datetime.now(ZoneInfo('America/Los_Angeles'))
    START_DATE: datetime = END_DATE - timedelta(days=1)

    # `BaseSettings` will attempt to load from environment
    # and form the .env file, if it exists (former takes precedence, t.ly/2hHDL)
    model_config = SettingsConfigDict(env_file='conf.env')
    
Config = AppConfig()