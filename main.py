import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import openai

# جلب التوكنات من إعدادات السيرفر (Koyeb) للأمان
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AI_KEY = os.getenv("AI_API_KEY")

def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! أنا رادار الريديوم الذكي، كيف يمكنني مساعدتك اليوم؟")

def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client = openai.OpenAI(api_key=AI_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": update.message.text}]
    )
    await update.message.reply_text(response.choices[0].message.content)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat))
    app.run_polling()