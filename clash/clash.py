import json
import asyncio
import logging
import os
import shutil
import subprocess
from urllib.parse import urljoin

import aiohttp
import appdirs
import yaml

import config
import utils.logging

logger = logging.getLogger(config.APP_NAME).getChild(__name__)


class Clash:
    CONFIG_DIR = os.path.join(appdirs.user_data_dir(config.APP_NAME), 'clash')
    BIN_PATH = os.path.join(CONFIG_DIR, 'clash')
    MAXMIND_DB_PATH = os.path.join(CONFIG_DIR, 'Country.mmdb')

    def __init__(self, config: dict, id_: str) -> None:
        self.id = id_
        self.config = config
        self._process: subprocess.Popen
        self._logger = utils.logging.IDAdapter(logger, {'id': self.id})

    def start(self):
        """Start clash."""
        self._logger.info('Starting clash')
        config_dir = os.path.join(appdirs.user_cache_dir(config.APP_NAME), self.id)
        shutil.rmtree(config_dir, ignore_errors=True)
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, 'config.yaml')
        os.link(self.MAXMIND_DB_PATH, os.path.join(config_dir, 'Country.mmdb'))
        with open(config_path, 'w', encoding='utf-8') as fs:
            yaml.safe_dump(self.config, fs, allow_unicode=True)
        self._process = subprocess.Popen([self.BIN_PATH, '-d', config_dir])
        self._logger.debug(
            'Clash started, pid=%d port=%d controller=%s working_dir=%s',
            self._process.pid,
            self.port,
            self.external_controller,
            config_dir,
        )

    def poll(self):
        """Poll clash."""
        return self._process.poll()

    @property
    def external_controller(self):
        return f'http://{self.config["external-controller"]}'

    async def ping(
        self, name: str, timeout=2000, url='http://www.gstatic.com/generate_204'
    ):
        """Ping a proxy.

        Return
        ---
        parsed json data
        """
        restful_url = urljoin(
            self.external_controller, f'proxies/{name}/delay?{timeout=}&url={url}'
        )
        client_timeout = aiohttp.ClientTimeout(total=max(timeout / 1000 + 1, 5))
        async with aiohttp.ClientSession(timeout=client_timeout) as session:
            try:
                async with session.get(restful_url) as resp:
                    self._logger.debug('Start  ping %s', name)
                    ret = await resp.json()
                    self._logger.debug('Finish ping %s', name)
                    return ret
            except asyncio.TimeoutError:
                self._logger.warning('Failed to ping %s', name)
                return {'message': 'timeout'}

    def __del__(self):
        self._process.terminate()

    async def switch(self, group: str, name: str):
        """Switch to a proxy."""
        restful_url = urljoin(self.external_controller, f'proxies/{group}')
        payload = {'name': name}
        async with aiohttp.ClientSession() as session:
            async with session.put(restful_url, data=json.dumps(payload)) as resp:
                if resp.status != 204:
                    self._logger.warning(
                        'Failed to switch to proxy %s, code: %d, text: %s',
                        name,
                        resp.status,
                        await resp.json(),
                    )
                    return False
                return True

    @property
    def port(self) -> int:
        return self.config['mixed-port']
