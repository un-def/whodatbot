import asyncio
from http import HTTPStatus
from typing import Dict, Optional, Type
from urllib.parse import urlparse

from aiohttp import web
from aiohttp.web import BaseRequest, Response

from .client import BotAPIClient
from .types import Message, Update, UpdateID
from .utils import LoggerDescriptor, TemplateFormatter, extract_users


class WebhookURLFormatter(TemplateFormatter):

    required_fields = ('secret',)
    optional_fields = ('port',)


class UpdateProcessor:

    update_type: str
    update_types: Dict[str, Type['UpdateProcessor']] = {}

    log = LoggerDescriptor()

    def __init__(self, update: Update):
        self.update_id: UpdateID = update['update_id']
        self.update_body = update[self.update_type]

    def __init_subclass__(cls, update_type: str) -> None:
        if update_type in cls.update_types:
            raise RuntimeError(f'already registered: {update_type}')
        super().__init_subclass__()
        cls.update_type = update_type
        cls.update_types[update_type] = cls

    @classmethod
    def dispatch(cls, update: Update) -> 'UpdateProcessor':
        cls.log.info('dispatching update: %s', update)
        keys = list(update.keys())
        if 'update_id' not in keys:
            raise ValueError(f'update_id not found: {keys}')
        keys.remove('update_id')
        if len(keys) != 1:
            raise ValueError(f'invalid update: {keys}')
        update_type = keys[0]
        if update_type not in cls.update_types:
            raise KeyError(f'unsupported update type: {update_type}')
        processor = cls.update_types[update_type]
        return processor(update)

    def __call__(self) -> None:
        raise NotImplementedError


class MessageProcessor(UpdateProcessor, update_type='message'):

    def __call__(self) -> None:
        message: Message = self.update_body
        for user in extract_users(message):
            self.log.info(user)


class UpdateDispatcher:

    processor_class = UpdateProcessor

    log = LoggerDescriptor()

    def __init__(self) -> None:
        self.queue: asyncio.Queue[Optional[Update]] = asyncio.Queue()
        self._running = False

    async def run(self) -> None:
        if self._running:
            return
        self.log.info('starting dispatcher')
        self._running = True
        try:
            await self._run()
        finally:
            self.log.info('stopping dispatcher')
            self._running = False

    async def _run(self) -> None:
        while True:
            update = await self.queue.get()
            if update is None:
                break
            try:
                processor = self.processor_class.dispatch(update)
                processor()
            except Exception:
                self.log.exception('')


class WhoDatBot:

    dispatcher_class = UpdateDispatcher

    log = LoggerDescriptor()

    def __init__(
        self, *,
        token: str,
        webhook_url_template: str,
        webhook_secret: str,
        webhook_port: int,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        self._token = token
        url_formatter = WebhookURLFormatter(webhook_url_template)
        self._webhook_url = webhook_url = url_formatter(
            port=webhook_port, secret=webhook_secret)
        self._secret_path = urlparse(webhook_url).path
        self._port = webhook_port
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        self._dispatcher = self.dispatcher_class()

    async def init(self) -> None:
        self._client = BotAPIClient(token=self._token, loop=self._loop)
        self._username = await self._client.get_username()
        await self._client.set_webhook(self._webhook_url)
        self._dispatcher_task = asyncio.create_task(self._dispatcher.run())

    async def close(self) -> None:
        await self._client.close()

    async def handler(self, request: BaseRequest) -> Response:
        dispatcher_queue = self._dispatcher.queue
        # Obscure (hah) any error with 403 FORBIDDEN
        error_status = HTTPStatus.FORBIDDEN
        if request.method != 'POST' or request.path != self._secret_path:
            return Response(status=error_status)
        try:
            update: Update = await request.json()
        except ValueError:
            return Response(status=error_status)
        dispatcher_queue.put_nowait(update)
        return Response(status=HTTPStatus.NO_CONTENT)

    async def run(self) -> None:
        server = web.Server(self.handler)
        runner = web.ServerRunner(server, handle_signals=True)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self._port)
        try:
            await site.start()
            while True:
                await asyncio.sleep(3600)
            await self._dispatcher.queue.put(None)
        finally:
            await runner.cleanup()
            current_task = asyncio.current_task()
            tasks = [t for t in asyncio.all_tasks() if t is not current_task]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
