import os
from utils import load_env_variables
load_env_variables(".env")

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_API = "https://api.telegram.org"
    TELEGRAM_CORE_API_HASH = os.getenv("TELEGRAM_API_HASH")
    TELEGRAM_CORE_API_ID = os.getenv("TELEGRAM_API_ID")
    TELEGRAM_CORE_API_SESSION_STR = os.getenv("TELEGRAM_SESSION_STRING")
    POE_PB_TOKEN = os.getenv("POE_PB_TOKEN")
    POE_CHAT_CODE = os.getenv("POE_CHAT_CODE")