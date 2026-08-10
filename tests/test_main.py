import importlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import main


@pytest.fixture
def update():
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def context():
    return MagicMock()


async def test_start_replies_with_greeting(update, context):
    await main.start(update, context)

    update.message.reply_text.assert_awaited_once()
    (text,), _ = update.message.reply_text.await_args
    assert "رادار الريديوم" in text


async def test_chat_sends_user_text_to_model(update, context):
    update.message.text = "ما هو سعر الريديوم؟"
    client = MagicMock()
    client.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="answer"))
    ]

    with patch.object(main.openai, "OpenAI", return_value=client) as openai_ctor:
        await main.chat(update, context)

    openai_ctor.assert_called_once_with(api_key=main.AI_KEY)
    client.chat.completions.create.assert_called_once_with(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "ما هو سعر الريديوم؟"}],
    )


async def test_chat_replies_with_model_answer(update, context):
    update.message.text = "hello"
    client = MagicMock()
    client.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="model answer"))
    ]

    with patch.object(main.openai, "OpenAI", return_value=client):
        await main.chat(update, context)

    update.message.reply_text.assert_awaited_once_with("model answer")


async def test_chat_propagates_api_errors(update, context):
    update.message.text = "hello"
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("api down")

    with patch.object(main.openai, "OpenAI", return_value=client):
        with pytest.raises(RuntimeError):
            await main.chat(update, context)

    update.message.reply_text.assert_not_awaited()


def test_tokens_are_read_from_environment():
    env = {"TELEGRAM_BOT_TOKEN": "token-123", "AI_API_KEY": "key-456"}

    with patch.dict("os.environ", env, clear=True):
        reloaded = importlib.reload(main)
        try:
            assert reloaded.TOKEN == "token-123"
            assert reloaded.AI_KEY == "key-456"
        finally:
            importlib.reload(main)


def test_tokens_default_to_none_when_unset():
    with patch.dict("os.environ", {}, clear=True):
        reloaded = importlib.reload(main)
        try:
            assert reloaded.TOKEN is None
            assert reloaded.AI_KEY is None
        finally:
            importlib.reload(main)
