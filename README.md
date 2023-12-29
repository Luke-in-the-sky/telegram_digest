# telegram_digest
Some Telegram chats are way too active for me to keep up with.  Let's pull the last N days from these chats, summarize and send a digest, instead

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
