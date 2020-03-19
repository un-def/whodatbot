import argparse
import asyncio
import logging
import os
from typing import Any, Callable, Optional

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
    port: int
    webhook_secret: str
    webhook_base_url: Optional[str]


def parse_args() -> Args:
    parser = argparse.ArgumentParser(prog=__package__)
    parser.register('action', 'store_envvar', StoreEnvVarAction)
    parser.add_argument(
        '--token',
        help='bot API token',
        action='store_envvar',
        envvar='WHODATBOT_API_TOKEN',
        required=True,
    )
    parser.add_argument(
        '--port',
        help='HTTP port',
        action='store_envvar',
        envvar='WHODATBOT_HTTP_PORT',
        type=int,
        required=True,
    )
    parser.add_argument(
        '--webhook-secret',
        help='secret part of webhook URL: https://example.com/<SECRET>',
        action='store_envvar',
        envvar='WHODATBOT_WEBHOOK_SECRET',
        required=True,
        metavar='SECRET',
    )
    parser.add_argument(
        '--webhook-base-url',
        action='store_envvar',
        envvar='WHODATBOT_WEBHOOK_BASE_URL',
        help='webhook base URL (without <SECRET>, e.g., https://example.com/)',
        required=False,
        metavar='URL',
    )
    return parser.parse_args(namespace=Args())


async def main_coro() -> None:
    args = parse_args()
    bot = WhoDatBot(
        token=args.token,
        port=args.port,
        webhook_secret=args.webhook_secret,
        webhook_base_url=args.webhook_base_url,
    )
    try:
        await bot.init()
        await bot.run()
    finally:
        await bot.close()


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main_coro())
