#!/usr/bin/env python3
import argparse
import asyncio
import logging
import os
import sys
from unittest.mock import Mock

import yaml

import clash.utils.common
import config
import utils.logging
import utils.net
from subscription.subscription import parse_subscription_config
from template.template import Template
from utils.telegrambot import TelegramBot

logger: logging.Logger


class Args(argparse.Namespace):
    subscription: str
    templates: list[str]
    outputs: list[str]
    verbose: bool
    proxy: str
    # cache: bool

    api_key: str
    chat_id: str


def parse_args():
    parser = argparse.ArgumentParser()
    # fmt: off
    parser.add_argument('-s', '--subscription', help='subscription config file', required=True)
    parser.add_argument('-t', '--templates', help='template files', nargs='+', required=True)
    parser.add_argument('-o', '--outputs', help='output files / directory, same name as templates if directory is provided', nargs='+', required=True)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--proxy', default=os.environ.get('HTTPS_PROXY', ''), help='used to download subscriptions')

    bot_options = parser.add_argument_group('bot options')
    bot_options.add_argument('--api-key', help='telegram bot api key')
    bot_options.add_argument('--chat-id', help='telegram chat id')

    # dev_options = parser.add_argument_group('dev options')
    # dev_options.add_argument('--cache', help='using cached subscriptions instead of re-downloading to speed up test', action='store_true')
    # fmt: on
    args = parser.parse_args(namespace=Args())
    return args


async def _main(args: Args):
    if args.proxy:
        os.environ['https_proxy'] = args.proxy
        os.environ['http_proxy'] = args.proxy
        os.environ['HTTPS_PROXY'] = args.proxy
        os.environ['HTTP_PROXY'] = args.proxy
    if os.environ.get('HTTPS_PROXY', ''):
        logger.info('Using proxy %s', os.environ['HTTPS_PROXY'])

    subscriptions = parse_subscription_config(args.subscription)
    fetch_coros = [subscription.fetch(15) for subscription in subscriptions]
    try:
        await asyncio.gather(*fetch_coros)
    except asyncio.TimeoutError:
        logger.exception('Failed to fetch subscriptions')
        return

    if os.path.exists(clash.Clash.BIN_PATH):
        logger.info('Using cached clash binary')
        logger.debug(clash.Clash.BIN_PATH)
    else:
        clash.utils.common.download_clash_bin(clash.Clash.BIN_PATH)

    if os.path.exists(clash.Clash.MAXMIND_DB_PATH):
        logger.info('Using cached maxmind db')
        logger.debug(clash.Clash.MAXMIND_DB_PATH)
    else:
        clash.utils.common.download_maxmind_db(clash.Clash.MAXMIND_DB_PATH)

    picker = utils.net.get_tcp_port_picker()
    filter_coros = [
        subscription.filter(next(picker), next(picker))
        for subscription in subscriptions
    ]
    await asyncio.gather(*filter_coros)

    templates = [Template(path) for path in args.templates]
    for template in templates:
        conf = template.fit(subscriptions, clash.Clash.MAXMIND_DB_PATH)
        if os.path.isdir(args.outputs[0]):
            output_path = os.path.join(args.outputs[0], f'{template.id}.yaml')
        else:
            output_path = args.outputs[0]
        with open(output_path, 'w', encoding='utf-8') as fs:
            yaml.safe_dump(conf, fs, allow_unicode=True)
        logger.info('Wrote %s', output_path)


def main(args: Args):
    global logger

    logger = utils.logging.init_logger(
        config.APP_NAME, level='DEBUG' if args.verbose else 'INFO'
    )
    if args.api_key and args.chat_id:
        logger.info('Telegram bot is enabled')
        bot = TelegramBot(args.api_key, args.chat_id)
    else:
        logger.info('Telegram bot is disabled')
        bot = Mock()

    try:
        asyncio.run(_main(args))
        bot.send_message('Finish merging Clash subscriptions.')
    except KeyboardInterrupt:
        pass
    except:
        logger.exception('Failed to merge Clash subscriptions')
        bot.send_message(f'Failed to merge Clash subscriptions\n{sys.exc_info()}')


if __name__ == '__main__':
    main(parse_args())
