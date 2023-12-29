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
1. re-wrod the prompt based on https://docs.anthropic.com/claude/docs/claude-2p1-guide#experimental-tool-use : first present the data, then ask the question
1. re-word the prompt with "You ALWAYS follow these guidelines when writing your response:"