from poe_api_wrapper import PoeApi
import textwrap
from utils import MyLogger

logger = MyLogger("bot").logger

class PoeBot:
    def __init__(self, poe_token) -> None:
        logger.info("Building a new PoeBot.")
        self.client = PoeApi(poe_token)

    def get_summary(self, convo_txt, bot="a2", chatCode=None):
        # clear previous context
        self.client.chat_break(bot, chatCode=chatCode)

        message_template = f"""Here's an extract of a chat thread. The participants are mostly
        users (aka Earn Users) of a company called 'Gemini'. The users have deposits 
        with Gemini (of different crypto currencies), but Gemini can't liquidate these 
        deposits because it has a large loan to a company called Genesis, which is 
        currently in a bankruptcy process. The process has being going on for over a 
        year, and the group of earn users leverages this chat thread to organize and 
        to communicate what is happening with the court cases.

        The following is only a short extract, not the full thread. It's formatted like this
        [<sender_name_a>] <message_text_1>
        [<sender_name_b>] <message_text_2>
        ...

        Summarize this extract following these guidelines:
        1. focus on information that is valuable to Earn Users, for example updates on 
        the case developments or action steps that the Earn Users should take;
        2. disregard any message that is purely emotional venting or bickering with other users
        3. format your summary as bullet-points
        4. each bullet-point must be substantiated with quotes from the original extract
        5. always refer to users by their names, never by generic "a user" or "another user"

        ```
        {convo_txt}
        ```"""
        message = textwrap.dedent(message_template)

        logger.info("Sending message to PoeBot.")
        for chunk in self.client.send_message(bot, message, chatCode=chatCode):
            assert chunk.get('state') != 'error_user_message_too_long', '>> message too long'
            # print(chunk["response"], end="", flush=True)
            print('.', end="")
        return chunk