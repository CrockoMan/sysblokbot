import pytest

import os
from typing import List

from telethon import TelegramClient
from telethon.tl.custom.message import Message

from conftest import telegram_bot_name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'command',
    (
        '/start',
        '/get_trello_board_state',
        '/get_publication_plans',
        '/get_editorial_report',
        '/bad_cmd',
    )
)
async def test_not_failing(client: TelegramClient, command: str):
    # Create a conversation
    async with client.conversation(telegram_bot_name, timeout=120) as conv:
        await conv.send_message(command)
        resp: Message = await conv.get_response()
        assert resp.raw_text
