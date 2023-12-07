import os
import asyncio
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.tl.functions.messages import SearchRequest
from telethon.tl.types import InputMessagesFilterEmpty
from openai import ChatCompletion

api_id = os.environ['TELEGRAM_API_ID']
api_hash = os.environ['TELEGRAM_API_HASH']
openai_api_key = os.environ['OPENAI_API_KEY']

openai.api_key = openai_api_key

client = TelegramClient('session_name', api_id, api_hash)

async def get_messages_in_last_n_days(group_name, n):
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
    group_name = os.environ['GROUP_USERNAME']
    personal_chat_id = os.environ['PERSONAL_CHAT_ID']
    n_days = 7

    messages = await get_messages_in_last_n_days(group_name, n_days)
    summary = summarize(messages)

    await send_message_to_chat(personal_chat_id, summary)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())