"""Filter subscriptions."""
import asyncio
import copy
import functools
import io
import logging
import os
from typing import Iterable

import aiohttp
import appdirs
import yaml

import clash
import clash.utils.common
import config
import subscription.utils.filterrecorder
import subscription.utils.net
import utils.logging

logger = logging.getLogger(config.APP_NAME).getChild(__name__)


class Subscription:
    """Clash subscription class."""

    CACHE_DIR = os.path.join(appdirs.user_cache_dir(config.APP_NAME), 'subscriptions')

    def __init__(self, name: str, url: str, patterns: Iterable[str]) -> None:
        self._logger = utils.logging.IDAdapter(logger, {'id': name})
        self.name = name
        self._url = url
        self._patterns = patterns
        self.__raw_content: str
        self.collection: subscription.utils.filterrecorder.FilterRecorderCollection

    @property
    def _raw_content(self) -> str:
        return self.__raw_content

    @_raw_content.setter
    def _raw_content(self, value: str) -> None:
        try:
            os.makedirs(self.CACHE_DIR, exist_ok=True)
            path = os.path.join(self.CACHE_DIR, f'{self.name}.yaml')
            try:
                with open(path, 'w', encoding='utf-8') as fs:
                    fs.write(value)
            except OSError:
                self._logger.warning("Failed to write subscription cache file %s", path)
        except OSError:
            self._logger.warning(
                "Failed to create subscription cache directory %s", self.CACHE_DIR
            )
        self.__raw_content = value

    async def fetch(self, timeout=10):
        """Fetch subscription raw content."""
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(
            timeout=client_timeout, trust_env=True
        ) as session:
            self._logger.info("Fetching subscription")
            async with session.get(self._url, allow_redirects=False, ssl=False) as resp:
                self._raw_content = await resp.text(encoding='utf-8')
                return self._raw_content

    @functools.cached_property
    def content(self) -> dict:
        """Get subscription parsed content."""
        if not self._raw_content:
            raise ValueError("Subscription content not fetched")
        return yaml.safe_load(io.StringIO(self._raw_content))

    def _name_filter(self, proxies: list[dict]):
        """Filter proxies by name."""
        names: list[str] = [proxy['name'] for proxy in proxies]
        recorder = subscription.utils.filterrecorder.ProxyNameFilterRecorder()
        recorder.source = copy.copy(proxies)
        if not self._patterns:
            recorder.accepted = recorder.source
        else:
            for name, proxy in zip(names, proxies):
                rejected = False
                for pattern in self._patterns:
                    if pattern in name:
                        recorder.rejected[pattern].append(proxy)
                        rejected = True
                        break
                if not rejected:
                    recorder.accepted.append(proxy)
        self._logger.info(
            '%d / %d proxies accepted after name filter', len(recorder), len(proxies)
        )
        return recorder

    async def _ingress_filter(self, proxies: list[dict]):
        """Filter proxies by ingress records."""
        recorder = subscription.utils.filterrecorder.ProxyIngressFilterRecorder()
        recorder.source = copy.copy(proxies)
        servers: list[str] = [proxy['server'] for proxy in proxies]
        ip_list = await asyncio.gather(
            *[subscription.utils.net.convert_server_to_ip(server) for server in servers]
        )
        for proxy, ip in zip(proxies, ip_list):
            port = proxy['port']
            key = f'{ip}:{port}'
            if ip == '':
                recorder.rejected[''].append(proxy)
            elif key in recorder.accepted.keys():
                recorder.rejected[key].append(proxy)
            else:
                recorder.accepted[key] = proxy
        for key in recorder.rejected.keys():
            # The first proxy in the rejected list is the accepted one
            recorder.rejected[key].insert(0, recorder.accepted[key])
        self._logger.info(
            '%d / %d proxies accepted after ingress filter', len(recorder), len(proxies)
        )
        return recorder

    async def _connectivity_filter(
        self, clash_instance: clash.Clash, proxies: list[dict]
    ):
        """Filter proxies by connectivity."""
        assert clash_instance.poll() is None, "Clash instance not started"
        recorder = subscription.utils.filterrecorder.ConnectivityFilterRecorder()
        recorder.source = copy.copy(proxies)
        names = [proxy['name'] for proxy in proxies]
        resps = await asyncio.gather(*[clash_instance.ping(name) for name in names])
        self._logger.debug('Connectivity responses: \n%s', '\n'.join(map(str, resps)))
        for proxy, resp in zip(proxies, resps):
            if 'delay' in resp:
                recorder.accepted.append(proxy)
            else:
                recorder.rejected.append(proxy)
        self._logger.info(
            '%d / %d proxies accepted after connectivity filter',
            len(recorder),
            len(names),
        )
        return recorder

    async def _egress_filter(self, clash_instance: clash.Clash, proxies: list[dict]):
        """Filter proxies by egress."""
        assert clash_instance.poll() is None, "Clash instance not started"
        self._logger.info('Filtering proxies by egress')
        recorder = subscription.utils.filterrecorder.EgressFilterRecorder()
        recorder.source = copy.copy(proxies)
        names = [proxy['name'] for proxy in proxies]
        ip_list = []
        for i, name in enumerate(names):
            self._logger.info(
                'egress ip lookup for %s, progress %d / %d, ', name, i + 1, len(names)
            )
            if not await clash_instance.switch('GLOBAL', name):
                ip_list.append('')
                continue
            http_proxy = f'http://127.0.0.1:{clash_instance.port}'
            ip = await subscription.utils.net.get_egress_ip(http_proxy)
            ip_list.append(ip)

        # Similar process to ns_filter
        for proxy, ip in zip(proxies, ip_list):
            if ip == '':
                recorder.rejected[''].append(proxy)
            elif ip in recorder.accepted.keys():
                recorder.rejected[ip].append(proxy)
            else:
                recorder.accepted[ip] = proxy
        for ip in recorder.rejected.keys():
            recorder.rejected[ip].insert(0, recorder.accepted[ip])

        self._logger.info(
            '%d / %d proxies accepted after egress filter', len(recorder), len(names)
        )
        return recorder

    async def filter(self, port: int, controller_port: int):
        """Filter proxies."""

        proxies = self.content['proxies']
        conf = clash.utils.common.build_simple_config(port, controller_port, proxies)
        clash_instance = clash.Clash(conf, self.name)
        clash_instance.start()
        proxies = self.content['proxies']
        recorder_name = self._name_filter(proxies)
        recorder_ingress = await self._ingress_filter(recorder_name.accepted)
        recorder_connectivity = await self._connectivity_filter(
            clash_instance, list(recorder_ingress.accepted.values())
        )
        recorder_egress = await self._egress_filter(
            clash_instance, recorder_connectivity.accepted
        )
        del clash_instance
        collection = subscription.utils.filterrecorder.FilterRecorderCollection(
            recorder_name, recorder_ingress, recorder_connectivity, recorder_egress
        )
        self.collection = collection
        return collection


def parse_subscription_config(path: str) -> list[Subscription]:
    """Parse subscription config from file."""
    with open(path, 'r', encoding='utf-8') as fs:
        sub_confs = yaml.safe_load(fs)
    subscriptions = []
    for sub_conf in sub_confs:
        subscriptions.append(
            Subscription(
                sub_conf['name'], sub_conf['url'], sub_conf.get('patterns', [])
            )
        )
    return subscriptions
