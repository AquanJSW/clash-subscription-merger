import gzip
import logging
import os

import requests

import config

logger = logging.getLogger(config.APP_NAME).getChild(__name__)


def build_simple_config(port, controller_port, proxies: list[dict]):
    """Build simple clash config."""
    return {
        'mixed-port': port,
        'ipv6': True,
        'proxies': proxies,
        'mode': 'global',
        'log-level': 'warning',
        'external-controller': f'127.0.0.1:{controller_port}',
    }


def download_clash_bin(
    filepath,
    url='https://github.com/Dreamacro/clash/releases/download/premium/clash-linux-amd64-2023.08.17.gz',
    timeout=10,
):
    """Download clash binary."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    logger.info('downloading clash binary')
    raw = gzip.decompress(requests.get(url, timeout=timeout).content)
    with open(filepath, 'wb') as fs:
        fs.write(raw)
    os.chmod(filepath, 0o755)


def download_maxmind_db(
    filepath,
    url='https://github.com/Dreamacro/maxmind-geoip/releases/download/20230812/Country.mmdb',
    timeout=10,
):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    logger.info('downloading maxmind db')
    raw = requests.get(url, timeout=timeout).content
    with open(filepath, 'wb') as fs:
        fs.write(raw)
