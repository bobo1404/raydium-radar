import logging
import os
import time

import openai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AI_KEY = os.getenv("AI_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "gpt-3.5-turbo")

# Comma separated Telegram user IDs allowed to talk to the bot.
ALLOWED_USER_IDS = {
    int(uid)
    for uid in os.getenv("ALLOWED_USER_IDS", "").replace(" ", "").split(",")
    if uid
}

MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "1000"))
MIN_SECONDS_BETWEEN_MESSAGES = float(os.getenv("MIN_SECONDS_BETWEEN_MESSAGES", "3"))

_last_request_at: dict[int, float] = {}


def is_authorized(update: Update) -> bool:
    user = update.effective_user
    if user is None:
        return False
    if not ALLOWED_USER_IDS:
        return False
    return user.id in ALLOWED_USER_IDS


def is_rate_limited(user_id: int) -> bool:
    now = time.monotonic()
    previous = _last_request_at.get(user_id)
    if previous is not None and now - previous < MIN_SECONDS_BETWEEN_MESSAGES:
        return True
    _last_request_at[user_id] = now
    return False


def user_id_of(update: Update) -> int | None:
    return update.effective_user.id if update.effective_user else None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        logger.warning("Rejected /start from unauthorized user %s", user_id_of(update))
        await update.message.reply_text("عذراً، غير مصرح لك باستخدام هذا البوت.")
        return
    await update.message.reply_text(
        "مرحباً! أنا رادار الريديوم الذكي، كيف يمكنني مساعدتك اليوم؟"
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        logger.warning("Rejected message from unauthorized user %s", user_id_of(update))
        await update.message.reply_text("عذراً، غير مصرح لك باستخدام هذا البوت.")
        return

    user_id = update.effective_user.id
    if is_rate_limited(user_id):
        await update.message.reply_text("الرجاء الانتظار قليلاً قبل إرسال رسالة أخرى.")
        return

    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text("الرجاء إرسال نص صالح.")
        return
    if len(text) > MAX_MESSAGE_LENGTH:
        await update.message.reply_text(
            f"الرسالة طويلة جداً، الحد الأقصى {MAX_MESSAGE_LENGTH} حرف."
        )
        return

    client = openai.AsyncOpenAI(api_key=AI_KEY)
    try:
        response = await client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": text}],
        )
    except Exception:
        logger.exception("AI request failed")
        await update.message.reply_text("حدث خطأ أثناء معالجة طلبك، حاول لاحقاً.")
        return

    await update.message.reply_text(response.choices[0].message.content)


def main() -> None:
    if not TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")
    if not AI_KEY:
        raise SystemExit("AI_API_KEY is not set")
    if not ALLOWED_USER_IDS:
        raise SystemExit(
            "ALLOWED_USER_IDS is not set; refusing to start an unauthenticated bot"
        )

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat))
    app.run_polling()


if __name__ == "__main__":
    main()
