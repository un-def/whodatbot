import asyncio
import logging
from http import HTTPStatus
from typing import Any, Awaitable, Optional, cast
from urllib.parse import urljoin

import aiohttp
from aiohttp import web
from aiohttp.web import BaseRequest, Response


class WhoDatBot:

    BASE_API_URL_TEMPLATE = 'https://api.telegram.org/bot{token}'

    log = logging.getLogger(__name__)

    def __init__(
        self, *, token: str, port: int,
        webhook_secret: str, webhook_base_url: Optional[str] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        self._base_api_url = self.BASE_API_URL_TEMPLATE.format(token=token)
        self._port = port
        self._secret = webhook_secret.strip('/')
        self._webhook_url: Optional[str]
        if webhook_base_url is not None:
            self._webhook_url = urljoin(webhook_base_url, self._secret)
        else:
            self._webhook_url = None

    async def init(self) -> None:
        self._session = aiohttp.ClientSession(loop=self._loop)
        self._username = await self.get_username()
        if self._webhook_url:
            await self.set_webhook(self._webhook_url)

    async def close(self) -> None:
        await self._session.close()

    async def handler(self, request: BaseRequest) -> Response:
        # Obscure (hah) any error with 403 FORBIDDEN
        error_status = HTTPStatus.FORBIDDEN
        if request.method != 'POST' or request.path.strip('/') != self._secret:
            return Response(status=error_status)
        try:
            self.log.debug(await request.json())
        except ValueError:
            return Response(status=error_status)
        return Response(status=HTTPStatus.NO_CONTENT)

    async def serve(self) -> None:
        server = web.Server(self.handler)
        runner = web.ServerRunner(server, handle_signals=True)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self._port)
        try:
            await site.start()
            while True:
                await asyncio.sleep(3600)
        finally:
            await runner.cleanup()

    def set_webhook(self, url: str) -> Awaitable[Any]:
        return self._call_api('setWebhook', url=url)

    async def get_username(self) -> str:
        response = await self._call_api('getMe')
        username = cast(str, response['result']['username'])
        self.log.debug('Bot username: %s', username)
        return username

    async def _call_api(self, method: str, **params: Any) -> Any:
        url = f'{self._base_api_url}/{method}'
        self.log.debug(f'Telegram API call: method={method} params={params}')
        async with self._session.post(url, json=params) as response:
            response_json = await response.json()
        self.log.debug(f'Telegram API response: {response_json}')
        return response_json
