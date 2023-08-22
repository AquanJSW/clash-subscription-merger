import copy
import logging
import os

import maxminddb
import yaml

import config
import utils.logging
from subscription.subscription import Subscription
from template.utils.subscriptionadapter import SubscriptionAdapter

logger = logging.getLogger(config.APP_NAME).getChild(__name__)


class Template:
    def __init__(self, path: str):
        self.path = path
        self.id = os.path.basename(path).split('.')[0]
        self._logger = utils.logging.IDAdapter(logger, {'id': self.id})

    def fit(self, subscriptions_: list[Subscription], maximind_db_path: str) -> dict:
        """Fit subscriptions into template."""
        reader = maxminddb.open_database(maximind_db_path)
        subscriptions = dict(
            (subscription.name, SubscriptionAdapter(subscription, reader))
            for subscription in subscriptions_
        )
        with open(self.path, 'r', encoding='utf-8') as fs:
            conf = yaml.safe_load(fs)

        if 'proxies' not in conf:
            conf['proxies'] = []
        for subscription in subscriptions.values():
            conf['proxies'].extend(subscription.proxies)

        for group in conf['proxy-groups']:
            if 'region' in group:
                region = group['region']
                del group['region']
            else:
                region = 'ALL'
            if 'proxies' not in group:
                group['proxies'] = []
            if 'subscriptions' in group:
                for name in group['subscriptions']:
                    if name not in subscriptions:
                        self._logger.warning(
                            'Subscription %s not found for group %s',
                            name,
                            group['name'],
                        )
                        continue
                    proxies = subscriptions[name][region]
                    group['proxies'].extend([proxy['name'] for proxy in proxies])
                del group['subscriptions']

        return self.clean(conf)

    @staticmethod
    def clean(conf_: dict):
        """Clean config."""

        def is_valid_group(group):
            '''Simple validation, not comprehensive.'''
            if 'use' in group or 'proxies' in group:
                return True

        def clean_groups(conf: dict, last: None | dict = None):
            if last == conf:
                return conf
            last = copy.deepcopy(conf)
            proxies = conf['proxies']
            proxy_names = [proxy['name'] for proxy in proxies] + [
                'DIRECT',
                'REJECT',
            ]

            # delete empty groups
            conf['proxy-groups'] = list(filter(is_valid_group, conf['proxy-groups']))

            group_names = [group['name'] for group in conf['proxy-groups']]
            proxy_names.extend(group_names)

            # delete invalid proxies for each group
            for group in conf['proxy-groups']:
                if 'proxies' in group:
                    group['proxies'] = list(
                        filter(lambda x: x in proxy_names, group['proxies'])
                    )

            # delete invalid keys for each group
            for group in conf['proxy-groups']:
                if 'use' in group and group['use'] == []:
                    del group['use']
                if 'proxies' in group and group['proxies'] == []:
                    del group['proxies']
            return clean_groups(conf, last)

        conf = clean_groups(conf_)

        # clean rules
        group_names = [group['name'] for group in conf['proxy-groups']]
        group_names.extend(['DIRECT', 'REJECT'])

        def is_valid_rule(rule: str):
            group = rule.split(',')[-1]
            return group in group_names

        conf['rules'] = list(filter(is_valid_rule, conf['rules']))

        return clean_groups(conf_)
