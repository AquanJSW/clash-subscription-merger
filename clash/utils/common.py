import gzip
import io
import logging
import os
import platform
import stat
import zipfile

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
    timeout=10,
):
    """Download clash binary."""
    # fmt: off
    URLS = {
        ('Windows', 'AMD64'):   'https://github.com/AquanJSW/clashpremium-core-binaries/raw/main/clashpremium-windows-amd64.exe',
        ('Linux',   'x86_64'):  'https://github.com/AquanJSW/clashpremium-core-binaries/raw/main/clashpremium-linux-amd64',
        ('Linux',   'aarch64'): 'https://github.com/AquanJSW/clashpremium-core-binaries/raw/main/clashpremium-linux-armv8'
    }
    # fmt: on
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    logger.info('downloading clash binary')
    query = (platform.system(), platform.machine())
    assert query in URLS, f'unsupported platform: {query}'
    raw = requests.get(URLS[query], timeout=timeout, allow_redirects=True).content
    with open(filepath, 'wb') as fs:
        fs.write(raw)
    # chmod +x
    os.chmod(filepath, os.stat(filepath).st_mode | stat.S_IEXEC)


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
