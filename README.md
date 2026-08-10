# raydium-radar

Telegram bot that forwards user messages to an AI model.

## Configuration

All configuration comes from environment variables; never commit secrets.

| Variable | Required | Description |
| --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | yes | Telegram bot token from BotFather. |
| `AI_API_KEY` | yes | OpenAI API key. |
| `ALLOWED_USER_IDS` | yes | Comma separated Telegram user IDs allowed to use the bot. The bot refuses to start when empty. |
| `AI_MODEL` | no | Model name (default `gpt-3.5-turbo`). |
| `MAX_MESSAGE_LENGTH` | no | Max accepted message length (default `1000`). |
| `MIN_SECONDS_BETWEEN_MESSAGES` | no | Per-user rate limit (default `3`). |

## Run

```bash
pip install -r requirements.txt
python main.py
```
