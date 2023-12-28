import textwrap
import asyncio
from utils import MyLogger
from config import Config
from telegram_bot import TelegramBotBuilder, TelegramMessagesParsing
from llm import PoeBot

logger = MyLogger("bot").logger

async def main():
    bot_builder = TelegramBotBuilder(Config.TELEGRAM_BOT_TOKEN) \
        .with_core_api(Config.TELEGRAM_API_ID, Config.TELEGRAM_API_HASH, api_session_str=Config.TELEGRAM_SESSION_STRING)
    bot = bot_builder.get_bot()
    
    # pull messages
    await bot.set_target_chat_id('Gemini Earn Users')
    messages = await bot.get_messages_between_dates(Config.START_DATE, Config.END_DATE)
    
    # process messages
    telparser = TelegramMessagesParsing(
        bot.core_api_client, bot.target_chat_id, messages
        )
    convo_txt = await telparser.to_str(clean_strings = True)
    convo_txt = convo_txt[-5000:]  #TODO: need a bette summarization startegy, perhaps a recursive

    # get a summary
    poe = PoeBot(Config.POE_PB_TOKEN)
    response = poe.get_summary(convo_txt, bot="a2", chatCode=Config.POE_CHAT_CODE)
    
    # send summary
    logger.info('## Sending summary to telegram')
    async with bot.core_api_client:
        message = f"""Summary: {Config.START_DATE.isoformat()[:10]} - {Config.END_DATE.isoformat()[:10]}

        {response['text']}
        """
        await bot.core_api_send_message('me', textwrap.dedent(message))

if __name__ == "__main__":
    asyncio.run(main())

    