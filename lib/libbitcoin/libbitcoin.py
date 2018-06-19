import os
import asyncio

from lib import constants
from lib.triggers import Triggers
from lib.libbitcoin.protocol import Protocol
from lib.libbitcoin.server import Server

class Libbitcoin(Protocol, Triggers):
    """ Libbitcoin brings everything together.
    """
    def __init__(self, client_settings):
        self._client_settings = client_settings
        self._auto_connect = True
        self._is_connecting = False
        self._servers = Libbitcoin._servers_from(self._client_settings,
            Libbitcoin._servers_from_file())
        self.active_server = None

    def connect(self):
        """ This call doesn't block. """
        self._is_connecting = True
        def no_longer_connecting(future):
            self._is_connecting = False

        future = asyncio.gather(
            *[server.connect() for server in self._servers]
        )
        future.add_done_callback(no_longer_connecting)
        return asyncio.get_event_loop().create_task(future)

    def disconnect(self):
        """ This call blocks. """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(
            *[server.disconnect() for server in self._servers]
        ))

    def _servers_from(client_settings, servers):
        return [Server(connection_details, client_settings)
            for connection_details in servers]

    def _servers_from_file():
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


