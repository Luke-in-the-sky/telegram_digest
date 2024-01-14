import asyncio
from utils import MyLogger, standardize_strings
from config import Config
from telegram_bot import TelegramBotBuilder, TelegramMessagesParsing, SummaryRenderer
from llm import PoeBot
from logging import DEBUG, INFO

logger = MyLogger("bot").logger
logger.setLevel(DEBUG)


async def main():
    # Build a Telegram client
    tel_bot = (
        TelegramBotBuilder(Config.TELEGRAM_BOT_TOKEN)
        .with_core_api(
            Config.TELEGRAM_API_ID,
            Config.TELEGRAM_API_HASH,
            api_session_str=Config.TELEGRAM_SESSION_STRING,
        )
        .get_bot()
    )

    # pull Telegram messages
    await tel_bot.set_target_chat_id(Config.TARGET_CHAT_NAME)
    messages = await tel_bot.get_messages_between_dates(
        Config.START_DATE, Config.END_DATE
    )

    # process messages
    telparser = TelegramMessagesParsing(
        tel_bot.core_api_client,
        tel_bot.target_chat_id,
        messages,
        filter_out_autosum_messages=Config.filter_out_autosum_messages,
    )

    msgs_formatted = await telparser.to_list_of_formatted_messages(
        clean_strings=True,
        render_upstreams=Config.render_msg_upstream,
        include_sender_name=Config.include_sender_name,
    )

    # get a summary
    poe = PoeBot(Config.POE_PB_TOKEN)
    summary = poe.get_refine_summary(
        msgs_formatted, bot_name="a2", chatCode=Config.POE_CHAT_CODE, max_tokens=4000
    )

    async with tel_bot.core_api_client:
        for chat_name in Config.OUTPUT_CHAT_NAMES:
            logger.info("## Sending summary to telegram chat `{chat_name}`")
            await tel_bot.core_api_send_message(
                chat_id=chat_name,
                message=SummaryRenderer.format(summary),
            )


if __name__ == "__main__":
    asyncio.run(main())
