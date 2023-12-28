import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from config import Config
from utils import MyLogger

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
            client = TelegramClient('anon', api_id, api_hash)
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
          with open('session.txt', 'w') as f:
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

    # def send_message(self, chat_id, message):
    #     try:
    #         logger.info(f"Sending message to chat #{chat_id}")
    #         send_message_url = f"{self.bot_api_url}/sendMessage"
    #         response = requests.post(send_message_url, json={"chat_id": chat_id,
    #                                                           "text": message})
    #         response.raise_for_status()
    #     except Exception as e:
    #         logger.error(f"Failed to send message: {e}")
    #         raise

    async def _from_chat_name_to_chat_id(self, chat_name: str) -> int:
        client = self.core_api_client
        if not self.dialogs:
            async with client:
                self.dialogs = {
                    dialog.name: dialog.id async for dialog in client.iter_dialogs()}
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
        await client.start()
        while continue_fetching:
            msgs = [message async for message in client.iter_messages(
                chat_id, 
                offset_date=end_date,
                limit=batch_size,
                offset_id = offset_id
                )]

            if not msgs or len(msgs)==0:
                logger.warning('  --> No messages')
                break

            for msg in msgs:
                if msg.date >= start_date:
                    all_messages.append(msg)
                else:
                    logger.info('  --> found all messages')
                    continue_fetching = False
                    break

            if len(all_messages) >= total_count_limit:
                break  # Break the loop if the limit is reached

            # update the offset
            offset_id = min([x.id for x in msgs])

        return all_messages
