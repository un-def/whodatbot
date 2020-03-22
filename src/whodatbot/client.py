import asyncio
from typing import Any, Awaitable, Optional, cast

import aiohttp

from .utils import LoggerDescriptor, TemplateFormatter


DEFAULT_URL_TEMPLATE = 'https://api.telegram.org/bot{token}/{method}'


class URLTemplateFormatter(TemplateFormatter):

    required_fields = ('token', 'method')


class BotAPIClientError(Exception):

    def __init__(self, error_code: int, description: str) -> None:
        self.error_code = error_code
        self.description = description

    def __str__(self) -> str:
        cls_name = self.__class__.__name__
        return f'<{cls_name}: [{self.error_code}] {self.description}>'

    def __repr__(self) -> str:
        return str(self)


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
        self._url_template = url_formatter(token=token)
        self._session = aiohttp.ClientSession(loop=loop)

    async def close(self) -> None:
        await self._session.close()

    async def _call_api(self, method: str, **params: Any) -> Any:
        url = self._url_template.format(method=method)
        self.log.debug(f'Telegram API call: method={method} params={params}')
        async with self._session.post(url, json=params) as response:
            response_json = await response.json()
        self.log.debug(f'Telegram API response: {response_json}')
        if not response_json['ok']:
            raise BotAPIClientError(
                error_code=response_json['error_code'],
                description=response_json['description'],
            )
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
