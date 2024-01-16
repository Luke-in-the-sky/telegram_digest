# telegram_digest
Some Telegram chats are way too active for me to keep up with.  Let's pull the last N days from these chats, summarize and send a digest, instead

## How to
Set your keys for anything that does not have a default value in `AppConfig` (`config.py`):
1. TELEGRAM_BOT_TOKEN: str
1. TELEGRAM_API_HASH: str
1. TELEGRAM_API_ID: str
1. TELEGRAM_SESSION_STRING: str
1. POE_PB_TOKEN: str
1. POE_CHAT_CODE: str

These can be placed in any of the following places:
1. as environment variables (eg `export`), including as secrets that then get exposed as environment variables
1. in a `conf.env` file

then do:
```
$ pip install -r requirements.txt
$ python telegram_digest/main.py
```

## v1
V1 can take arbitrary-length input and uses a refine-summary strategy to summarize.
1. Telegram setup: use individual credentials (not a bot), so we can get the full history
1. llm: leverage Poe (so we can try different llms quickly)
1. summarization: implemented a `refine` strategy
    1. splits input into batches, each having at most `max_token` tokens
    1. iteratively generates a summary (refine-style)
1. config loading: use pydantic_settings.BaseSettings to import either from environment variables (eg github secrets) or from file

## TODO
1. summary quality. 2 issues
    1. no metric to measure quality of one summary vs another
    2. no stability: even the same input against the same poe bot will give different summaries
1. experiment with different bots 
2. experiment with different thread representations
     1. add "reply to.." to identify replies
     2. represent the reply-chains in a more structured form (eg all replies in the same chain are collected and represented together, instead of interleaved in the main thread)
1. interactive: host the bot on heroku / fly.io, so I can interact with it via Telegram
1. consolidate logging

## Code walkthough
1. `main.py` is the entry point.
1. `telegram_bot.py` handles creating of a Telegram client (`TelegramBotBuilder`), pulling history and sending messages (`TelegramBot`) and message-data munging (`TelegramMessagesParsing`)
1. `llm.py` handles interfacing with Poe (sending messages, defining prompts) and has helpers for splitting the text into batches that fit into the context (`TextBatcher`)

# Lessons learned
1. Telegram interface
    1. `telethon` is what you want to use
    1. You can interface as your own user or as a bot. 
        1. my account --> bot: I thought I wanted to do as myself, then I discovered the bots, which have a simpler api
        2. bot --> myself: then I discovered bots can only see the conversation once they are added to a thread, and even then they can see only the messages sent *after* they were added
        3. [?] myself --> bot: having a bot is nice because you can interact with it (eg passing different ocnfig arguments) and is more clear who is doing what, see 
            1. https://medium.com/hyperskill/telegram-conversation-summarizer-bot-with-chatgpt-and-flask-quart-bb2e19884c 
            1. https://github.com/yellalena/telegram-gpt-summarizer/blob/92ee101ba3b2633560e65049e8e14d4851a88bc1/main.py#L28
1. Summarization
    1. **strategies**: langchain details 2 summarization strategies (stuff-it-all in the prompt, map-reduce or refine).
    1. **metrics**: it's unclear how to measure quality: if you have a reference summary you can measure similarity to the reference, but if you don't have a reference metrics might not be very reliable: https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00417/107833/A-Statistical-Analysis-of-Summarization-Evaluation
1. `pydantic_settings.BaseSettings` is very useful for loading config from environment variables and files.
