import os
import asyncio

from lib import constants 
from lib import simple_config
from .protocol import Protocol
from .server import Server

class Libbitcoin(Protocol):
    """ Libbitcoin brings everything together.
    """
    def __init__(self, config: simple_config.SimpleConfig):
        self.config = config
        self._servers = self._servers_from(self._servers_from_file())

    def disconnect(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(
            *[server.disconnect() for server in self._servers]
        ))

    def _servers_from(self, servers):
        return [Server(server) for server in servers]

    def _servers_from_file(self):
        # TODO read recent servers OR
        # read packaged servers
        return constants.read_json(
            os.path.join("libbitcoin", "servers.json"), [])

    def get_server_height(self):
        pass

    def is_connected(self):
        return False

    def is_connecting(self):
        pass

    def get_parameters(self):
        pass

    def get_donation_address(self):
        pass

    def get_interfaces(self):
        pass

    def get_servers(self):
        return self._servers

    def fast_getaddrinfo(host, *args, **kwargs):
        pass

    def set_parameters(self, host, port, protocol, proxy, auto_connect):
        pass

    def switch_to_interface(self, server):
        pass

    def unsubscribe(self, callback):
        pass

    def fetch_missing_headers_around(self, tx_height):
        pass

    def run(self):
        pass

    def blockchain(self):
        pass

    def get_blockchains(self):
        pass

    def follow_chain(self, index):
        pass

    def get_local_height(self):
        pass


