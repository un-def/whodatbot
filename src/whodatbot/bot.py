import asyncio
import logging

import aiohttp
from aiohttp import web


class WhoDatBot:

    BASE_API_URL_TEMPLATE = 'https://api.telegram.org/bot{token}'

    log = logging.getLogger(__name__)

    def __init__(self, *, token, port):
        self.base_api_url = self.BASE_API_URL_TEMPLATE.format(token=token)
        self.port = port

    async def handler(self, request):
        if request.method != 'POST':
            return web.Response(status=405)
        try:
            self.log.debug(await request.json())
        except ValueError:
            return web.Response(status=400)
        return web.Response(status=204)

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

    def set_webhook(self, url):
        return self._call_api('setWebhook', url=url)

    async def _call_api(self, method, **params):
        url = f'{self.base_api_url}/{method}'
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=params) as response:
                return await response.json()
