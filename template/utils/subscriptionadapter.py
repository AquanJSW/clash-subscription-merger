import dataclasses
import json
import logging
import re

import maxminddb

import config
import utils.logging
from subscription.subscription import Subscription

logger = logging.getLogger(config.APP_NAME).getChild(__name__)


@dataclasses.dataclass
class _ProxyClass:
    proxy: dict
    ip: str
    region: str


class SubscriptionAdapter:
    def __init__(self, subscription: Subscription, reader: maxminddb.Reader) -> None:
        self._logger = utils.logging.IDAdapter(logger, {'id': subscription.name})
        self._proxy_insts: list[_ProxyClass] = []
        for ip, proxy in subscription.collection.egress.accepted.items():
            try:
                region = reader.get(ip)['country']['iso_code']
            except KeyError:
                self._logger.warning('Failed to get region for %s', ip)
                region = ''
            self._proxy_insts.append(_ProxyClass(proxy, ip, region))

        self._logger.debug(str(self))

    def __str__(self):
        d = []
        for prxoy_inst in self._proxy_insts:
            d.append(
                {
                    'ip': prxoy_inst.ip,
                    'region': prxoy_inst.region,
                    'name': prxoy_inst.proxy['name'],
                    'server': prxoy_inst.proxy['server'],
                }
            )
        return json.dumps(d, indent=4, ensure_ascii=False)

    @property
    def proxies(self):
        return [proxy_inst.proxy for proxy_inst in self._proxy_insts]

    def __getitem__(self, key: str):
        key = key.upper()
        if key == 'ALL':
            return self.proxies
        if not key.startswith(('+', '-')):
            key = '+' + key
        match = re.match(r'^([+-])[A-Z]{2}(\1[A-Z]{2})*', key)
        assert match and len(match.group(0)) == len(
            key
        ), 'key should be like "US", "+US", "-US", "-US-AU", "+US+AU"...'

        sign = key[0]
        positive = sign == '+'
        regions = set(key[1:].split(sign))
        if positive:
            proxy_insts = filter(lambda x: x.region in regions, self._proxy_insts)
        else:
            proxy_insts = filter(lambda x: x.region not in regions, self._proxy_insts)
        return [proxy_inst.proxy for proxy_inst in proxy_insts]
