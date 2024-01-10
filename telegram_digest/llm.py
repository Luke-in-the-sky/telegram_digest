from typing import List
from poe_api_wrapper import PoeApi
import textwrap
from utils import MyLogger
import tiktoken
import re
from logging import DEBUG

logger = MyLogger("bot").logger

setup_statement = """
    Attached is an extract of a chat thread. The participants are mostly 
    users (aka Earn Users) of a company called 'Gemini'. The users have deposits 
    with Gemini (of different crypto currencies), but Gemini can't liquidate these 
    deposits because it has a large loan to a company called Genesis, which is 
    currently in a bankruptcy process. The process has being going on for over a 
    year, and the group of Earn Users leverages this chat thread to organize and 
    to communicate what is happening with the court cases.

    The thread is formatted like this
    [<sender_name_a>] <message_text_1>
    [<sender_name_b>] <message_text_2>
    ...""".strip()

guidelines = """
    1. focus on information that is valuable to Earn Users, for example updates on 
    the case developments or action steps that the Earn Users should take
    2. disregard any message that is purely emotional venting or bickering with other users
    3. format your summary as bullet-points
    4. each bullet-point must be substantiated with quotes from the original extract
    5. always refer to users by their names, never by generic "a user" or "another user"
    6. Start directly with the bullet list, omitting any introductory text.
    """.strip()

prompt_template = """
    {setup_statement}

    ```
    {thread_content}
    ```

    Summarize the extract, ALWAYS following these guidelines:
    {guidelines}
    """.strip()

refine_template = """
    {setup_statement}
    
    We have provided an existing summary up to 
    a certain point: 
    ------------
    {existing_summary}
    ------------
    We have the opportunity to refine the existing summary (only if needed) 
    with some more context below

    ```
    {thread_content}
    ```

    Your job is to produce a final summary: refine the original, if need be, 
    otherwise simply return the original summary.
    ALWAYS follow these guidelines:
    {guidelines}
  """.strip()


def standardize_prompt(txt):
    """
    Remove single newlines (like in Markdown syntax).
    This allows for writing longer prompts in python with multiline strings
    that wrap in the code, but are un-wrapped when sent to the LLM
    """
    txt = re.sub(r"(?i)(\w\s?)\n(\w\w)", r"\1 \2", txt)
    return textwrap.dedent(txt)


class PoeBot:
    def __init__(self, poe_token) -> None:
        logger.info("Building a new PoeBot.")
        self.client = PoeApi(poe_token)

    def send_message(
        self, txt, bot_name="a2", chatCode=None, streaming=True, preclear_context=True
    ) -> str:
        if preclear_context:
            logger.info("Clering context")
            self.client.chat_break(bot_name, chatCode=chatCode)

        logger.info("Sending message to PoeBot")
        for chunk in self.client.send_message(bot_name, txt, chatCode=chatCode):
            assert (
                chunk.get("state") != "error_user_message_too_long"
            ), ">> message too long"
            if streaming:
                print(chunk["response"], end="", flush=True)
        return chunk["text"]

    def get_summary(self, convo_txt, bot="a2", chatCode=None):
        message = prompt_template.format(
            setup_statement=setup_statement, thread_content=convo_txt
        )
        message = standardize_prompt(message)

        # Summarization strategy: stuff-it all in the context
        self.send_message(
            self,
            message,
            bot_name="a2",
            chatCode=chatCode,
            streaming=False,
            preclear_context=True,
        )

    def get_refine_summary(
        self, messages: List[str], bot_name="a2", chatCode=None, max_tokens=4000
    ):
        """
        Splits messages into batches, summarizes them **serially**:
        1. summarize the first
        2. ask to refine the summary with new context
        """
        batcher = TextBatcher(max_tokens=max_tokens)
        batches = batcher.create_batches(messages)
        flattened_batches = ["\n".join(batch) for batch in batches]

        # Summarization strategy: refine
        running_summary = ""
        for i, batch in enumerate(flattened_batches):
            logger.debug(f"Refine summary: batch {i}")
            if i == 0:
                # first message goes with the `prompt_template`
                txt = prompt_template.format(
                    setup_statement=setup_statement,
                    thread_content=batch,
                    guidelines=guidelines,
                )
            else:
                # next messages go with the `refine_template`
                txt = refine_template.format(
                    setup_statement=setup_statement,
                    thread_content=batch,
                    existing_summary=running_summary,
                    guidelines=guidelines,
                )
            txt = standardize_prompt(txt)

            # send txt to LLM
            if logger.isEnabledFor(DEBUG):
                tokens_in_msg = TextBatcher.num_tokens(txt)
                logger.debug(
                    f"Refine summary: sending message, length in tokens: {tokens_in_msg}"
                )
            running_summary = self.send_message(
                txt,
                bot_name=bot_name,
                chatCode=chatCode,
                streaming=False,
                preclear_context=True,
            )

        return running_summary


class TextBatcher:
    """
    Creates batches of text from a list of strings, where the length of each batch
    is < then a given max number of tokens
    """

    def __init__(self, max_tokens, encoding_name="cl100k_base"):
        self.encoding_name = encoding_name
        self.max_tokens = max_tokens

    @staticmethod
    def num_tokens(txt, encoding_name="cl100k_base") -> int:
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(txt))

    def create_batches(self, messages: List[str]) -> List[List[str]]:
        """
        Splits a list of messages into a list of batches
        """
        batches = []
        batch = []
        current_size = 0

        for msg in messages:
            msg_size = TextBatcher.num_tokens(msg, self.encoding_name)
            if current_size + msg_size > self.max_tokens:
                if batch:  # Ensure we don't add empty batches
                    batches.append(batch)
                batch = [msg]
                current_size = msg_size
            else:
                batch.append(msg)
                current_size += msg_size

        if batch:  # Add the last batch if it's not empty
            batches.append(batch)

        return batches
