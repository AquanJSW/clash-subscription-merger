#!/usr/bin/env python3
import argparse
import asyncio
import os

import yaml

import clash.utils.common
import config
import utils.logging
import utils.net
from subscription.subscription import parse_subscription_config
from template.template import Template


class Args(argparse.Namespace):
    subscription: str
    templates: list[str]
    outputs: list[str]
    verbose: bool
    proxy: str
    # cache: bool


def parse_args():
    parser = argparse.ArgumentParser()
    # fmt: off
    parser.add_argument('-s', '--subscription', help='subscription config file', required=True)
    parser.add_argument('-t', '--templates', help='template files', nargs='+', required=True)
    parser.add_argument('-o', '--outputs', help='output files / directory, same name as templates if directory is provided', nargs='+', required=True)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--proxy', default=os.environ.get('HTTPS_PROXY', ''), help='used to download subscriptions')

    # dev_options = parser.add_argument_group('dev options')
    # dev_options.add_argument('--cache', help='using cached subscriptions instead of re-downloading to speed up test', action='store_true')
    # fmt: on
    args = parser.parse_args(namespace=Args())
    return args


async def main():
    args = parse_args()

    logger = utils.logging.init_logger(
        config.APP_NAME, level='DEBUG' if args.verbose else 'INFO'
    )

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


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
