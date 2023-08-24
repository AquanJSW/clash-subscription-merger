"""Telegram bot module."""
import json
import logging
from concurrent.futures import ThreadPoolExecutor

import requests

import config

logger = logging.getLogger(config.APP_NAME).getChild(__name__)


class TelegramBot:
    """Telegram bot class."""

    _HEADERS = {
        'Content-Type': 'application/json',
        'Proxy-Authorization': 'Basic base64',
    }
    _DATA = {
        'parse_mode': 'HTML',
        'disable_notification': True,
    }

    def __init__(self, api_key, chat_id):
        self._base_url = f'https://api.telegram.org/bot{api_key}'
        self._data = self._DATA.copy()
        self._data['chat_id'] = chat_id
        self._executor = ThreadPoolExecutor()

    def send_message(self, message, timeout=5):
        """Send a message to the chat."""

        def _send_message():
            data = self._data.copy()
            data['text'] = message
            data = json.dumps(data)
            url = f'{self._base_url}/sendMessage'
            with requests.post(
                url,
                data=data,
                headers=self._HEADERS,
                timeout=timeout,
            ) as response:
                if not response.ok:
                    logger.debug(
                        'Failed to send message "%s" to Telegram. Response: %s',
                        message,
                        response.text,
                    )
                return response

        return self._executor.submit(_send_message)
