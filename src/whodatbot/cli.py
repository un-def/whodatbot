import argparse
import asyncio
import logging
import os

from .bot import WhoDatBot


def _noop_setter(instance, value):
    pass


def careless_property(func):
    return property(func, _noop_setter)


class StoreEnvVarAction(argparse._StoreAction):

    def __init__(self, *, envvar, default=None, required=False, **kwargs):
        super().__init__(**kwargs)
        self.__envvar = envvar
        self.__default = default
        self.__required = required

    @careless_property
    def default(self):
        return os.environ.get(self.__envvar, self.__default)

    @careless_property
    def required(self):
        if not self.__required:
            return False
        if self.__envvar in os.environ:
            return False
        return True


def parse_args():
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
        '--secret',
        help='secret part of webhook URL: https://example.com/<SECRET>',
        action='store_envvar',
        envvar='WHODATBOT_WEBHOOK_SECRET',
        required=True,
    )
    parser.add_argument(
        '--set-webhook',
        help='set webhook URL (without <SECRET>, e.g., https://example.com/)',
        required=False,
        metavar='URL',
    )
    return parser.parse_args()


async def main_coro():
    args = parse_args()
    bot = WhoDatBot(token=args.token, port=args.port, secret=args.secret)
    if args.set_webhook:
        await bot.set_webhook(args.set_webhook)
    await bot.serve()


def main():
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main_coro())
