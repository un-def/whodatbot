import asyncio
import logging
from http import HTTPStatus
from urllib.parse import urljoin

import aiohttp
from aiohttp import web


class WhoDatBot:

    BASE_API_URL_TEMPLATE = 'https://api.telegram.org/bot{token}'

    log = logging.getLogger(__name__)

    def __init__(self, *, token, port, secret):
        self.base_api_url = self.BASE_API_URL_TEMPLATE.format(token=token)
        self.port = port
        self.secret = secret

    async def handler(self, request):
        # Obscure (hah) any error with 403 FORBIDDEN
        error_status = HTTPStatus.FORBIDDEN
        if request.method != 'POST' or request.path.strip('/') != self.secret:
            return web.Response(status=error_status)
        try:
            self.log.debug(await request.json())
        except ValueError:
            return web.Response(status=error_status)
        return web.Response(status=HTTPStatus.NO_CONTENT)

    async def serve(self):
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

    def set_webhook(self, base_url):
        url = urljoin(base_url, self.secret)
        return self._call_api('setWebhook', url=url)

    async def _call_api(self, method, **params):
        url = f'{self.base_api_url}/{method}'
        self.log.debug(f'Telegram API call: method={method} params={params}')
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=params) as response:
                response_json = await response.json()
        self.log.debug(f'Telegram API response: {response_json}')
        return response_json
