import re
from typing import List
import pandas as pd
from telethon import TelegramClient
from telethon.sessions import StringSession
from config import Config
from utils import (
    MyLogger,
    clean_string,
    standardize_strings,
    replace_urls_with_placeholder,  # TODO: optionally add back
)
from pydantic_models import Message

logger = MyLogger("bot").logger


class TelegramBotBuilder:
    """
    Helper class to set up the Telegram Client
    """

    def __init__(self, token):
        logger.info("Building a new bot.")
        self.bot = TelegramBot(token)

    def with_core_api(self, api_id, api_hash, api_session_str=None):
        logger.info("Setting up core api client.")

        try:
            client = TelegramClient(StringSession(api_session_str), api_id, api_hash)
        except KeyError:
            logger.warning(
                "No session string found, will need to login again. "
                + "See cls._create_a_session_key() for how to get a session string"
            )
            client = TelegramClient("anon", api_id, api_hash)
        self.bot.core_api_client = client
        return self

    def get_bot(self):
        return self.bot

    async def _create_a_session_key(self, api_id, api_hash) -> str:
        """
        Create a new session string, save it to file.

        This class uses the Telethon library, so it will interface as a specific user
        (as opposed to being a bot). This allows to pull the whole history
        of the threads where the user is a participats (bots can only see messages
        after they were added to a thread).
        The downside is: you need to login (2FAC) every time. To reduce friction, you
        can use the session string to keep working with the same session.
        """
        # Generating a new session key
        async with TelegramClient(StringSession(), api_id, api_hash) as client:
            s = client.session.save()
            with open("session.txt", "w") as f:
                f.write(s)


