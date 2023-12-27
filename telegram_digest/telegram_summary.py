import os
import asyncio
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.tl.functions.messages import SearchRequest
from telethon.tl.types import InputMessagesFilterEmpty
from openai import ChatCompletion

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import SearchRequest
from telethon.tl.types import InputMessagesFilterEmpty

import pandas as pd


async def get_messages_in_last_n_days(client, group_name, n):
    await client.start()
    entity = await client.get_entity(group_name)
    today = datetime.now()
    n_days_ago = today - timedelta(days=n)
    result = await client(SearchRequest(
        peer=entity,
        q='',
        filter=InputMessagesFilterEmpty(),
        min_date=n_days_ago,
        max_date=today,
        offset_id=0,
        add_offset=0,
        limit=100,
        max_id=0,
        min_id=0,
        from_id=None
    ))
    return result

def summarize(messages):
    conversation = "\n".join([msg.message for msg in messages])
    response = ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Summarize the following conversation."},
            {"role": "user", "content": conversation}
        ],
        temperature=0
    )
    return response.choices[0].message['content']

async def send_message_to_chat(chat_id, message):
    await client.send_message(chat_id, message)

async def main():
    #== Pull params from env variables
    # API keys
    load_env_variables('.env')
    api_id = os.environ['TELEGRAM_API_ID']
    api_hash = os.environ['TELEGRAM_API_HASH']
    # openai.api_key = os.environ['OPENAI_API_KEY']
    # Other params
    group_chat_name = os.environ['GROUP_CHAT_NAME']
    personal_chat_id = os.environ['PERSONAL_CHAT_ID']

    #== Initialize Telegram client
    client = TelegramClient('session_name', api_id, api_hash)

    #== Other params (that we should probably pull out)
    n_days = 7

    #== Run the bot
    messages = await get_messages_in_last_n_days(client, group_chat_name, n_days)
    print(messages)
    # summary = summarize(messages)

    # await send_message_to_chat(personal_chat_id, summary)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(
        main()
        )
