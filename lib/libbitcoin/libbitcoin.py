import os
import asyncio
import zmq.asyncio

import pylibbitcoin.client

from lib import constants
from lib import blockchain
from lib.triggers import Triggers
from lib.util import DaemonThread
from lib.libbitcoin.protocol import Protocol
from lib.libbitcoin.server import Server


class Libbitcoin(DaemonThread, Protocol, Triggers):
    """ Libbitcoin brings everything together.
    """

    def __init__(self, client_settings=None):
        DaemonThread.__init__(self)

        # FIXME passing path like that is an utter hack
        self._blockchains = blockchain.read_blockchains("/tmp/blockchains")

        self._loop = asyncio.new_event_loop()
        self._client_settings = self._client_settings(client_settings)
        self._auto_connect = True
        self._is_connecting = True
        self._servers = Libbitcoin._servers_from(
            self._client_settings,
            Libbitcoin._servers_from_file(),
            self._loop,
        )
        self.active_server = None

    def run(self):
        """ This method is called when the thread starts
        """
        self._loop.run_until_complete(self.connect())
        self._is_connecting = False
        self._loop.run_forever()

    def stop(self):
        """ This method SHOULD be called when stopping the program. Is method
        is overwritten from the DaemonThread super class.
        """
        self._loop.run_until_complete(self.disconnect())
        self._loop.stop()
        self.on_stop()

    def connect(self):
        self._is_connecting = True
        return asyncio.gather(
            *[server.connect() for server in self._servers],
            loop=self._loop,
        )

    def disconnect(self):
        return asyncio.gather(
            *[server.disconnect() for server in self._servers],
            loop=self._loop,
        )

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
            server = next(
                (existing for existing in self._servers if existing == server))
        else:
            self._servers.append(server)

        self.active_server = server

    def unsubscribe(self, callback):
        pass

    def fetch_missing_headers_around(self, tx_height):
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

    # private methods

    # TODO 'self' is really dumb here. I should reconsider the constructor.
    def _client_settings(self, client_settings):
        if client_settings is None:
            return pylibbitcoin.client.ClientSettings(
                timeout=2,
                context=zmq.asyncio.Context(),
                loop=self._loop,
            )

        return client_settings

    def _servers_from(client_settings, servers, loop):
        return [Server(connection_details, client_settings, loop)
                for connection_details in servers]

    def _servers_from_file():
        # TODO read recent servers OR
        # read packaged servers
        return constants.read_json(
            os.path.join("libbitcoin", "servers.json"), [])
