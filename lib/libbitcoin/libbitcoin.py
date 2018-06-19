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
        return self.active_server.last_height()[1]

    def is_connected(self):
        return next(
            (True for server in self._servers if server.is_connected()),
            False
        )

    def is_connecting(self):
        return self._is_connecting

    # TODO
    def get_donation_address(self):
        pass

    def get_interfaces(self):
        return [server for server in self._servers if server.is_connected()]

    def get_servers(self):
        return self._servers

    # FIXME this method is doing a lot of things and should be split into:
    # get_proxy
    # get_autoconnect
    # get_active_server
    def get_parameters(self):
        return self.active_server.host, \
            self.active_server.port, \
            self.active_server.protocol, \
            self.proxy, \
            self.auto_connect

    # FIXME this method is doing a lof of things and should be split into:
    # set_proxy
    # set_autoconnect
    # set_active_server
    def set_parameters(self, host, port, protocol, proxy, auto_connect):
        """ This method is used to change to the specified server.
        This server might be new or might be known already. If unknown add
        the server. In both cases switch to it.

            'protocol' is ElectrumX specific and is dropped.
            'proxy' is TODO
        """
        self.switch_to_interface(":".join([host, port]))

        self.auto_connect = auto_connect

    # NOTE: the name of the method is legacy in a sense. Libbitcoin doesn't
    # have the concept of 'interface'. `switch_to_server` is a better name.
    def switch_to_interface(self, server):
        """ The 'server' argument is a string <host>:<port>:<protocol>
        """
        host, port = server.split(':')
        server = Server({"hostname": host, "ports": {"public": port}},
            self._client_settings)
        if server in self._servers:
            server = next((existing for existing in self._servers if existing == server))
        else:
            self._servers.append(server)

        self.active_server = server

    def unsubscribe(self, callback):
        pass

    def fetch_missing_headers_around(self, tx_height):
        pass

    def run(self):
        pass

    # FIXME should be called 'get_blockchain' (or 'get_blockchains' should be 'blockchains')
    def blockchain(self):
        pass

    def get_blockchains(self):
        pass

    def follow_chain(self, index):
        pass

    def get_local_height(self):
        pass
