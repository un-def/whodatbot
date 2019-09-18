import asyncio
import logging
from http import HTTPStatus
from typing import Any
from urllib.parse import urljoin

import aiohttp
from aiohttp import web
from aiohttp.web import BaseRequest, Response


class WhoDatBot:

    BASE_API_URL_TEMPLATE = 'https://api.telegram.org/bot{token}'

    log = logging.getLogger(__name__)

    def __init__(self, *, token: str, port: int, secret: str) -> None:
        self.base_api_url = self.BASE_API_URL_TEMPLATE.format(token=token)
        self.port = port
        self.secret = secret

    async def handler(self, request: BaseRequest) -> Response:
        # Obscure (hah) any error with 403 FORBIDDEN
        error_status = HTTPStatus.FORBIDDEN
        if request.method != 'POST' or request.path.strip('/') != self.secret:
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
        site = web.TCPSite(runner, 'localhost', self.port)
        try:
            await site.start()
            while True:
                await asyncio.sleep(3600)
        finally:
            await runner.cleanup()

    def set_webhook(self, base_url: str) -> Any:
        url = urljoin(base_url, self.secret)
        return self._call_api('setWebhook', url=url)

    async def _call_api(self, method: str, **params: Any) -> Any:
        url = f'{self.base_api_url}/{method}'
        self.log.debug(f'Telegram API call: method={method} params={params}')
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=params) as response:
                response_json = await response.json()
        self.log.debug(f'Telegram API response: {response_json}')
        return response_json
