from sentence_transformers import SentenceTransformer
from typing import List, Iterable
from config import Config

from config import Config
from telegram_bot import TelegramBotBuilder, TelegramMessagesParsing
from embedding_manager import EmbeddingManager


def update_config(
    start_date: str, end_date: str, render_msg_upstream: bool, include_sender_name: bool
) -> Config:
    # Create an instance of the Config class
    config = Config()

    # Update the START_DATE, END_DATE, and render_msg_upstream
    config.START_DATE = start_date
    config.END_DATE = end_date
    config.render_msg_upstream = render_msg_upstream
    config.include_sender_name = include_sender_name

    return config


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
def join_messages(messages, n, overlap, separator):
    joined_messages = []
    i = 0
    while i < len(messages):
        # Calculate the end index for slicing
        end = min(i + n, len(messages))
        # Join the messages and add to the list
        joined_messages.append(separator.join(messages[i:end]))
        # Move the index, considering the overlap
        i = end - overlap if (end - overlap) > i else end
    return joined_messages


async def build_docs_and_embeddings(
    start_date: str,
    end_date: str,
    render_msg_upstream: bool,
    include_sender_name: bool,
    join_messages_n: int,
    join_messages_overlap: int,
    join_messages_separator: str = "\n",
) -> Iterable[Iterable]:
    # Example usage
    Config = update_config(
        start_date,
        end_date,
        render_msg_upstream,
        include_sender_name=include_sender_name,
    )

    msgs_formatted = await get_formatted_messages(Config)

    # build text documents
    docs = join_messages(
        msgs_formatted, join_messages_n, join_messages_overlap, join_messages_separator
    )

    # build embeddings
    sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
    emb_manager = EmbeddingManager(filename="./data_assets/emb_storage.pkl")
    return emb_manager.get_embeddings(sentence_model=sentence_model, docs=docs)
