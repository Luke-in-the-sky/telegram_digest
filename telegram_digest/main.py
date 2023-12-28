from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import asyncio
from utils import MyLogger
from config import Config
from telegram_bot import TelegramBotBuilder, TelegramMessagesParsing
from llm import PoeBot

logger = MyLogger("bot").logger

async def main():
    bot_builder = TelegramBotBuilder(Config.TELEGRAM_TOKEN) \
        .with_core_api(Config.TELEGRAM_CORE_API_ID, Config.TELEGRAM_CORE_API_HASH, api_session_str=Config.TELEGRAM_CORE_API_SESSION_STR)
    bot = bot_builder.get_bot()
    
    # pull messages
    await bot.set_target_chat_id('Gemini Earn Users')
    current_time = datetime.now(ZoneInfo('America/Los_Angeles'))
    end_date = current_time - timedelta(days=1)
    start_date = end_date - timedelta(days=1)
    messages = await bot.get_messages_between_dates(start_date , end_date)
    
    # process messages
    telparser = TelegramMessagesParsing(
        bot.core_api_client, bot.target_chat_id, messages
        )
    convo_txt = await telparser.to_str(clean_strings = True)
    convo_txt = convo_txt[:5000]  #TODO: need a bette summarization startegy, perhaps a recursive

    # get a summary
    poe = PoeBot(Config.POE_PB_TOKEN)
    response = poe.get_summary(convo_txt, bot="a2", chatCode=Config.POE_CHAT_CODE)
    
    # send summary
    logger.info('## Sending summary to telegram')
    async with bot.core_api_client:
        await bot.core_api_send_message('me', f'Summary: {start_date.isoformat()[:10]} - {end_date.isoformat()[:10]}')
        await bot.core_api_send_message('me', response['text'])


if __name__ == "__main__":
    asyncio.run(main())

    