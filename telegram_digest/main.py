from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import asyncio
from utils import MyLogger
from config import Config
from telegram_bot import TelegramBotBuilder

logger = MyLogger("bot").logger

async def main():
    bot_builder = TelegramBotBuilder(Config.TELEGRAM_TOKEN) \
        .with_core_api(Config.TELEGRAM_CORE_API_ID, Config.TELEGRAM_CORE_API_HASH, api_session_str=Config.TELEGRAM_CORE_API_SESSION_STR)
    bot = bot_builder.get_bot()


    # if bot.core_api_client:
    await bot.core_api_client.connect()
    await bot.core_api_client.start()

    await bot.set_target_chat_id('Gemini Earn Users')
    print(bot.target_chat_id)


    # pull messages
    # Get the current time with timezone
    current_time = datetime.now(ZoneInfo('America/Los_Angeles'))
    end_date = current_time - timedelta(days=1)
    start_date = end_date - timedelta(days=1)
    out = await bot.get_messages_between_dates(start_date , end_date)
    print(out)

if __name__ == "__main__":
    asyncio.run(main())

    

