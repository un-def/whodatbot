import argparse
import asyncio
import logging
import os
from typing import Any, Callable

from .bot import WhoDatBot


def _noop_setter(instance: Any, value: Any) -> None:
    pass


def careless_property(func: Callable[[Any], Any]) -> property:
    return property(func, _noop_setter)


class StoreEnvVarAction(argparse._StoreAction):

    def __init__(
        self, *, envvar: str, default: Any = None, required: bool = False,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.__envvar = envvar
        self.__default = default
        self.__required = required

    @careless_property
    def default(self) -> Any:
        return os.environ.get(self.__envvar, self.__default)

    # see https://github.com/python/mypy/issues/4125
    @careless_property
    def required(self) -> bool:   # type: ignore
        if not self.__required:
            return False
        if self.__envvar in os.environ:
            return False
        return True


class Args:

    token: str
    webhook_url_template: str
    webhook_secret: str
    webhook_port: int


def parse_args() -> Args:
    parser = argparse.ArgumentParser(prog=__package__)
    parser.register('action', 'store_envvar', StoreEnvVarAction)
    parser.add_argument(
        '--token',
        required=True,
        action='store_envvar',
        envvar='WHODATBOT_API_TOKEN',
        metavar='TOKEN',
        help='bot API token',
    )
    parser.add_argument(
        '--webhook-url-template',
        required=True,
        action='store_envvar',
        envvar='WHODATBOT_WEBHOOK_URL_TEMPLATE',
        metavar='URL_TEMPLATE',
        help=(
            'URL template with required {secret} and optional {port} '
            'placeholders, e.g., https://example.com/webhook/{secret}/path'
        ),
    )
    parser.add_argument(
        '--webhook-secret',
        required=True,
        action='store_envvar',
        envvar='WHODATBOT_WEBHOOK_SECRET',
        metavar='SECRET',
        help='secret part of webhook URL',
    )
    parser.add_argument(
        '--webhook-port',
        required=True,
        action='store_envvar',
        type=int,
        envvar='WHODATBOT_WEBHOOK_PORT',
        metavar='PORT',
        help='webhook HTTP port',
    )
    return parser.parse_args(namespace=Args())


async def main_coro() -> None:
    args = parse_args()
    bot = WhoDatBot(
        token=args.token,
        webhook_url_template=args.webhook_url_template,
        webhook_secret=args.webhook_secret,
        webhook_port=args.webhook_port,
    )
    try:
        await bot.init()
        await bot.run()
    finally:
        await bot.close()


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main_coro())
