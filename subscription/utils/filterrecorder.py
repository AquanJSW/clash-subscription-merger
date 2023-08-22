"""Record the filtering process.

NOTE: The subclasses should be used in sequence.
"""
import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Collection, List, MutableMapping, Sequence


@dataclass
class FilterRecorder:
    """A base class used to record filtering."""

    rejected: object
    accepted: Collection
    source: Sequence

    def __len__(self):
        return len(self.accepted)

    def __iter__(self):
        return iter(self.accepted)


@dataclass
class ProxyNameFilterRecorder(FilterRecorder):
    '''Record the 'filter by proxy name' operation.'''

    rejected: MutableMapping[str, List[dict]] = field(
        default_factory=lambda: defaultdict(list)
    )
    '''key: pattern, value: list of proxies'''
    accepted: List[dict] = field(default_factory=list)
    '''list of proxies'''
    source: List[dict] = field(default_factory=list)
    '''list of proxies'''


@dataclass
class ProxyIngressFilterRecorder(FilterRecorder):
    '''Record the 'filter by ns records' operation.'''

    rejected: MutableMapping[str, list] = field(
        default_factory=lambda: defaultdict(list)
    )
    '''key: IP, value: list of proxies'''
    accepted: MutableMapping[str, dict] = field(
        default_factory=lambda: defaultdict(dict)
    )
    '''key: IP, value: proxy'''
    source: List[dict] = field(default_factory=list)
    '''list of proxies'''

    def __str__(self):
        compact = defaultdict(list)
        for ip, proxies in self.rejected.items():
            for proxy in proxies:
                compact[ip].append({'name': proxy['name'], 'server': proxy['server']})
        return json.dumps(compact, indent=4, ensure_ascii=False)


@dataclass
class ConnectivityFilterRecorder(FilterRecorder):
    '''Record the 'filter by clash ping connectivity' operation.'''

    rejected: List[dict] = field(default_factory=list)
    '''list of proxies'''
    accepted: List[dict] = field(default_factory=list)
    '''list of proxies'''
    source: List[dict] = field(default_factory=list)
    '''list of proxies'''


@dataclass
class EgressFilterRecorder(FilterRecorder):
    '''Record the 'filter by egress' operation.'''

    rejected: MutableMapping[str, list] = field(
        default_factory=lambda: defaultdict(list)
    )
    accepted: MutableMapping[str, dict] = field(
        default_factory=lambda: defaultdict(dict)
    )
    source: List[dict] = field(default_factory=list)


@dataclass
class FilterRecorderCollection:
    name: ProxyNameFilterRecorder
    ingress: ProxyIngressFilterRecorder
    connectivity: ConnectivityFilterRecorder
    egress: EgressFilterRecorder
