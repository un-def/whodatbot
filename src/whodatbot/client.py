import asyncio
import string
from typing import Any, Awaitable, Optional, cast

import aiohttp

from .utils import LoggerDescriptor


DEFAULT_URL_TEMPLATE = 'https://api.telegram.org/bot{token}/{method}'


class URLTemplateFormatter(string.Formatter):

    KEYS = ('token', 'method')

    def __init__(self, template: str) -> None:
        self._template = template

    def get_value(self, key, args, kwargs):   # type: ignore
        assert not isinstance(key, int), 'unexpected positional formatting'
        if key in kwargs:
            return kwargs[key]
        return f'{{{key}}}'

    def check_template(self) -> None:
        template = self._template
        expected = sorted((k, '', None) for k in self.KEYS)
        actual = sorted(f[1:] for f in self.parse(template) if f[1])
        if expected != actual:
            raise ValueError(f'invalid url_template: {template}')

    def format_template(self, **kwargs: Any) -> str:
        return self.format(self._template, **kwargs)


class BotAPIClient:

    log = LoggerDescriptor()

    _username: Optional[str] = None

    def __init__(
        self, *, token: str, url_template: Optional[str] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        if url_template is None:
            url_template = DEFAULT_URL_TEMPLATE
        url_formatter = URLTemplateFormatter(url_template)
        url_formatter.check_template()
        self._url_template = url_formatter.format_template(token=token)
        self._session = aiohttp.ClientSession(loop=loop)

    async def close(self) -> None:
        await self._session.close()

    async def _call_api(self, method: str, **params: Any) -> Any:
        url = self._url_template.format(method=method)
        self.log.debug(f'Telegram API call: method={method} params={params}')
        async with self._session.post(url, json=params) as response:
            response_json = await response.json()
        self.log.debug(f'Telegram API response: {response_json}')
        return response_json

    def set_webhook(self, url: str) -> Awaitable[Any]:
        return self._call_api('setWebhook', url=url)

    async def get_username(self, force: bool = False) -> str:
        if self._username is not None and not force:
            return self._username
        response = await self._call_api('getMe')
        username = cast(str, response['result']['username'])
        self.log.debug('Bot username: %s', username)
        self._username = username
        return username