class TelegramBot:
    """
    Telegram bot to pull thread history and send summary messages
    """

    def __init__(self, token):
        self.token = token
        self.bot_api_url = f"{Config.TELEGRAM_API}/bot{self.token}"
        self.core_api_client = None
        self.dialogs = None

    async def core_api_send_message(self, chat_id, message):
        """
        Sending a message with the core api (as opposed to as a bot)
        """
        try:
            logger.info(f"Telegram: sending message to chat `{chat_id}`")
            await self.core_api_client.send_message(chat_id, message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise

    async def _from_chat_name_to_chat_id(self, chat_name: str) -> int:
        client = self.core_api_client
        if not self.dialogs:
            async with client:
                self.dialogs = {
                    dialog.name: dialog.id async for dialog in client.iter_dialogs()
                }
        return self.dialogs.get(chat_name)

    async def set_target_chat_id(self, target_chat_name: str) -> int:
        """
        Set the specific chat we want to summarize. Returns the chat id.
        """
        logger.info(f"Getting the group chat id for `{target_chat_name}`")
        self.target_chat_name = target_chat_name
        self.target_chat_id = await self._from_chat_name_to_chat_id(target_chat_name)
        logger.info(f"  --> found id {self.target_chat_id} for `{target_chat_name}`")
        return self.target_chat_id

    async def get_messages_between_dates(self, start_date, end_date):
        """
        Fetch all messages between the given datetimes. If `mode=='a'`,
        we will append to the previously-pulled list
        Fetching is paginated (batch size=100)
        """
        client = self.core_api_client
        chat_id = self.target_chat_id
        all_messages = []
        total_count_limit = 1000  # Adjust this number based on how many messages you want to retrieve in total
        batch_size = 100
        offset_id = 0
        continue_fetching = True

        logger.info(f"Fetching messages from {start_date} to {end_date}...")
        async with client:
            while continue_fetching:
                msgs = [
                    message
                    async for message in client.iter_messages(
                        chat_id,
                        offset_date=end_date,
                        limit=batch_size,
                        offset_id=offset_id,
                    )
                ]

                if not msgs or len(msgs) == 0:
                    logger.warning("  --> No messages")
                    break

                for msg in msgs:
                    if msg.date >= start_date:
                        all_messages.append(msg)
                    else:
                        logger.info("  --> found all messages")
                        continue_fetching = False
                        break

                if len(all_messages) >= total_count_limit:
                    break  # Break the loop if the limit is reached

                # update the offset
                offset_id = min([x.id for x in msgs])

        return all_messages


class TelegramMessagesParsing:
    """
    Helper class to parse messages
    """

    def __init__(self, client, chat_id, messages, filter_out_autosum_messages: bool=True):
        self.messages = messages
        self.chat_id = chat_id
        self.client = client
        self.participants = None
        self.digest_messages = None
        self.filter_out_autosum_messages = filter_out_autosum_messages

        logger.debug(f"{len(self.messages)=}")

    async def _build_digest_messages(self, render_upstreams=True):
        logger.info("Making Message objects...")
        client = self.client

        # build Message objects
        msgs = [Message.from_telethon_message(x) for x in self.messages if x]

        # optional: remove autosummary msgs
        if self.filter_out_autosum_messages:
            msgs = [x for x in msgs if not SummaryRenderer.is_autosummary(x.text)]

        # optional: fetch upstreams
        if render_upstreams:
            logger.debug("  --> Fetching upstreams...")
            # fetch any upstreams, ie those messages that the present messages are replying to
            upstream_ids_to_be_fetched = {
                x.reply_to_msg_id for x in msgs if x.reply_to_msg_id
            }
            async with client:
                upstreams = await client.get_messages(
                    entity=self.chat_id, ids=list(upstream_ids_to_be_fetched)
                )
            upstreams = {
                u.id: Message.from_telethon_message(u).to_str() for u in upstreams if u
            }

            # Add the "reply_to" text to the messages
            msgs = [x._set_reply_to_msg(upstreams.get(x.reply_to_msg_id)) for x in msgs]

        self.digest_messages = msgs
        logger.debug(f"  {len(self.digest_messages)=}")
        return self

    async def from_sender_id_to_name(self, sender_id: int) -> str:
        """
        Get Sender names
        """
        client = self.client

        if self.participants is None or len(self.participants) == 0:
            logger.info("Building dict of participants")
            async with client:
                self.participants = {
                    x.id: x for x in await client.get_participants(self.chat_id)
                }

        entity = self.participants.get(sender_id)
        if entity is None:
            name = "<NoName>"
        else:
            name = entity.first_name or entity.username
        return name[:10]

    async def to_df(self, clean_strings=True):
        logger.info("Making it a df...")
        msgs = self.messages

        # make it a df
        df = pd.DataFrame(
            [{"msg": x.message, "date": x.date, "sender_id": x.sender_id} for x in msgs]
        ).sort_values(by="date")

        # from user_ids to user names (from_sender_id_to_name is async, so we can't apply directly in pandas)
        users = {
            id: await self.from_sender_id_to_name(int(id))
            for id in df.sender_id.unique()
            if id is not None
        }
        df["sender_name"] = df.sender_id.apply(users.get)

        if clean_strings:
            df = df.dropna()
            df["msg_clean"] = df.msg.apply(lambda x: clean_string(x, replace_urls=True))

        return df

    async def to_list_of_formatted_messages(
        self, clean_strings=True, render_upstreams=True, include_sender_name=True
    ) -> List[str]:
        if self.messages and len(self.messages) > 0 and self.digest_messages is None:
            _ = await self._build_digest_messages(render_upstreams=render_upstreams)

        formatted_messages = [
            x.to_str(include_sender_name=include_sender_name)
            for x in self.digest_messages
        ]

        logger.debug(f"{len(formatted_messages)=}")
        sample = "\n".join(formatted_messages[:5])
        logger.debug(f"Example formatted msgs: {sample}")

        if clean_strings:
            formatted_messages = [
                clean_string(x, replace_urls=True) for x in formatted_messages
            ]
        return formatted_messages


class SummaryRenderer:
    """
    Formatting strings for the auto-summary
    and recognizing when a string is from the auto-summary
    """

    is_autosum_pattern = re.compile(
        r"(?s)\#AutoSummary:.*\(Disclaimer: this is an auto-gen summary\)"
    )

    @staticmethod
    def format(summary: str) -> str:
        formatted = f"""#AutoSummary: from {Config.START_DATE.isoformat()[:10]} to now.

        {summary}

        (Disclaimer: this is an auto-gen summary)"""
        return standardize_strings(formatted)

    @classmethod
    def is_autosummary(cls, msg: str) -> bool:
        try:
            return bool(re.match(cls.is_autosum_pattern, msg))
        except TypeError as e:
            if msg is None: return False
            else: raise e
