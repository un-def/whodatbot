import argparse
import asyncio
import logging
import os

from .bot import WhoDatBot


def prepare_argparser():
    api_token_from_env = os.environ.get('WHODATBOT_API_TOKEN')
    http_port_from_env = os.environ.get('WHODATBOT_HTTP_PORT')
    parser = argparse.ArgumentParser(prog=__package__)
    parser.add_argument(
        '--token',
        help='bot API token',
        required=api_token_from_env is None,
        default=api_token_from_env,
    )
    parser.add_argument(
        '--port',
        help='HTTP port',
        type=int,
        required=http_port_from_env is None,
        default=http_port_from_env,
    )
    parser.add_argument(
        '--set-webhook',
        help='set webhook URL',
        required=False,
    )
    return parser


async def main():
    argparser = prepare_argparser()
    args = argparser.parse_args()
    bot = WhoDatBot(token=args.token, port=args.port)
    if args.set_webhook:
        await bot.set_webhook(args.set_webhook)
    await bot.serve()


logging.basicConfig(level=logging.DEBUG)
asyncio.run(main())
