from pathlib import Path
import asyncio
import pandas as pd
from pydantic_settings import BaseSettings
from typing import Generator
from typing import List
from config import Config
from telegram_bot import TelegramBotBuilder, TelegramMessagesParsing
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DOCS_OUTPUT_FOLDER = Path("./data_assets/")


def update_config(
    start_date: datetime,
    end_date: datetime,
    render_msg_upstream: bool,
    include_sender_name: bool,
) -> Config:
    # Create an instance of the Config class
    config = Config

    # Update the START_DATE, END_DATE, and render_msg_upstream
    config.START_DATE = start_date
    config.END_DATE = end_date
    config.render_msg_upstream = render_msg_upstream
    config.include_sender_name = include_sender_name

    return config


# TODO: cache (note: can't use lru_cache , unhashable type: 'AppConfig' )
async def get_formatted_messages(Config) -> List[str]:
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
        tel_bot.core_api_client, tel_bot.target_chat_id, messages
    )
    msgs_formatted = await telparser.to_list_of_formatted_messages(
        clean_strings=True,
        render_upstreams=Config.render_msg_upstream,
        include_sender_name=Config.include_sender_name,
    )

    return msgs_formatted


# Function to join messages
def join_messages(
    messages: List[str], n: int, overlap: int, separator: str
) -> Generator[str, None, None]:
    i = 0
    while i < len(messages):
        # Calculate the end index for slicing
        end = min(i + n, len(messages))

        # Yield the joined message
        yield separator.join(messages[i:end])

        # Move the index, considering the overlap
        i = end - overlap if (end - overlap) > i else end


class DocBuilderSetup(BaseSettings):
    doc_builder_setup_name: str
    start_date: datetime
    end_date: datetime
    render_msg_upstream: bool
    include_sender_name: bool
    join_messages_n: int
    join_messages_overlap: int
    join_messages_separator: str = "\n"


async def main():
    end_dates = [
        datetime(2024, 1, 12, tzinfo=ZoneInfo("America/Los_Angeles")),
        datetime(2023, 11, 2, tzinfo=ZoneInfo("America/Los_Angeles")),
    ]
    join_messages_n_values = [1, 5]

    builder_configs = [
        DocBuilderSetup(
            doc_builder_setup_name="testing",
            start_date=end_date - timedelta(days=1),
            end_date=end_date,
            render_msg_upstream=render_msg_upstream,
            include_sender_name=join_messages_n > 1 or render_msg_upstream,
            join_messages_n=join_messages_n,
            join_messages_overlap=0,
            join_messages_separator="\n",
        )
        for end_date in end_dates
        for render_msg_upstream in [True]
        for join_messages_n in join_messages_n_values
    ]

    docs_with_configs = []
    for setup in builder_configs:
        print(setup.model_dump())
        Config = update_config(
            setup.start_date,
            setup.end_date,
            setup.render_msg_upstream,
            include_sender_name=setup.include_sender_name,
        )

        msgs_formatted = await get_formatted_messages(Config)

        # yield text documents
        docs = join_messages(
            msgs_formatted,
            setup.join_messages_n,
            setup.join_messages_overlap,
            setup.join_messages_separator,
        )

        df = pd.DataFrame(
            [
                dict(
                    doc=doc,
                    **setup.model_dump(),
                )
                for doc in docs
            ]
        )

        docs_with_configs.append(df)

    folder = DOCS_OUTPUT_FOLDER
    if not folder.exists():
        folder.mkdir()

    file_name = f"docs_{setup.doc_builder_setup_name}.pkl"
    file_path = folder / file_name

    print("saving")
    pd.concat(docs_with_configs).to_pickle(file_path)


if __name__ == "__main__":
    asyncio.run(main())
