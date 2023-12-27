import os

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_API = "https://api.telegram.org"
    TELEGRAM_CORE_API_HASH = os.getenv("TELEGRAM_CORE_API_HASH")
    TELEGRAM_CORE_API_ID = os.getenv("TELEGRAM_CORE_API_ID")
    TELEGRAM_CORE_API_SESSION_STR = os.getenv("TELEGRAM_SESSION_STRING")
    PORT = os.getenv("TELEGRAM_BOT_PORT", 5000)