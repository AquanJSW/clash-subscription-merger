import asyncio
import logging
import socket
from ipaddress import ip_address

import aiohttp

import config

logger = logging.getLogger(config.APP_NAME).getChild(__name__)


async def nslookup(host):
    """Lookup host ip address.

    Return
    ---
    A list of IP address, or `['']` if failed.
    """
    loop = asyncio.get_event_loop()
    try:
        resp = await loop.getaddrinfo(host, None, proto=socket.SOCK_RAW)
    except socket.gaierror:
        return ['']
    return [r[4][0] for r in resp]


async def convert_server_to_ip(server: str) -> str:
    """Convert server(hostname or IP) to IP.

    Assuming there is only one IP address for a hostname.

    Return
    ---
    IP address, or an empty string if failed.
    """
    try:
        ip_address(server)
        return server
    except ValueError:
        return (await nslookup(server))[0]


EGRESS_FINDERS = (
    'https://api.ipify.org',
    'https://api.ip.sb/ip',
    'https://icanhazip.com',
)


async def _get_egress_ip(finder: str, http_proxy: str | None = None, timeout=10):
    client_timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=client_timeout) as session:
        async with session.get(finder, proxy=http_proxy, ssl=False) as resp:
            ip = await resp.text()
            ip = ip.strip()
            return ip


async def get_egress_ip(http_proxy: str | None = None):
    """Get egress ip address.

    Return
    ---
    IP address, or an empty string if failed.
    """
    for finder in EGRESS_FINDERS:
        try:
            return await _get_egress_ip(finder, http_proxy)
        except aiohttp.ClientError:
            logger.debug('Error when getting egress ip', exc_info=True)
            continue
    logger.warning("Exhausted all egress finders, failed to get egress ip")
    return ''
